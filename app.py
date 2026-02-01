#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# FX分析AIエージェント（高精度分析モデル）
try:
    from fx_ai_agent import analyze_fx, create_fx_agent
    FX_AI_AGENT_AVAILABLE = True
except ImportError:
    FX_AI_AGENT_AVAILABLE = False
    print("[WARN] fx_ai_agent module not found. FX AI features will be disabled.")

# 外部ネイティブAI呼び出しモジュール（オプション）
try:
    from native_ai import call_native_ai
    NATIVE_AI_AVAILABLE = True
except ImportError:
    NATIVE_AI_AVAILABLE = False
    print("[WARN] native_ai module not found. External native AI features will be disabled.")

load_dotenv()

app = Flask(__name__)

# 環境変数の読み込み（起動時エラーハンドリング）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# LINE Bot API初期化（環境変数が無い場合は後でエラーを返す）
line_bot_api = None
handler = None

if LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET:
    try:
        line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
        handler = WebhookHandler(LINE_CHANNEL_SECRET)
        print("[INFO] LINE Bot API initialized successfully")
    except Exception as e:
        print(f"[WARN] Failed to initialize LINE Bot API: {e}")
else:
    print("[WARN] LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET not set. LINE features will be disabled.")

# 許可されたコマンド（安全のため）
ALLOWED_COMMANDS = {
    "分析": "analyze",
    "予測": "predict",
    "データ更新": "update_data",
    "イベント更新": "update_events",
    "ヘルプ": "help",
}


def run_job(job_name: str, args: list = None, timeout: int = 300) -> tuple[bool, str]:
    """ジョブを実行して結果を返す"""
    jobs_dir = Path(__file__).parent / "jobs"
    job_path = jobs_dir / f"{job_name}.py"
    
    if not job_path.exists():
        return False, f"Job {job_name} not found"
    
    try:
        cmd = ["python3", str(job_path)] + (args or [])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=jobs_dir.parent
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Job timeout ({timeout}s)"
    except Exception as e:
        return False, str(e)


def analyze_usdjpy() -> str:
    """USDJPY分析を実行して結果を返す（FX AIエージェントを使用）"""
    if FX_AI_AGENT_AVAILABLE:
        # FX AIエージェントを使用（高精度分析）
        return analyze_fx("現在の相場状況を分析してください", pair="USDJPY")
    else:
        # フォールバック: 簡易分析
        # プロジェクトルートからの絶対パスを使用
        project_root = Path(__file__).parent
        features_path = project_root / "data/features/USDJPY/M5_features.parquet"
        if not features_path.exists():
            return "特徴量ファイルが見つかりません。まずデータ更新を実行してください。"
        
        import pandas as pd
        try:
            df = pd.read_parquet(features_path)
            latest = df.iloc[-1]
            
            result = f"""USDJPY 最新分析結果

📊 テクニカル指標
RSI(14): {latest.get('rsi_14', 'N/A'):.2f}
ATR(14): {latest.get('atr_14', 'N/A'):.4f}
MA(20): {latest.get('ma_20', 'N/A'):.2f}

📈 イベント状況（24時間）
マクロイベント数: {latest.get('macro_cnt_24H', 0):.0f}
ニュースイベント数: {latest.get('news_cnt_24H', 0):.0f}

💡 推奨アクション
データ更新日時: {df['ts'].max()}
"""
            return result
        except Exception as e:
            return f"分析エラー: {e}"


def update_data() -> str:
    """データ更新を実行（複数データソース対応、簡略化版）"""
    now = datetime.now(timezone.utc)
    end_date = now.strftime("%Y-%m-%d")
    start_date = (now - timedelta(days=3)).strftime("%Y-%m-%d")  # 3日分に短縮（処理時間短縮）
    
    results = []
    results.append("🔄 データ更新を開始しました...")
    
    # 方法1: Yahoo Financeからデータを取得（最も確実で簡単）
    print("[INFO] Yahoo Financeからデータを取得中...")
    results.append("📥 Yahoo Financeからデータを取得中...")
    success_yahoo, msg_yahoo = run_job("download_yahoo_finance", [
        "--pair", "USDJPY",
        "--start-date", start_date,
        "--end-date", end_date,
        "--interval", "1h"
    ], timeout=180)  # タイムアウトを3分に短縮
    
    if success_yahoo:
        results.append("✅ Yahoo Financeデータ取得完了")
        
        # Yahoo Financeデータをbuild_features.pyが読み込める形式に変換
        # data/yahoo_finance/USDJPY/1h.parquet → data/bars/USDJPY/tf=H1/all.parquet
        try:
            import pandas as pd
            from pathlib import Path
            
            yahoo_path = Path("data/yahoo_finance/USDJPY/1h.parquet")
            bars_dir = Path("data/bars/USDJPY/tf=H1")
            
            if yahoo_path.exists():
                bars_dir.mkdir(parents=True, exist_ok=True)
                df = pd.read_parquet(yahoo_path)
                
                # タイムスタンプをUTCに統一
                if "ts" in df.columns:
                    df["ts"] = pd.to_datetime(df["ts"], utc=True)
                elif df.index.name == "ts" or isinstance(df.index, pd.DatetimeIndex):
                    df = df.reset_index()
                    if "ts" not in df.columns and len(df.columns) > 0:
                        # 最初の列がタイムスタンプの可能性
                        df.columns = ["ts"] + list(df.columns[1:])
                
                # 必要なカラムがあるか確認
                required_cols = ["open", "high", "low", "close"]
                if all(col in df.columns for col in required_cols):
                    bars_path = bars_dir / "all.parquet"
                    df.to_parquet(bars_path, index=False)
                    results.append("✅ H1バーデータを準備完了")
                else:
                    results.append("⚠️ Yahoo Financeデータに必要なカラムがありません")
        except Exception as e:
            results.append(f"⚠️ バーデータ変換エラー: {str(e)[:100]}")
    else:
        results.append(f"⚠️ Yahoo Finance取得エラー: {msg_yahoo}")
    
    # 方法2: DukascopyからBI5をダウンロード（スキップ - 時間がかかりすぎる）
    # Render環境ではYahoo Financeのみを使用
    results.append("⏭️ Dukascopyはスキップ（Yahoo Financeデータを使用）")
    
    if success_bi5:
        results.append("✅ Dukascopy BI5ダウンロード完了")
        
        # M1生成
        start_date_m1 = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date_m1 = now.strftime("%Y-%m-%d")
        success_m1, msg_m1 = run_job("build_m1_from_bi5", [
            "--pair", "USDJPY",
            "--start-date", start_date_m1,
            "--end-date", end_date_m1
        ], timeout=300)
        
        if success_m1:
            results.append("✅ M1バー生成完了")
            
            # 全時間足生成
            success_bars, msg_bars = run_job("build_bars_from_m1", [
                "--pair", "USDJPY"
            ], timeout=300)
            
            if success_bars:
                results.append("✅ 時間足バー生成完了")
            else:
                results.append(f"⚠️ 時間足生成エラー: {msg_bars}")
        else:
            results.append(f"⚠️ M1生成エラー: {msg_m1}")
    else:
        results.append(f"⚠️ Dukascopy取得エラー: {msg_bi5}（スキップ）")
    
    # イベントデータ取得（簡略化 - スキップして高速化）
    # results.append("⏭️ イベントデータはスキップ（高速化のため）")
    
    # 特徴量生成（データが存在する場合）
    # Yahoo FinanceからはH1データを取得しているため、H1特徴量を生成
    print("[INFO] 特徴量を生成中...")
    results.append("🔧 特徴量を生成中...")
    success_features, msg_features = run_job("build_features", [
        "--pair", "USDJPY",
        "--timeframe", "H1"  # Yahoo Financeは1hデータなので、H1特徴量を生成
    ], timeout=180)  # タイムアウトを3分に短縮
    
    if success_features:
        results.append("✅ 特徴量生成完了")
        return "\n".join(results) + "\n\n✅ データ更新完了！「分析」コマンドを試してください。"
    else:
        # エラーメッセージを短縮
        error_msg = str(msg_features)[:200] if msg_features else "不明なエラー"
        results.append(f"⚠️ 特徴量生成エラー: {error_msg}")
        return "\n".join(results) + "\n\n⚠️ 一部の処理が失敗しました。数分待ってから再度「データ更新」を試してください。"


def update_events() -> str:
    """イベント更新を実行"""
    events_cache = "data/events/events_cache.parquet"
    
    # マクロイベント
    success1, msg1 = run_job("fetch_macro_events", [
        "--events-cache", events_cache
    ])
    
    # RSSイベント
    success2, msg2 = run_job("fetch_rss_events", [
        "--events-cache", events_cache
    ])
    
    if success1 and success2:
        return "✅ イベント更新完了"
    else:
        return f"⚠️ 一部エラー: {msg1 or msg2}"


def train_fx_model() -> str:
    """FXモデル学習を実行（自動判定付き）"""
    # 自動学習スクリプトを使用（再学習判定あり）
    # モデル学習は時間がかかる可能性があるため、タイムアウトを延長
    success, msg = run_job("auto_train_model", [
        "--pair", "USDJPY",
        "--features-tf", "M5",
        "--force"  # LINE Botから実行時は強制学習
    ], timeout=1800)  # 30分タイムアウト
    
    if success:
        return f"✅ モデル学習完了\n\n{msg}\n\nモデル保存先: models/fx_usdjpy_model.pkl"
    else:
        # タイムアウトの場合は別メッセージ
        if "timeout" in msg.lower():
            return "⚠️ モデル学習がタイムアウトしました（30分）。データ量が多い場合は時間がかかります。\n\nバックグラウンドで実行するか、データ量を減らして再試行してください。"
        return f"⚠️ モデル学習エラー: {msg}"


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook"""
    if not handler:
        print("[ERROR] LINE handler not initialized. Check LINE_CHANNEL_SECRET.")
        abort(503)
    
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[ERROR] Invalid LINE signature")
        abort(400)
    except Exception as e:
        print(f"[ERROR] LINE webhook error: {e}")
        abort(500)
    
    return "OK"


def handle_message(event):
    """メッセージハンドラー"""
    if not line_bot_api:
        print("[ERROR] LINE Bot API not initialized. Cannot handle message.")
        return
    
    try:
        text = event.message.text.strip()
        
        # コマンド判定
        cmd = None
        for key, value in ALLOWED_COMMANDS.items():
            if key in text:
                cmd = value
                break
        
        if cmd == "help":
            help_text = """📋 利用可能なコマンド

• 分析 - USDJPYの最新分析結果を表示
• 予測 - AIによる高精度予測を表示
• データ更新 - Dukascopyから最新データを取得
• イベント更新 - 経済指標・要人発言を更新
• モデル学習 - 高精度分析モデルを学習・更新

例: 「分析」「データ更新して」「モデル学習」

💡 その他のメッセージはFX分析AIエージェントが回答します"""
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
            return
        
        if cmd == "analyze":
            result = analyze_usdjpy()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
            return
        
        if cmd == "predict":
            # 高精度予測機能（AIエージェント使用）
            if FX_AI_AGENT_AVAILABLE:
                result = analyze_fx(text, pair="USDJPY")
            else:
                result = analyze_usdjpy() + "\n\n💹 予測: 分析結果を確認してください"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
            return
        
        if cmd == "update_data":
            # 即座に応答を返す（処理が長時間かかる可能性があるため）
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="🔄 データ更新を開始しました。処理中です...\n\n（数分かかる場合があります）")
            )
            # バックグラウンドで処理を実行（LINE Botのタイムアウトを回避）
            try:
                result = update_data()
                # 処理完了後にユーザーに通知（オプション - 実装が複雑なため、今回はスキップ）
                # ユーザーは「分析」コマンドで結果を確認できる
            except Exception as e:
                print(f"[ERROR] Data update failed: {e}")
            return
        
        if cmd == "update_events":
            result = update_events()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
            return
        
        if cmd == "train_model" or cmd == "モデル学習":
            # モデル学習を実行（バックグラウンド推奨）
            result = train_fx_model()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
            return
        
        # コマンドが一致しない場合: FX分析AIエージェントまたは外部ネイティブAIに投げる
        # 優先順位: 1) FX分析AIエージェント（このプロジェクト内） 2) 外部ネイティブAI
        
        # FX関連の質問かどうかを簡易判定（大文字小文字を区別しない）
        fx_keywords = ["ドル円", "USDJPY", "usdjpy", "USD/JPY", "usd/jpy", "為替", "FX", "fx", 
                      "相場", "価格", "予測", "分析", "買い", "売り", "上昇", "下落", 
                      "トレンド", "チャート", "円", "ドル", "jpy", "usd"]
        text_lower = text.lower()
        is_fx_question = any(kw.lower() in text_lower for kw in fx_keywords)
        
        # 1. FX分析AIエージェント（推奨・高精度分析）
        if FX_AI_AGENT_AVAILABLE and is_fx_question:
            try:
                # FX分析AIエージェントで回答
                ai_reply = analyze_fx(text, pair="USDJPY")
                # データが見つからないなどの警告でも、そのまま返す（外部AIにフォールバックしない）
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
                return
            except Exception as e:
                print(f"[ERROR] FX AI Agent failed: {e}")
                # FX質問の場合は、エラーでも外部AIにフォールバックせず、エラーメッセージを返す
                error_msg = f"⚠️ FX分析中にエラーが発生しました: {str(e)[:200]}"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_msg))
                return
        
        # 2. 外部ネイティブAI（FX質問でない場合、またはFX分析AIが利用不可の場合）
        # NATIVE_AI_URLが設定されている場合、かつプレースホルダーでない場合のみ呼び出す
        native_ai_url = os.getenv("NATIVE_AI_URL", "").strip()
        is_placeholder_url = (
            not native_ai_url or 
            "example.com" in native_ai_url.lower() or 
            "your-ai" in native_ai_url.lower() or
            "placeholder" in native_ai_url.lower()
        )
        
        if NATIVE_AI_AVAILABLE and native_ai_url and not is_placeholder_url:
            try:
                # FX分析データをcontextに含める（あれば）
                context = None
                try:
                    features_path = Path("data/features/USDJPY/M5_features.parquet")
                    if features_path.exists():
                        import pandas as pd
                        df = pd.read_parquet(features_path)
                        latest = df.iloc[-1] if not df.empty else None
                        if latest is not None:
                            context = f"FX分析コンテキスト: RSI={latest.get('rsi_14', 'N/A'):.2f}, ATR={latest.get('atr_14', 'N/A'):.4f}, 価格={latest.get('close', 'N/A'):.2f}"
                except Exception:
                    pass  # FXデータ取得失敗は無視
                
                # 外部ネイティブAIを呼び出す
                ai_reply = call_native_ai(text, context=context)
                # プレースホルダー警告が返ってきた場合は、そのまま返す
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
                return
            except Exception as e:
                print(f"[ERROR] External Native AI call failed: {e}")
                error_msg = f"⚠️ 外部AI呼び出し中にエラーが発生しました: {str(e)[:200]}"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_msg))
                return
        
        # 3. FX質問だがFX分析AIが利用不可の場合
        if is_fx_question and not FX_AI_AGENT_AVAILABLE:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ FX分析AIエージェントが利用できません。データ更新を実行するか、管理者にご連絡ください。")
            )
            return
        
        # 4. デフォルト（AI未設定の場合）
        if FX_AI_AGENT_AVAILABLE:
            # FX分析AIエージェントで一般的な分析を返す
            try:
                result = analyze_fx("現在の相場状況を教えて", pair="USDJPY")
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
                return
            except Exception:
                pass
        
        # 最終フォールバック
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="コマンドが認識できませんでした。「ヘルプ」と送ってください。")
        )
    except Exception as e:
        print(f"[ERROR] Error handling LINE message: {e}")
        if line_bot_api:
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="エラーが発生しました。しばらくしてから再度お試しください。")
                )
            except Exception as reply_error:
                print(f"[ERROR] Failed to send error reply: {reply_error}")


@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェック - 200を返す"""
    from flask import jsonify
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


# LINE handler登録（初期化済みの場合のみ）
if handler and line_bot_api:
    try:
        handler.add(MessageEvent, message=TextMessage)(handle_message)
        print("[INFO] LINE message handler registered successfully")
    except Exception as e:
        print(f"[ERROR] Failed to register LINE handler: {e}")
else:
    print("[WARN] LINE handler not registered. Set LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET to enable LINE features.")


@app.route("/", methods=["GET"])
def index():
    """ルートエンドポイント"""
    return {
        "service": "FX Analysis Agent with LINE Bot",
        "status": "running",
        "endpoints": {
            "/health": "Health check",
            "/callback": "LINE Webhook (POST)",
            "/": "This page"
        },
        "line_enabled": line_bot_api is not None,
        "fx_ai_agent_enabled": FX_AI_AGENT_AVAILABLE,
        "native_ai_enabled": NATIVE_AI_AVAILABLE and bool(os.getenv("NATIVE_AI_URL"))
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[INFO] Starting server on port {port}")
    print(f"[INFO] Health check: http://localhost:{port}/health")
    app.run(host="0.0.0.0", port=port, debug=False)

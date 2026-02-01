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
    """USDJPY分析を実行して結果を返す"""
    # 最新の特徴量ファイルを確認
    features_path = Path("data/features/USDJPY/M5_features.parquet")
    if not features_path.exists():
        return "特徴量ファイルが見つかりません。まずデータ更新を実行してください。"
    
    # 簡易分析（実際はモデル推論をここに入れる）
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
    """データ更新を実行"""
    now = datetime.now(timezone.utc)
    end = now.strftime("%Y-%m-%dT%H")
    start = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H")
    
    # 1. bi5ダウンロード
    success, msg = run_job("download_bi5", [
        "--pair", "USDJPY",
        "--start", start,
        "--end", end
    ])
    if not success:
        return f"データ取得エラー: {msg}"
    
    # 2. M1生成
    start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")
    success, msg = run_job("build_m1_from_bi5", [
        "--pair", "USDJPY",
        "--start-date", start_date,
        "--end-date", end_date
    ])
    if not success:
        return f"M1生成エラー: {msg}"
    
    # 3. 全時間足生成
    success, msg = run_job("build_bars_from_m1", [
        "--pair", "USDJPY"
    ])
    if not success:
        return f"時間足生成エラー: {msg}"
    
    return "✅ データ更新完了"


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
            result = update_data()
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
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
        
        # 1. FX分析AIエージェント（推奨・高精度分析）
        if FX_AI_AGENT_AVAILABLE:
            try:
                # FX関連の質問かどうかを簡易判定
                fx_keywords = ["ドル円", "USDJPY", "USD/JPY", "為替", "FX", "相場", "価格", "予測", "分析", 
                              "買い", "売り", "上昇", "下落", "トレンド", "チャート"]
                is_fx_question = any(kw in text for kw in fx_keywords)
                
                if is_fx_question:
                    # FX分析AIエージェントで回答
                    ai_reply = analyze_fx(text, pair="USDJPY")
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
                    return
            except Exception as e:
                print(f"[ERROR] FX AI Agent failed: {e}")
                # フォールバック処理に続く
        
        # 2. 外部ネイティブAI（NATIVE_AI_URLが設定されている場合）
        if NATIVE_AI_AVAILABLE and os.getenv("NATIVE_AI_URL"):
            try:
                # FX分析データをcontextに含める
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
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
                return
            except Exception as e:
                print(f"[ERROR] External Native AI call failed: {e}")
                # フォールバック処理に続く
        
        # 3. デフォルト（AI未設定の場合）
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

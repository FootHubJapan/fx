#!/bin/bash
# FXデータパイプライン実行スクリプト

set -e  # エラーが発生したら停止

PAIR=USDJPY

# 過去何日分のデータを取得するか（デフォルト: 7日）
DAYS_BACK=${1:-7}

# 日付計算
END_DATE=$(date -u +"%Y-%m-%d")
START_DATE=$(date -u -v-${DAYS_BACK}d +"%Y-%m-%d" 2>/dev/null || date -u -d "${DAYS_BACK} days ago" +"%Y-%m-%d")
START_DATETIME="${START_DATE}T00"
END_DATETIME="${END_DATE}T00"

echo "=========================================="
echo "FXデータパイプライン実行"
echo "通貨ペア: ${PAIR}"
echo "期間: ${START_DATE} ～ ${END_DATE} (${DAYS_BACK}日間)"
echo "=========================================="
echo ""

# 1. BI5ダウンロード
echo "[1/5] BI5ファイルをダウンロード中..."
python3 jobs/download_bi5.py \
  --pair ${PAIR} \
  --start ${START_DATETIME} \
  --end ${END_DATETIME}
if [ $? -ne 0 ]; then
  echo "❌ BI5ダウンロードに失敗しました"
  exit 1
fi
echo "✅ BI5ダウンロード完了"
echo ""

# 2. M1バー生成
echo "[2/5] M1バーを生成中..."
python3 jobs/build_m1_from_bi5.py \
  --pair ${PAIR} \
  --start-date ${START_DATE} \
  --end-date ${END_DATE}
if [ $? -ne 0 ]; then
  echo "❌ M1バー生成に失敗しました"
  exit 1
fi
echo "✅ M1バー生成完了"
echo ""

# 3. 全時間足バー生成
echo "[3/5] 全時間足バーを生成中..."
python3 jobs/build_bars_from_m1.py --pair ${PAIR}
if [ $? -ne 0 ]; then
  echo "❌ 時間足バー生成に失敗しました"
  exit 1
fi
echo "✅ 時間足バー生成完了"
echo ""

# 4. イベントデータ取得（オプション、エラーでも続行）
echo "[4/5] イベントデータを取得中..."
python3 jobs/fetch_macro_events.py || echo "⚠️ マクロイベント取得をスキップ"
python3 jobs/fetch_rss_events.py || echo "⚠️ RSSイベント取得をスキップ"
echo "✅ イベントデータ取得完了"
echo ""

# 5. 特徴量生成
echo "[5/5] 特徴量を生成中..."
python3 jobs/build_features.py \
  --pair ${PAIR} \
  --timeframe M5
if [ $? -ne 0 ]; then
  echo "❌ 特徴量生成に失敗しました"
  exit 1
fi
echo "✅ 特徴量生成完了"
echo ""

echo "=========================================="
echo "✅ データパイプライン実行完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. LINE Botで「分析」または「予測」コマンドを試す"
echo "2. または、python3 -c \"from fx_ai_agent import analyze_fx; print(analyze_fx('現在の相場状況を教えて'))\" を実行"

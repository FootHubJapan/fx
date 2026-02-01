#!/bin/bash
# ダウンロード完了を待って、自動的に次のステップに進むスクリプト

PAIR=USDJPY
START_DATE=2026-01-25
END_DATE=2026-02-01
TARGET_COUNT=168  # 7日間 × 24時間

echo "=========================================="
echo "ダウンロード完了待機中..."
echo "通貨ペア: ${PAIR}"
echo "期間: ${START_DATE} ～ ${END_DATE}"
echo "目標: ${TARGET_COUNT}個のBI5ファイル"
echo "=========================================="
echo ""

# 進行状況を表示する関数
show_progress() {
    current=$(find data/raw_bi5/${PAIR} -name "*.bi5" 2>/dev/null | wc -l | tr -d ' ')
    progress=$(echo "scale=1; ${current} * 100 / ${TARGET_COUNT}" | bc)
    echo "[$(date +%H:%M:%S)] ダウンロード済み: ${current}/${TARGET_COUNT}個 (${progress}%)"
}

# ダウンロード完了まで待機
while true; do
    current=$(find data/raw_bi5/${PAIR} -name "*.bi5" 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$current" -ge "$TARGET_COUNT" ]; then
        echo ""
        echo "✅ ダウンロード完了！"
        show_progress
        break
    fi
    
    show_progress
    sleep 10  # 10秒ごとに確認
done

echo ""
echo "=========================================="
echo "次のステップ: M1バー生成"
echo "=========================================="
echo ""

# M1バー生成
echo "[1/4] M1バーを生成中..."
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

# 全時間足バー生成
echo "[2/4] 全時間足バーを生成中..."
python3 jobs/build_bars_from_m1.py --pair ${PAIR}
if [ $? -ne 0 ]; then
  echo "❌ 時間足バー生成に失敗しました"
  exit 1
fi
echo "✅ 時間足バー生成完了"
echo ""

# イベントデータ取得（オプション）
echo "[3/4] イベントデータを取得中..."
python3 jobs/fetch_macro_events.py || echo "⚠️ マクロイベント取得をスキップ"
python3 jobs/fetch_rss_events.py || echo "⚠️ RSSイベント取得をスキップ"
echo "✅ イベントデータ取得完了"
echo ""

# 特徴量生成
echo "[4/4] 特徴量を生成中..."
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
echo "✅ データパイプライン完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. LINE Botで「分析」または「予測」コマンドを試す"
echo "2. または、python3 -c \"from fx_ai_agent import analyze_fx; print(analyze_fx('現在の相場状況を教えて'))\" を実行"

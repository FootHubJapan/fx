#!/bin/bash
# マルチデータソース統合パイプライン

set -e

PAIR=USDJPY
DAYS_BACK=${1:-7}

# 日付計算
END_DATE=$(date -u +"%Y-%m-%d")
START_DATE=$(date -u -v-${DAYS_BACK}d +"%Y-%m-%d" 2>/dev/null || date -u -d "${DAYS_BACK} days ago" +"%Y-%m-%d")
START_DATETIME="${START_DATE}T00"
END_DATETIME="${END_DATE}T00"

echo "=========================================="
echo "マルチデータソース統合パイプライン"
echo "通貨ペア: ${PAIR}"
echo "期間: ${START_DATE} ～ ${END_DATE} (${DAYS_BACK}日間)"
echo "=========================================="
echo ""

# 1. Dukascopy（既存・推奨）
echo "[1/6] DukascopyからBI5ファイルをダウンロード中..."
python3 jobs/download_bi5.py \
  --pair ${PAIR} \
  --start ${START_DATETIME} \
  --end ${END_DATETIME} || echo "⚠️ Dukascopyダウンロードをスキップ"
echo ""

echo "[2/6] DukascopyからM1バーを生成中..."
python3 jobs/build_m1_from_bi5.py \
  --pair ${PAIR} \
  --start-date ${START_DATE} \
  --end-date ${END_DATE} || echo "⚠️ M1バー生成をスキップ"
echo ""

# 2. Yahoo Finance（新規・無料）
echo "[3/6] Yahoo Financeからデータを取得中..."
python3 jobs/download_yahoo_finance.py \
  --pair ${PAIR} \
  --start-date ${START_DATE} \
  --end-date ${END_DATE} \
  --interval 1h || echo "⚠️ Yahoo Finance取得をスキップ"
echo ""

# 3. OANDA（新規・オプション）
if [ -n "$OANDA_API_KEY" ]; then
  echo "[4/6] OANDAからデータを取得中..."
  python3 jobs/download_oanda.py \
    --pair ${PAIR} \
    --start "${START_DATE}T00:00:00" \
    --end "${END_DATE}T00:00:00" \
    --granularity H1 || echo "⚠️ OANDA取得をスキップ"
else
  echo "[4/6] OANDAをスキップ（OANDA_API_KEY未設定）"
fi
echo ""

# 4. データマージ
echo "[5/6] データソースをマージ中..."
python3 jobs/merge_data_sources.py \
  --pair ${PAIR} \
  --start-date ${START_DATE} \
  --end-date ${END_DATE} \
  --priority dukascopy,yahoo,oanda || echo "⚠️ データマージをスキップ"
echo ""

# 5. 特徴量生成（既存のM1バーまたはマージデータを使用）
echo "[6/6] 特徴量を生成中..."
python3 jobs/build_features.py \
  --pair ${PAIR} \
  --timeframe M5 || echo "⚠️ 特徴量生成をスキップ"
echo ""

echo "=========================================="
echo "✅ マルチデータソース統合パイプライン完了！"
echo "=========================================="
echo ""
echo "データソースの状況:"
echo "- Dukascopy: data/bars/${PAIR}/"
echo "- Yahoo Finance: data/yahoo_finance/${PAIR}/"
echo "- OANDA: data/oanda/${PAIR}/"
echo "- マージデータ: data/merged/${PAIR}/"
echo ""
echo "次のステップ:"
echo "1. LINE Botで「分析」または「予測」コマンドを試す"
echo "2. データ品質を確認: ./CHECK_PIPELINE_STATUS.sh"

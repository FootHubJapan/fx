#!/bin/bash
# データパイプラインの進行状況を確認するスクリプト

echo "=========================================="
echo "データパイプライン進行状況確認"
echo "=========================================="
echo ""

# 1. BI5ファイル数
bi5_count=$(find data/raw_bi5/USDJPY -name "*.bi5" 2>/dev/null | wc -l | tr -d ' ')
echo "[1] BI5ファイル: ${bi5_count}個"
if [ "$bi5_count" -gt 0 ]; then
  echo "    ✅ ダウンロード済み"
  find data/raw_bi5/USDJPY -name "*.bi5" 2>/dev/null | head -3 | sed 's/^/    - /'
  if [ "$bi5_count" -gt 3 ]; then
    echo "    ... 他 ${bi5_count}個"
  fi
else
  echo "    ⏳ ダウンロード中または未開始"
fi
echo ""

# 2. M1バーファイル数
m1_count=$(find data/bars/USDJPY/tf=M1 -name "*.parquet" 2>/dev/null | wc -l | tr -d ' ')
echo "[2] M1バーファイル: ${m1_count}個"
if [ "$m1_count" -gt 0 ]; then
  echo "    ✅ 生成済み"
else
  echo "    ⏳ 未生成（BI5ダウンロード完了後に生成されます）"
fi
echo ""

# 3. 時間足バーファイル数
bars_count=$(find data/bars/USDJPY -name "*.parquet" 2>/dev/null | grep -v "tf=M1" | wc -l | tr -d ' ')
echo "[3] 時間足バー（M5, H1など）: ${bars_count}個"
if [ "$bars_count" -gt 0 ]; then
  echo "    ✅ 生成済み"
else
  echo "    ⏳ 未生成（M1バー生成後に生成されます）"
fi
echo ""

# 4. 特徴量ファイル
features_file="data/features/USDJPY/M5_features.parquet"
if [ -f "$features_file" ]; then
  file_size=$(ls -lh "$features_file" | awk '{print $5}')
  echo "[4] 特徴量ファイル: ✅ 存在（サイズ: ${file_size}）"
else
  echo "[4] 特徴量ファイル: ⏳ 未生成"
fi
echo ""

echo "=========================================="
echo "次のステップ"
echo "=========================================="

if [ "$bi5_count" -eq 0 ]; then
  echo "→ BI5ダウンロードを待っています..."
elif [ "$m1_count" -eq 0 ]; then
  echo "→ M1バー生成を実行してください:"
  echo "  python3 jobs/build_m1_from_bi5.py --pair USDJPY --start-date 2026-01-25 --end-date 2026-02-01"
elif [ "$bars_count" -eq 0 ]; then
  echo "→ 時間足バー生成を実行してください:"
  echo "  python3 jobs/build_bars_from_m1.py --pair USDJPY"
elif [ ! -f "$features_file" ]; then
  echo "→ 特徴量生成を実行してください:"
  echo "  python3 jobs/build_features.py --pair USDJPY --timeframe M5"
else
  echo "✅ すべてのデータが準備できています！"
  echo "→ LINE Botで「分析」または「予測」を試してください"
fi

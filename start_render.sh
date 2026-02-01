#!/bin/bash
# Render起動スクリプト
# データが無い場合、自動的にデータパイプラインを実行

set -e

echo "=========================================="
echo "Render起動スクリプト"
echo "=========================================="

# データディレクトリを作成
mkdir -p data/{raw_bi5,bars,features,events,logs,merged,yahoo_finance,oanda}
mkdir -p models

# 特徴量ファイルが存在するか確認
if [ ! -f "data/features/USDJPY/M5_features.parquet" ]; then
    echo "[INFO] 特徴量ファイルが見つかりません。データパイプラインを実行します..."
    
    # 最新7日分のデータを取得
    END_DATE=$(date -u +%Y-%m-%d)
    START_DATE=$(date -u -v-7d +%Y-%m-%d 2>/dev/null || date -u -d "7 days ago" +%Y-%m-%d)
    
    echo "[INFO] 期間: $START_DATE ～ $END_DATE"
    
    # Yahoo Financeからデータを取得（最も簡単で確実）
    echo "[1/3] Yahoo Financeからデータを取得中..."
    python3 jobs/download_yahoo_finance.py \
        --pair USDJPY \
        --start-date "$START_DATE" \
        --end-date "$END_DATE" \
        --interval 1h || echo "[WARN] Yahoo Finance取得をスキップ"
    
    # M5バーを生成（Yahoo Financeデータから直接）
    # 注意: Yahoo Financeは1hデータなので、M5バーを生成するには別の方法が必要
    # ここでは簡易的に、Yahoo Financeデータをそのまま使用
    
    # 特徴量を生成（データが存在する場合）
    if [ -f "data/yahoo_finance/USDJPY/1h.parquet" ]; then
        echo "[2/3] 特徴量を生成中..."
        # Yahoo Financeデータから特徴量を生成する場合は、build_features.pyを修正する必要があります
        # ここでは簡易的にスキップ
        echo "[INFO] 特徴量生成をスキップ（Yahoo Financeデータから直接生成する場合は実装が必要）"
    fi
    
    echo "[WARN] データパイプラインが完了しましたが、特徴量ファイルが生成されていない可能性があります。"
    echo "[WARN] LINE Botで「データ更新」コマンドを実行してください。"
else
    echo "[INFO] 特徴量ファイルが見つかりました。"
fi

echo ""
echo "アプリケーションを起動中..."
echo ""

# アプリを起動
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

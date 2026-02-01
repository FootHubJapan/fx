#!/bin/bash
# 仮想環境を再構築するスクリプト

set -e

echo "=========================================="
echo "仮想環境を再構築中..."
echo "=========================================="
echo ""

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
echo "プロジェクトディレクトリ: ${PROJECT_DIR}"

# 既存の仮想環境を無効化（あれば）
if [ -n "$VIRTUAL_ENV" ]; then
    echo "既存の仮想環境を無効化: ${VIRTUAL_ENV}"
    deactivate 2>/dev/null || true
fi

# 既存の仮想環境を削除
if [ -d "venv" ]; then
    echo "既存の仮想環境を削除中..."
    rm -rf venv
fi

# 新しい仮想環境を作成
echo "新しい仮想環境を作成中..."
python3 -m venv venv

# 仮想環境を有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# pipをアップグレード
echo "pipをアップグレード中..."
pip install --upgrade pip

# 依存関係をインストール
echo "依存関係をインストール中..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ 仮想環境の再構築が完了しました！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. 仮想環境が有効化されています"
echo "2. データパイプラインを実行: ./run_data_pipeline.sh 7"
echo "3. または、Yahoo Financeからデータ取得: python3 jobs/download_yahoo_finance.py --pair USDJPY --start-date 2026-01-25 --end-date 2026-02-01 --interval 1h"

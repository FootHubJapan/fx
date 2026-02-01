#!/bin/bash
# アプリケーションを再起動するスクリプト

cd "$(dirname "$0")"

echo "=========================================="
echo "アプリケーション再起動"
echo "=========================================="
echo ""

# ポート5002を使用しているプロセスを確認
PID=$(lsof -ti :5002)
if [ -n "$PID" ]; then
    echo "ポート5002を使用しているプロセスを停止中 (PID: $PID)..."
    kill -9 $PID 2>/dev/null || {
        echo "⚠️ プロセスを停止できませんでした。手動で停止してください:"
        echo "   kill -9 $PID"
        echo ""
        echo "または、別のポートを使用してください（.envでPORT=5003に変更）"
        exit 1
    }
    sleep 2
    echo "✅ プロセスを停止しました"
else
    echo "✅ ポート5002は使用されていません"
fi

# 仮想環境を有効化
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 仮想環境を有効化しました"
else
    echo "❌ 仮想環境が見つかりません。先に仮想環境を作成してください。"
    exit 1
fi

# 特徴量ファイルの存在確認
if [ -f "data/features/USDJPY/M5_features.parquet" ]; then
    echo "✅ 特徴量ファイルが見つかりました"
else
    echo "⚠️ 特徴量ファイルが見つかりません。先に特徴量を生成してください:"
    echo "   python3 jobs/build_features.py --pair USDJPY --timeframe M5"
fi

echo ""
echo "アプリケーションを起動中..."
echo ""

# アプリを起動
python3 app.py

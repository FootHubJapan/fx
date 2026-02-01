#!/bin/bash
# 依存関係インストールスクリプト

echo "仮想環境をアクティベート中..."
source venv/bin/activate

echo "pipをアップグレード中..."
pip install --upgrade pip

echo "依存関係をインストール中..."
echo "（ネットワーク接続が必要です）"

# 個別にインストール（エラーが出た場合にどのパッケージで失敗したか分かる）
pip install pandas==2.1.4 && echo "✓ pandas installed"
pip install numpy==1.26.2 && echo "✓ numpy installed"
pip install flask==3.0.0 && echo "✓ flask installed"
pip install line-bot-sdk==3.5.0 && echo "✓ line-bot-sdk installed"
pip install pyarrow==14.0.2 && echo "✓ pyarrow installed"
pip install requests==2.31.0 && echo "✓ requests installed"
pip install feedparser==6.0.10 && echo "✓ feedparser installed"
pip install python-dotenv==1.0.0 && echo "✓ python-dotenv installed"
pip install gunicorn==21.2.0 && echo "✓ gunicorn installed"
pip install lightgbm==4.5.0 && echo "✓ lightgbm installed"
pip install scikit-learn==1.4.2 && echo "✓ scikit-learn installed"

echo ""
echo "インストール確認中..."
python3 -c "import pandas; import lightgbm; import flask; print('✓ すべてのパッケージがインストールされました')" && echo "成功！" || echo "エラー: 一部のパッケージがインストールされていません"

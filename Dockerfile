FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# データディレクトリ作成
RUN mkdir -p data/{raw_bi5,bars,features,events,logs}

# ポート公開（Renderが自動設定する$PORTを使用）
# EXPOSEは動的ポートのためコメントアウト

# 起動コマンド（$PORT環境変数を使用）
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120

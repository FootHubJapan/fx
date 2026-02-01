# デプロイ手順

## Renderへのデプロイ

### 1. GitHubリポジトリの準備

```bash
# リポジトリを初期化（まだの場合）
git init
git add .
git commit -m "Initial commit: FX Analysis Agent with LINE Bot"

# GitHubにpush
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2. RenderでWeb Serviceを作成

1. Renderダッシュボードにログイン
2. **New +** → **Web Service** を選択
3. GitHubリポジトリを選択
4. 以下の設定を入力：

   - **Name**: `fx-analysis-line-bot`
   - **Region**: 最寄りのリージョン
   - **Branch**: `main`
   - **Root Directory**: （空欄のまま）
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 3. 環境変数の設定

Renderの **Environment** タブで以下を設定：

```
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here
TE_API_KEY=guest:guest
```

### 4. LINE Developers設定

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. プロバイダーとチャネルを作成
3. **Webhook URL** に RenderのURLを設定：
   ```
   https://your-app.onrender.com/callback
   ```
4. **Webhook** を有効化
5. **Channel Access Token** と **Channel Secret** をコピーしてRenderの環境変数に設定

### 5. デプロイ

Renderで **Manual Deploy** を実行、または自動デプロイを待つ。

### 6. 動作確認

LINEアプリでボットに「ヘルプ」と送信して、応答があるか確認。

## ローカル開発環境

### セットアップ

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envを編集してLINEトークンを設定
```

### ローカル実行

```bash
# LINEボット起動
python app.py

# 別ターミナルでデータ更新テスト
python jobs/download_bi5.py --pair USDJPY --start 2025-01-01T00 --end 2025-01-02T00
python jobs/build_m1_from_bi5.py --pair USDJPY --start-date 2025-01-01 --end-date 2025-01-02
```

### ngrokでローカルテスト

```bash
# ngrokインストール（未インストールの場合）
brew install ngrok  # Mac
# または https://ngrok.com/download

# ngrok起動
ngrok http 5000

# LINE DevelopersでWebhook URLをngrokのURLに設定
# https://xxxx.ngrok.io/callback
```

## トラブルシューティング

### Renderでビルドエラー

- `requirements.txt` の依存関係を確認
- Pythonバージョンを3.11に固定（`runtime.txt`を作成）

### LINE Webhookエラー

- Webhook URLが正しいか確認
- Channel Secretが正しく設定されているか確認
- Renderのログを確認（`/health`エンドポイントで動作確認）

### データ取得エラー

- DukascopyのURLが正しいか確認
- ネットワーク接続を確認
- 日付範囲が正しいか確認

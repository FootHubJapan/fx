# クイックスタートガイド

## 5分で動かす

### 1. リポジトリをクローン/ダウンロード

```bash
git clone <your-repo-url>
cd fx-agent
```

### 2. 依存関係インストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数設定（最小限）

`.env`ファイルを作成：

```bash
# LINE Botを使わない場合でも起動可能（機能制限あり）
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
TE_API_KEY=guest:guest
```

### 4. 起動

```bash
python app.py
```

### 5. 動作確認

ブラウザで `http://localhost:5000/health` にアクセス

✅ `{"status": "ok", "timestamp": "..."}` が返れば成功！

## Renderデプロイ（最短手順）

### 1. GitHubにpush

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Renderで作成

1. [render.com](https://render.com) にログイン
2. **New +** → **Web Service**
3. GitHubリポジトリを選択
4. **Apply render.yaml** をクリック（自動設定）
5. 環境変数を設定：
   - `LINE_CHANNEL_ACCESS_TOKEN`（LINE Botを使う場合）
   - `LINE_CHANNEL_SECRET`（LINE Botを使う場合）
6. **Create Web Service**

### 3. 確認

デプロイ完了後、`https://your-app.onrender.com/health` にアクセス

✅ `{"status": "ok"}` が返れば成功！

## トラブルシューティング

### 起動しない

- Python 3.11以上か確認: `python3 --version`
- 依存関係がインストールされているか: `pip list | grep flask`
- ポート5000が使用中でないか確認

### Renderでエラー

- **Logs**タブでエラー内容を確認
- 環境変数が設定されているか確認
- `render.yaml`の設定が正しいか確認

### LINE Botが動かない

- LINE DevelopersでWebhook URLが正しく設定されているか
- Channel Access Token と Channel Secret が正しいか
- Renderのログでエラー内容を確認

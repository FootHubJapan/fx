# アプリケーション起動ガイド

## 起動方法

### 1. 仮想環境をアクティベート

```bash
source venv/bin/activate
```

### 2. アプリケーション起動

```bash
python3 app.py
```

`.env` ファイルに `PORT=8080` が設定されているので、ポート8080で起動します。

## ポート競合の解決

### ポートが使用中の場合

**確認方法**:
```bash
lsof -i :5001
```

**解決方法**:

1. **使用中のプロセスを終了**:
   ```bash
   kill <PID>
   ```

2. **別のポートを使用**:
   ```bash
   PORT=8080 python3 app.py
   ```

3. **`.env` ファイルでポートを変更**:
   ```bash
   PORT=8080
   ```

## 動作確認

起動後、別のターミナルで：

```bash
# ヘルスチェック
curl http://localhost:8080/health

# ルートエンドポイント
curl http://localhost:8080/
```

期待されるレスポンス（`/health`）:
```json
{
  "status": "ok",
  "timestamp": "2025-02-01T..."
}
```

## バックグラウンド実行

バックグラウンドで実行する場合：

```bash
PORT=8080 python3 app.py > app.log 2>&1 &
```

ログを確認：
```bash
tail -f app.log
```

プロセスを終了：
```bash
pkill -f "python3 app.py"
```

## トラブルシューティング

### ポートが使用中

```bash
# 使用中のポートを確認
lsof -i :8080

# プロセスを終了
kill <PID>
```

### アプリケーションが起動しない

1. 仮想環境がアクティベートされているか確認
2. 依存関係がインストールされているか確認
3. `.env` ファイルが存在するか確認

### LINE Botが無効

`.env` ファイルに以下を追加：

```bash
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here
```

**注意**: LINE Botが無効でも、FX分析AIエージェントは動作します。

# ポート5000が使用中の場合の対処法

## 問題

```
Address already in use
Port 5000 is in use by another program.
```

Macでは、**AirPlay Receiver**がポート5000を使用していることが多いです。

## 解決方法

### 方法1: 別のポートを使用（推奨・簡単）

環境変数 `PORT` を設定して別のポートで起動：

```bash
source venv/bin/activate
PORT=5001 python3 app.py
```

または `.env` ファイルに追加：

```bash
PORT=5001
```

### 方法2: AirPlay Receiverを無効化

1. **システム設定** → **一般** → **AirDropと隔空播放（AirPlay）**
2. **AirPlay Receiver** をOFFにする

これでポート5000が使用可能になります。

### 方法3: 使用中のプロセスを確認

```bash
# ポート5000を使用しているプロセスを確認
lsof -i :5000

# プロセスを終了（必要に応じて）
kill -9 <PID>
```

## 確認方法

アプリケーション起動後：

```bash
# ヘルスチェック
curl http://localhost:5001/health

# またはブラウザで
open http://localhost:5001/health
```

期待されるレスポンス：

```json
{
  "status": "ok",
  "timestamp": "2025-02-01T..."
}
```

## 推奨設定

`.env` ファイルに以下を追加：

```bash
# ポート設定（AirPlay Receiverと競合しないように）
PORT=5001
```

これで毎回同じポートで起動できます。

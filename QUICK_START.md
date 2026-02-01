# クイックスタート

## アプリケーション起動

### 1. 仮想環境をアクティベート

```bash
source venv/bin/activate
```

### 2. アプリケーション起動

**重要**: ポート5000が使用中の場合は、環境変数でポートを指定：

```bash
# 方法1: 環境変数を同じ行で指定
PORT=5001 python3 app.py

# 方法2: .envファイルに設定済みの場合
python3 app.py
```

### 3. 動作確認

別のターミナルで：

```bash
curl http://localhost:5001/health
```

またはブラウザで `http://localhost:5001/health` にアクセス

## よくある問題

### ポート5000が使用中

**原因**: MacのAirPlay Receiverがポート5000を使用

**解決方法**:
1. `.env` ファイルに `PORT=5001` を追加
2. または `PORT=5001 python3 app.py` で起動

### LINE Botが無効

**原因**: `.env` ファイルにLINE Botの認証情報が設定されていない

**解決方法**: `.env` ファイルに以下を追加：

```bash
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here
```

**注意**: LINE Botが無効でも、FX分析AIエージェントは動作します。

## 次のステップ

- **データ更新**: `python3 jobs/download_bi5.py ...`
- **モデル学習**: `python3 jobs/auto_train_model.py --pair USDJPY`
- **FX分析**: LINE Botから「予測」コマンドを送信

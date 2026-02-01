# 503 Service Unavailable エラーの解決方法

## エラーの原因

503エラーは、`app.py`の`/callback`エンドポイントで`handler`が初期化されていない場合に発生します。

```python
@app.route("/callback", methods=["POST"])
def callback():
    if not handler:
        print("[ERROR] LINE handler not initialized. Check LINE_CHANNEL_SECRET.")
        abort(503)  # ← ここで503を返している
```

`handler`が初期化されない原因は、**環境変数が設定されていない**ことです。

## 解決手順

### 1. Renderの環境変数を確認

Render Dashboard → あなたのサービス → **Environment** タブ

以下の環境変数が設定されているか確認：

- ✅ `LINE_CHANNEL_ACCESS_TOKEN` - 設定されているか？
- ✅ `LINE_CHANNEL_SECRET` - 設定されているか？

**設定されていない場合**：
1. **Add Environment Variable** をクリック
2. Key と Value を入力
3. **Save Changes** をクリック
4. **Manual Deploy** → **Deploy latest commit** で再デプロイ

### 2. 環境変数の取得方法

#### LINE_CHANNEL_SECRET
- LINE Developers → チャネル → **Basic settings** タブ
- **Channel secret** をコピー

#### LINE_CHANNEL_ACCESS_TOKEN（長期）
- LINE Developers → チャネル → **Messaging API** タブ
- 下の方に **「Channel access token（長期）」** セクション
- **発行** または **再発行** をクリック
- 表示されたトークンをコピー（**一度しか表示されません**）

### 3. サービスが起動しているか確認

ブラウザで以下にアクセス：

```
https://fx-orm5.onrender.com/health
```

期待されるレスポンス：
```json
{
  "status": "ok",
  "timestamp": "2025-02-01T..."
}
```

✅ 200 OKが返ればサービスは起動しています  
❌ エラーが出る場合は、Renderの**Logs**タブでエラー内容を確認

### 4. Renderのログを確認

Render Dashboard → あなたのサービス → **Logs** タブ

以下のようなエラーメッセージがないか確認：

```
[WARN] LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET not set. LINE features will be disabled.
[ERROR] LINE handler not initialized. Check LINE_CHANNEL_SECRET.
```

このメッセージが出ている場合、環境変数が設定されていません。

### 5. 再デプロイ

環境変数を設定・更新した後は、**必ず再デプロイ**が必要です：

1. Render Dashboard → あなたのサービス
2. **Manual Deploy** → **Deploy latest commit**
3. デプロイ完了を待つ（1-2分）
4. 再度Webhook検証を試す

## 確認チェックリスト

- [ ] Renderの環境変数に `LINE_CHANNEL_ACCESS_TOKEN` が設定されている
- [ ] Renderの環境変数に `LINE_CHANNEL_SECRET` が設定されている
- [ ] 環境変数の値にスペースや改行が入っていない
- [ ] 環境変数設定後に再デプロイを実行した
- [ ] `/health` エンドポイントが200 OKを返す
- [ ] Renderのログにエラーメッセージがない

## よくある間違い

### ❌ 間違い1: 環境変数名のタイポ
```
LINE_CHANNEL_ACCESS_TOKEN  ← 正しい
LINE_CHANNEL_ACCESS_TOKEN_  ← 間違い（末尾のアンダースコア）
LINE_CHANNEL_ACCESS_TOKENS  ← 間違い（複数形）
```

### ❌ 間違い2: 値に余分なスペース
```
LINE_CHANNEL_ACCESS_TOKEN = your_token  ← 間違い（=の前後にスペース）
LINE_CHANNEL_ACCESS_TOKEN=your_token    ← 正しい
```

### ❌ 間違い3: 再デプロイを忘れる
環境変数を設定しても、**再デプロイしないと反映されません**。

## それでも解決しない場合

1. **Renderのログ**を確認して、具体的なエラーメッセージを特定
2. **/health** エンドポイントが200 OKを返すか確認
3. 環境変数の値が正しいか再確認（コピペミスがないか）
4. Channel Access Tokenを再発行して、新しいトークンで試す

# LINE Bot セットアップ完全ガイド

## ✅ Webhook URL（確定版）

**あなたのWebhook URLはこれです：**

```
https://fx-orm5.onrender.com/callback
```

`app.py`に`@app.route("/callback", methods=["POST"])`が実装されているので、このURLをLINE Developersに設定してください。

---

## セットアップ手順（この順で実行）

### 1. LINE Developers で Webhook URL を設定

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. 対象チャネルを選択
3. **Messaging API** タブを開く
4. **Webhook URL** に以下を入力：
   ```
   https://fx-orm5.onrender.com/callback
   ```
5. **Webhookの利用** を **ON** にする
6. **検証** ボタンをクリック
   - ✅ **200 OK** が返れば成功
   - ❌ **405 Method Not Allowed** が出る場合は、URLが正しいか確認（末尾に`/callback`が付いているか）

### 2. Channel Access Token（長期）を発行

**重要**: Channel Access Tokenは **LINE Developers** 側で発行します（LINE Official Account Manager側では発行できません）。

1. LINE Developers Console → 対象チャネル → **Messaging API** タブ
2. 下の方に **「Channel access token（長期）」** セクションがある
3. **発行** または **再発行** ボタンをクリック
4. 表示されたトークンをコピー（**このトークンは一度しか表示されません**）

### 3. Render の環境変数を設定

Render Dashboard → あなたのサービス → **Environment** タブ

以下の環境変数を追加：

| Key | Value | 説明 |
|-----|-------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | （ステップ2で発行したトークン） | Channel Access Token（長期） |
| `LINE_CHANNEL_SECRET` | （チャネル設定から取得） | Channel Secret |
| `NATIVE_AI_URL` | （あなたのAI API URL） | ネイティブAIのURL |
| `NATIVE_AI_API_KEY` | （オプション） | ネイティブAIのAPIキー |

**重要**: 
- 値は **Renderの画面で直接入力**（`.env`ファイルはコミットしない）
- トークン類は **このチャットに貼らない**（漏洩防止）

### 4. LINE Official Account Manager で自動応答をOFF

1. [LINE Official Account Manager](https://manager.line.biz/) にログイン
2. 対象アカウントを選択
3. **設定** → **応答設定**
4. 以下を設定：
   - **Webhook：ON** ✅
   - **応答メッセージ：OFF** ✅（自動応答を止める）
   - **あいさつメッセージ**：好み（最初だけならONでもOK）

### 5. 動作確認

1. Renderでデプロイが完了していることを確認
2. LINEアプリでボットに「こんにちは」と送信
3. ネイティブAIからの応答が返ってくることを確認

---

## トラブルシューティング

### 405 Method Not Allowed

**原因**: Webhook URLが間違っている

**解決策**:
- Webhook URLが `https://fx-orm5.onrender.com/callback` になっているか確認
- 末尾に `/callback` が付いているか確認
- ルート（`/`）ではなく `/callback` を指定

### 401 Unauthorized

**原因**: Channel Access Token または Channel Secret が間違っている

**解決策**:
- Renderの環境変数が正しく設定されているか確認
- Channel Access Token を再発行して、Renderの環境変数を更新
- スペースや改行が入っていないか確認

### 自動応答メッセージが返ってくる

**原因**: LINE Official Account Manager側の自動応答がONになっている

**解決策**:
- LINE Official Account Manager → 応答設定 → **応答メッセージ：OFF**

### Webhook検証が失敗する

**原因**: Renderのサービスが起動していない、またはエラーが発生している

**解決策**:
1. Renderの **Logs** タブでエラーを確認
2. `/health` エンドポイントにアクセスしてサービスが起動しているか確認
   ```
   https://fx-orm5.onrender.com/health
   ```
3. 環境変数が正しく設定されているか確認

---

## セキュリティ注意事項

⚠️ **重要**: スクショやチャットに **Channel Secret** や **Channel Access Token** を貼らないでください。

もし既に漏洩した可能性がある場合は：

1. **Channel Access Token を再発行**（LINE Developers → Messaging API → 再発行）
2. Renderの環境変数を新しいトークンに更新
3. 古いトークンは無効化される

---

## 環境変数テンプレート（ローカル開発用）

`.env`ファイル（**このファイルはGitにコミットしない**）：

```env
# LINE Bot設定
LINE_CHANNEL_ACCESS_TOKEN=<<<ここに長期アクセストークンを貼る>>>
LINE_CHANNEL_SECRET=<<<ここにChannel secretを貼る>>>

# ネイティブAI設定（OpenAI不使用）
NATIVE_AI_URL=https://your-ai.example.com/chat
NATIVE_AI_API_KEY=<<<必要ならBearer用キーを貼る>>>
NATIVE_AI_TIMEOUT_SEC=20

# TradingEconomics API（オプション）
TE_API_KEY=guest:guest

# ポート（ローカル開発時のみ）
PORT=5000
```

**注意**: `<<<...>>>`の部分を実際の値に置き換えてください。このファイルは`.gitignore`に含まれているので、Gitにはコミットされません。

---

## 確認チェックリスト

- [ ] LINE Developers で Webhook URL が `https://fx-orm5.onrender.com/callback` に設定されている
- [ ] Webhookの利用がONになっている
- [ ] Webhook検証で200 OKが返る
- [ ] Channel Access Token（長期）を発行した
- [ ] Renderの環境変数に `LINE_CHANNEL_ACCESS_TOKEN` と `LINE_CHANNEL_SECRET` を設定した
- [ ] Renderの環境変数に `NATIVE_AI_URL` を設定した
- [ ] LINE Official Account Manager で応答メッセージをOFFにした
- [ ] LINEアプリでボットにメッセージを送信して動作確認した

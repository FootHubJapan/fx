# ネイティブAI連携セットアップ

## 概要

このプロジェクトは、OpenAIを使わずに**あなたのネイティブAI（HTTP API）**を呼び出すように設計されています。

**動作フロー**: コマンド（「分析」「予測」等）以外のメッセージは全てネイティブAIに送信されます。

## 動作フロー

```
LINE → Webhook (/callback) → コマンド判定
  ├─ コマンド一致 → FX分析機能を実行
  └─ コマンド不一致 → ネイティブAI APIを呼び出し → LINEへ返信
```

## セットアップ手順

### 1. 環境変数の設定

`.env`ファイルまたはRenderの環境変数に以下を追加：

```bash
# ネイティブAIのURL（必須）
NATIVE_AI_URL=https://your-ai.example.com/chat

# APIキー（オプション、必要な場合のみ）
NATIVE_AI_API_KEY=your_api_key_here

# タイムアウト秒数（オプション、デフォルト: 20秒）
NATIVE_AI_TIMEOUT_SEC=20
```

**注意**: URL末尾の改行/スペースがあると失敗しがちなので、`.strip()`で処理済みです。

### 2. ネイティブAI APIの仕様

あなたのAI APIは以下の形式でリクエストを受け取り、レスポンスを返す必要があります：

#### リクエスト

```http
POST https://your-ai.example.com/chat
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY  # NATIVE_AI_API_KEYが設定されている場合

{
  "text": "ユーザーのメッセージ",
  "context": "追加コンテキスト（オプション）"
}
```

#### レスポンス

```json
{
  "reply": "AIからの返答テキスト"
}
```

**または**

```json
{
  "response": "AIからの返答テキスト"
}
```

**または**

```json
{
  "text": "AIからの返答テキスト"
}
```

### 3. context のカスタマイズ

`app.py`の`handle_message`関数内で、ネイティブAIに送る`context`をカスタマイズできます：

```python
# context に何を入れるか（必要に応じてカスタマイズ）
context = None

# 例: FX分析データをcontextに含める場合（コメントアウト解除）
# try:
#     features_path = Path("data/features/USDJPY/M5_features.parquet")
#     if features_path.exists():
#         import pandas as pd
#         df = pd.read_parquet(features_path)
#         latest = df.iloc[-1] if not df.empty else None
#         if latest is not None:
#             context = f"FX分析コンテキスト: RSI={latest.get('rsi_14', 'N/A')}, ATR={latest.get('atr_14', 'N/A')}"
# except Exception:
#     pass
```

**contextの用途例**:
- ユーザーID
- 通貨ペア固定文
- 簡易プロフィール
- 直近の分析結果
- 会話履歴

### 4. エラー時の処理カスタマイズ

`app.py`で、エラー時の返信方法を選択できます：

**A案（現在の実装）**: エラーメッセージをそのまま返す
```python
line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
```

**B案**: 一般化したメッセージを返す（コメントアウト解除して使用）
```python
if ai_reply.startswith("⚠️") or "失敗" in ai_reply or "エラー" in ai_reply:
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="申し訳ございません。現在AIが混み合っております。しばらくしてから再度お試しください。")
    )
else:
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
```

### 5. API形式のカスタマイズ

もしあなたのAI APIの形式が異なる場合は、`native_ai.py`の以下の部分を修正してください：

```python
# リクエストボディの形式を変更
payload = {"text": text}
if context:
    payload["context"] = context
# ↑ あなたのAPIに合わせて追加フィールドを設定

# レスポンスのパース部分を変更
reply = (
    data.get("reply")
    or data.get("response")
    or data.get("text")
)
# ↑ あなたのAPIのレスポンス形式に合わせて変更
```

## 動作確認

### ローカル

1. `.env`に`NATIVE_AI_URL`を設定
2. アプリを起動: `python app.py`
3. LINEでボットにメッセージを送信
4. コマンド以外のメッセージはネイティブAIが処理

### Render

1. RenderのEnvironmentタブで`NATIVE_AI_URL`を設定
2. 必要に応じて`NATIVE_AI_API_KEY`を設定
3. デプロイ後、LINEでテスト

## コマンド一覧

以下のコマンドはネイティブAIを呼び出さず、直接処理されます：

- `分析` - USDJPYの最新分析結果を表示
- `予測` - 売買予測を表示
- `データ更新` - Dukascopyから最新データを取得
- `イベント更新` - 経済指標・要人発言を更新
- `ヘルプ` - コマンド一覧を表示

**それ以外のメッセージ**は全てネイティブAIに送信されます。

## トラブルシューティング

### ネイティブAIが呼ばれない

- `NATIVE_AI_URL`が正しく設定されているか確認（末尾の改行/スペースに注意）
- Renderのログでエラーメッセージを確認
- `native_ai.py`のレスポンスパース部分が正しいか確認

### エラーメッセージが返る

- APIのURLが正しいか確認
- APIキーが必要な場合は`NATIVE_AI_API_KEY`を設定
- APIのレスポンス形式が期待通りか確認（`native_ai.py`を参照）
- タイムアウトが発生している場合は`NATIVE_AI_TIMEOUT_SEC`を増やす（デフォルト: 20秒）

### タイムアウトが発生する

- ネイティブAIの処理が重い場合、タイムアウト時間を延長:
  ```bash
  NATIVE_AI_TIMEOUT_SEC=30  # 30秒に延長
  ```
- LINE返信が遅延するため、20秒以内の応答を推奨
- 重い処理の場合は「受理だけ返す→後でPush返信」方式を検討（次の段階で実装可能）

# ネイティブAI エンドポイント仕様

## 概要

このプロジェクトは、あなたが作成したネイティブAI（HTTP API）を呼び出すように設計されています。

## エンドポイント設定

### 環境変数で設定

Renderの環境変数または`.env`ファイルに以下を設定：

```bash
NATIVE_AI_URL=https://your-ai-api.example.com/chat
NATIVE_AI_API_KEY=your_api_key_here  # オプション
NATIVE_AI_TIMEOUT_SEC=20  # オプション、デフォルト20秒
```

## リクエスト仕様

### HTTPメソッド
`POST`

### エンドポイント
`NATIVE_AI_URL`で指定したURL（例: `https://your-ai-api.example.com/chat`）

### リクエストヘッダー

```http
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY  # NATIVE_AI_API_KEYが設定されている場合のみ
```

### リクエストボディ

```json
{
  "text": "ユーザーがLINEで送信したメッセージ",
  "context": "追加コンテキスト（オプション、現在はnull）"
}
```

**例**:
```json
{
  "text": "こんにちは",
  "context": null
}
```

## レスポンス仕様

### 成功時（200 OK）

以下のいずれかの形式で返してください：

**形式1（推奨）**:
```json
{
  "reply": "AIからの返答テキスト"
}
```

**形式2**:
```json
{
  "response": "AIからの返答テキスト"
}
```

**形式3**:
```json
{
  "text": "AIからの返答テキスト"
}
```

### エラー時（4xx, 5xx）

エラーメッセージがそのままLINEユーザーに返されます：

```json
{
  "error": "エラーメッセージ"
}
```

または、HTTPステータスコードが400以上の場合、レスポンス本文がエラーメッセージとして表示されます。

## 実装例

### Python (Flask) の例

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_text = data.get("text", "")
    context = data.get("context")
    
    # ここでAI処理
    ai_reply = your_ai_function(user_text, context)
    
    return jsonify({
        "reply": ai_reply
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Node.js (Express) の例

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/chat', (req, res) => {
  const { text, context } = req.body;
  
  // ここでAI処理
  const aiReply = yourAIFunction(text, context);
  
  res.json({
    reply: aiReply
  });
});

app.listen(8000, () => {
  console.log('AI server running on port 8000');
});
```

## タイムアウト

- デフォルト: 20秒
- 設定可能: `NATIVE_AI_TIMEOUT_SEC`環境変数で変更
- 推奨: 20秒以内で応答（LINE返信が遅延しないように）

## エラーハンドリング

### タイムアウト時
```
ネイティブAIがタイムアウトしました（20s）
```

### HTTPエラー時
```
ネイティブAI呼び出し失敗: HTTP 500
[エラーレスポンス本文（最大600文字）]
```

### JSONパースエラー時
```
ネイティブAIの応答がJSONではありません:
[レスポンス本文（最大1500文字）]
```

### 予想外の形式時
```
ネイティブAIの返却形式が想定外です:
[レスポンスJSON（最大1500文字）]
```

## テスト方法

### curlでテスト

```bash
curl -X POST https://your-ai-api.example.com/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "text": "こんにちは",
    "context": null
  }'
```

期待されるレスポンス:
```json
{
  "reply": "こんにちは！何かお手伝いできることはありますか？"
}
```

## 現在の実装状況

- ✅ リクエスト送信: `native_ai.py`で実装済み
- ✅ レスポンスパース: `reply` / `response` / `text` のいずれかに対応
- ✅ エラーハンドリング: タイムアウト・HTTPエラー・JSONエラーに対応
- ✅ タイムアウト設定: 環境変数で変更可能

## カスタマイズ

もしあなたのAPI形式が異なる場合は、`native_ai.py`の以下を修正：

1. **リクエストボディ**: `payload`の構造を変更（47-49行目）
2. **レスポンスパース**: `reply`の取得部分を変更（70-74行目）

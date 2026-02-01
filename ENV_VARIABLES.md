# 環境変数設定ガイド

このプロジェクトで使用する環境変数の一覧と設定方法です。

## 必須環境変数（LINE Bot使用時）

### LINE Bot設定

| 変数名 | 説明 | 取得方法 |
|--------|------|----------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Botのアクセストークン | [LINE Developers Console](https://developers.line.biz/console/) で発行 |
| `LINE_CHANNEL_SECRET` | LINE Botのシークレット | [LINE Developers Console](https://developers.line.biz/console/) で取得 |

**設定方法**:
1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. プロバイダーとチャネル（Messaging API）を作成
3. Channel Access Token と Channel Secret をコピー
4. `.env` ファイルまたは Render の環境変数に設定

## オプション環境変数

### 外部ネイティブAI（オプション）

**重要**: このプロジェクトには**プロジェクト内のFX分析AIエージェント**が組み込まれており、外部APIは**オプション**です。

| 変数名 | 説明 | 必須 | デフォルト |
|--------|------|------|-----------|
| `NATIVE_AI_URL` | 外部AI APIのURL | オプション | なし（未設定時はFX分析AIエージェントを使用） |
| `NATIVE_AI_API_KEY` | 外部AI APIの認証キー | オプション | なし |
| `NATIVE_AI_TIMEOUT_SEC` | 外部AI APIのタイムアウト（秒） | オプション | 20 |

**動作**:
- `NATIVE_AI_URL` が**設定されている場合**: 外部APIを呼び出し
- `NATIVE_AI_URL` が**設定されていない場合**: プロジェクト内のFX分析AIエージェントが自動的に使用される

**設定例**:
```bash
# 外部APIを使う場合（オプション）
NATIVE_AI_URL=https://your-ai-api.example.com/chat
NATIVE_AI_API_KEY=your_api_key_here
NATIVE_AI_TIMEOUT_SEC=20
```

### TradingEconomics API（オプション）

| 変数名 | 説明 | 必須 | デフォルト |
|--------|------|------|-----------|
| `TE_API_KEY` | TradingEconomics APIキー | オプション | `guest:guest` |

**設定例**:
```bash
# デフォルト（無料プラン）
TE_API_KEY=guest:guest

# 有料プランの場合
TE_API_KEY=your_api_key:your_secret
```

### ポート設定（ローカル開発時のみ）

| 変数名 | 説明 | 必須 | デフォルト |
|--------|------|------|-----------|
| `PORT` | アプリケーションのポート番号 | オプション | 5000 |

**注意**: Renderでは `$PORT` が自動設定されるため、設定不要です。

## 設定方法

### ローカル開発（`.env`ファイル）

1. `.env.example` をコピー:
   ```bash
   cp .env.example .env
   ```

2. `.env` ファイルを編集:
   ```bash
   # LINE Bot設定（必須）
   LINE_CHANNEL_ACCESS_TOKEN=your_token_here
   LINE_CHANNEL_SECRET=your_secret_here

   # 外部ネイティブAI（オプション）
   # NATIVE_AI_URL=https://your-ai.example.com/chat
   # NATIVE_AI_API_KEY=your_api_key_here

   # TradingEconomics API（オプション）
   TE_API_KEY=guest:guest

   # ポート（ローカル開発時のみ）
   PORT=5000
   ```

### Render（環境変数）

1. Render Dashboard → 対象サービス → **Environment** タブ
2. **Add Environment Variable** をクリック
3. Key と Value を入力して保存

**設定すべき環境変数**:
- `LINE_CHANNEL_ACCESS_TOKEN`（必須）
- `LINE_CHANNEL_SECRET`（必須）
- `NATIVE_AI_URL`（オプション、外部APIを使う場合のみ）
- `NATIVE_AI_API_KEY`（オプション、外部APIを使う場合のみ）
- `TE_API_KEY`（オプション、デフォルト: `guest:guest`）

## よくある質問

### Q: `NATIVE_AI_URL` は必須ですか？

**A: いいえ、オプションです。**

- **設定しない場合**: プロジェクト内のFX分析AIエージェントが自動的に使用されます
- **設定する場合**: 外部のHTTP APIを呼び出します

### Q: FX分析AIエージェントを使うのに環境変数は必要ですか？

**A: いいえ、不要です。**

FX分析AIエージェント（`fx_ai_agent.py`）はプロジェクト内のAIで、環境変数は不要です。データさえあれば動作します。

### Q: 外部APIとFX分析AIエージェントのどちらが使われますか？

**優先順位**:
1. **FX関連の質問**: FX分析AIエージェントが回答
2. **その他の質問**: 
   - `NATIVE_AI_URL` が設定されている場合 → 外部API
   - `NATIVE_AI_URL` が設定されていない場合 → FX分析AIエージェント

### Q: 両方設定できますか？

**A: はい、できます。**

- FX関連の質問 → FX分析AIエージェント
- その他の質問 → 外部API（`NATIVE_AI_URL`）

## 動作確認

### 環境変数の確認

```bash
# ローカル開発時
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('LINE_CHANNEL_ACCESS_TOKEN:', 'SET' if os.getenv('LINE_CHANNEL_ACCESS_TOKEN') else 'NOT SET')"
```

### アプリケーション起動時のログ確認

起動時に以下のログが表示されます：

```
[INFO] LINE Bot API initialized successfully
[WARN] native_ai module not found. External native AI features will be disabled.
```

または

```
[INFO] LINE Bot API initialized successfully
[INFO] FX AI Agent available
```

## トラブルシューティング

### エラー: "LINE_CHANNEL_ACCESS_TOKEN not set"

`.env` ファイルまたは Render の環境変数に `LINE_CHANNEL_ACCESS_TOKEN` を設定してください。

### エラー: "NATIVE_AI_URL が未設定です"

外部APIを使う場合は `NATIVE_AI_URL` を設定してください。設定しない場合は、FX分析AIエージェントが自動的に使用されます。

### 環境変数が読み込まれない

1. `.env` ファイルがプロジェクトルートにあるか確認
2. `.env` ファイルの構文エラーを確認（余分なスペース、引用符など）
3. アプリケーションを再起動

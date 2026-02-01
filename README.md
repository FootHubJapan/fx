# FX Analysis Agent with LINE Bot Integration

USDJPYを中心としたFX分析システムとLINEボット連携。

## 機能

- **データ収集**: Dukascopyからティックデータを自動取得
- **バー生成**: M1/M5/H1/D1/1M/6Mなど全時間足を自動生成
- **特徴量生成**: テクニカル指標 + ファンダメンタル（経済指標・要人発言）
- **予測分析**: マルチ時間足分析による売買判断
- **LINE連携**: LINEから分析結果を取得・レポート生成

## セットアップ

### 1. 依存関係のインストール

```bash
# Python 3.11以上が必要
python3 --version

# 仮想環境作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成（`.env.example`をコピー）：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```bash
# LINE Bot設定（必須）
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here

# TradingEconomics API（オプション、guest:guestでも可）
TE_API_KEY=guest:guest

# ポート（ローカル開発時のみ、Renderでは自動設定）
PORT=5000
```

**LINE Bot設定の取得方法**:
1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. プロバイダーを作成
3. チャネルを作成（Messaging API）
4. Channel Access Token と Channel Secret をコピー

### 3. ローカル起動

#### 3-1. アプリケーション起動

```bash
python app.py
```

起動確認：
- ブラウザで `http://localhost:5000/health` にアクセス
- `{"status": "ok", "timestamp": "..."}` が返ればOK

#### 3-2. データ処理ジョブ（オプション）

データ分析機能を使う場合は、以下のジョブを実行：

```bash
# データ取得（1日分）
python jobs/download_bi5.py --pair USDJPY --start 2025-01-01T00 --end 2025-01-02T00

# M1バー生成
python jobs/build_m1_from_bi5.py --pair USDJPY --start-date 2025-01-01 --end-date 2025-01-02

# 全時間足生成
python jobs/build_bars_from_m1.py --pair USDJPY

# イベント取得
python jobs/fetch_macro_events.py --events-cache data/events/events_cache.parquet
python jobs/fetch_rss_events.py --events-cache data/events/events_cache.parquet

# 特徴量生成
python jobs/build_features.py --bars data/bars/USDJPY/tf=M5/all.parquet --out data/features/USDJPY/M5_features.parquet --events-cache data/events/events_cache.parquet
```

## Renderデプロイ

### Render設定方針

このプロジェクトは **`render.yaml` を使用した自動設定** を推奨します。

- **起動方式**: `gunicorn` でWSGIサーバーとして起動
- **ポート**: Renderが自動設定する `$PORT` 環境変数を使用
- **ホスト**: `0.0.0.0` でバインド（外部アクセス可能）
- **ヘルスチェック**: `/health` エンドポイントを使用
- **Pythonバージョン**: 3.11.0（`runtime.txt`で指定）

### 前提条件

- GitHubアカウント
- Renderアカウント（[render.com](https://render.com)で無料登録可能）
- LINE Developersアカウント（LINE Bot機能を使う場合）

### デプロイ手順

#### 1. GitHubリポジトリにpush

```bash
git add .
git commit -m "feat: Render deploy support"
git push origin main
```

#### 2. RenderでWeb Serviceを作成

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. **New +** → **Web Service** を選択
3. GitHubリポジトリを選択（または **Connect GitHub** で連携）
4. **Apply render.yaml** を選択（推奨）
   - これにより `render.yaml` の設定が自動適用されます
   - 手動設定する場合は以下を入力：
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

#### 3. 環境変数の設定

Renderの **Environment** タブで以下を設定：

| Key | Value | 必須 | 説明 |
|-----|-------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | （LINE Developersから取得） | LINE Bot使用時 | LINE Botのアクセストークン |
| `LINE_CHANNEL_SECRET` | （LINE Developersから取得） | LINE Bot使用時 | LINE Botのシークレット |
| `NATIVE_AI_URL` | （あなたのAI API URL） | オプション | ネイティブAIのHTTP API URL |
| `NATIVE_AI_API_KEY` | （APIキー） | オプション | ネイティブAIの認証キー（必要な場合） |
| `TE_API_KEY` | `guest:guest` | オプション | TradingEconomics APIキー |

**環境変数の設定方法**:
1. Renderのサービス画面で **Environment** タブを開く
2. **Add Environment Variable** をクリック
3. Key と Value を入力して保存

> **Note**: LINE Botを使わない場合でも、`/health` エンドポイントは動作します。

#### 4. LINE Webhook設定（LINE Botを使う場合）

1. [LINE Developers Console](https://developers.line.biz/console/) でチャネルを開く
2. **Messaging API** タブ → **Webhook URL** に以下を設定：
   ```
   https://your-app-name.onrender.com/callback
   ```
   （`your-app-name` は Renderで設定したサービス名）
   > **重要**: エンドポイントは `/callback` です（`/` ではありません）
3. **Webhook** を有効化（**Use webhook** をON）
4. **Verify** ボタンで接続確認
   - ✅ **200 OK** が返れば成功
   - ❌ **405 Method Not Allowed** が出る場合は、URLが正しいか確認

#### 4-1. Channel Access Token（長期）の発行

**重要**: Channel Access Tokenは **LINE Developers** 側で発行します。

1. LINE Developers Console → 対象チャネル → **Messaging API** タブ
2. 下の方に **「Channel access token（長期）」** セクションがある
3. **発行** または **再発行** ボタンをクリック
4. 表示されたトークンをコピー（**このトークンは一度しか表示されません**）
5. Renderの環境変数 `LINE_CHANNEL_ACCESS_TOKEN` に設定

#### 4-2. LINE Official Account Manager で自動応答をOFF

1. [LINE Official Account Manager](https://manager.line.biz/) にログイン
2. 対象アカウント → **設定** → **応答設定**
3. 以下を設定：
   - **Webhook：ON** ✅
   - **応答メッセージ：OFF** ✅（自動応答を止める）

#### 5. デプロイ実行

- **Manual Deploy** → **Deploy latest commit** をクリック
- または、GitHubにpushすると自動デプロイされます

#### 6. 動作確認

**ヘルスチェックURL**: `https://your-app-name.onrender.com/health`

期待されるレスポンス（200 OK）:
```json
{
  "status": "ok",
  "timestamp": "2025-02-01T12:00:00.000000+00:00"
}
```

**ルートエンドポイント**: `https://your-app-name.onrender.com/`
- サービス情報とLINE Botの有効/無効状態が表示されます

### トラブルシューティング

#### ビルドエラー

- **ログ確認**: Renderの **Logs** タブでエラー内容を確認
- **Pythonバージョン**: `runtime.txt` で3.11.0を指定済み
- **依存関係**: `requirements.txt` のパッケージ名・バージョンを確認

#### 起動エラー

- **環境変数**: LINE_CHANNEL_ACCESS_TOKEN と LINE_CHANNEL_SECRET が設定されているか確認
- **ポート**: `$PORT` 環境変数が自動設定されているか確認（Renderが自動設定）
- **ログ**: Renderの **Logs** タブで起動ログを確認

#### LINE Webhookエラー

- **405 Method Not Allowed**: Webhook URLが `/callback` になっているか確認（ルート `/` ではなく）
- **401 Unauthorized**: Channel Access Token または Channel Secret が正しいか確認
- **自動応答が返る**: LINE Official Account Manager で応答メッセージをOFFにする
- **URL確認**: Webhook URLが正しいか（`https://your-app.onrender.com/callback` の形式か）
- **SSL証明書**: Renderは自動でHTTPS証明書を発行（数分かかる場合あり）
- **チャネル設定**: LINE DevelopersでWebhookが有効になっているか確認
- **詳細**: `LINE_SETUP_GUIDE.md` を参照

## ディレクトリ構造

```
.
├── app.py                 # メインアプリケーション（LINE Webhook）
├── jobs/                  # データ処理ジョブ
│   ├── download_bi5.py           # Dukascopyからティックデータ取得
│   ├── build_m1_from_bi5.py     # M1バー生成
│   ├── build_bars_from_m1.py    # 全時間足生成（M5/H1/D1/1M/6M）
│   ├── fetch_macro_events.py    # TradingEconomics経済指標取得
│   ├── fetch_rss_events.py      # 中央銀行RSS取得
│   └── build_features.py        # 特徴量生成
├── data/                  # データ保存先（.gitignore対象）
│   ├── raw_bi5/          # 生データ（.bi5）
│   ├── bars/              # OHLCバー（Parquet）
│   ├── features/          # 特徴量（Parquet）
│   └── events/            # イベントキャッシュ（Parquet）
├── render.yaml            # Render Blueprint設定
├── Dockerfile             # Docker設定（オプション）
├── requirements.txt      # Python依存関係
├── .env.example          # 環境変数テンプレート
├── DEPLOY.md             # デプロイ手順
└── README.md
```

## 機能詳細

### データ収集
- **Dukascopy**: 無料ヒストリカルティックデータ（2003年〜現在）
- **TradingEconomics**: 経済指標カレンダー（重要度2&3、方向付きサプライズ）
- **中央銀行RSS**: BOJ/ECB/Fed/BoEの公式発表・要人発言

### 分析機能
- **マルチ時間足**: M1/M5/H1/D1/1M/6Mの全時間軸分析
- **テクニカル指標**: RSI, ATR, MA, ボラティリティ
- **ファンダメンタル**: 経済指標サプライズ、要人発言イベント
- **予測**: 短期（イベント反応）〜中長期（トレンド）まで対応

### LINEボット機能
- **分析結果表示**: 最新のテクニカル・イベント状況を表示
- **データ更新**: LINEからデータ取得を実行
- **予測表示**: 売買判断の提案
- **ネイティブAI連携**: OpenAI不使用、あなたのHTTP APIを呼び出し（`NATIVE_AI_URL`設定時）

## 動作確認

### ローカル環境

1. **アプリケーション起動**:
   ```bash
   python app.py
   ```
   起動ログに以下が表示されます:
   ```
   [INFO] Starting server on port 5000
   [INFO] Health check: http://localhost:5000/health
   ```

2. **ヘルスチェック**:
   ```bash
   curl http://localhost:5000/health
   ```
   またはブラウザで `http://localhost:5000/health` にアクセス
   
   期待されるレスポンス（200 OK）:
   ```json
   {
     "status": "ok",
     "timestamp": "2025-02-01T12:00:00.000000+00:00"
   }
   ```

3. **ルートエンドポイント確認**:
   ```bash
   curl http://localhost:5000/
   ```

### Render環境

**ヘルスチェックURL**: `https://your-app-name.onrender.com/health`

期待されるレスポンス（200 OK）:
```json
{
  "status": "ok",
  "timestamp": "2025-02-01T12:00:00.000000+00:00"
}
```

**ルートエンドポイント**: `https://your-app-name.onrender.com/`
- サービス情報とLINE Botの有効/無効状態が表示されます

## 次のステップ

1. **モデル学習**: 特徴量を使って機械学習モデルを構築
2. **バックテスト**: walk-forward検証で性能評価
3. **自動取引**: 条件付きエントリー/エグジットの実装
4. **他通貨対応**: EURUSD, GBPUSD, AUDUSDなどの追加
5. **レポート生成**: 日次/週次レポートの自動生成

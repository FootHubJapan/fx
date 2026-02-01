# FX Analysis Agent with LINE Bot Integration

USDJPYを中心としたFX分析システムとLINEボット連携。

## 機能

- **データ収集**: 複数データソース対応（Dukascopy、Yahoo Finance、OANDA）
- **バー生成**: M1/M5/H1/D1/1M/6Mなど全時間足を自動生成
- **特徴量生成**: テクニカル指標 + ファンダメンタル（経済指標・要人発言）
- **高精度分析AI**: LightGBMベースの機械学習モデルによる予測分析
- **予測分析**: マルチ時間足分析による売買判断（買い/売り/様子見）
- **LINE連携**: LINEから分析結果を取得・レポート生成
- **拡張性**: 将来的にサッカー勝敗分析などにも対応可能な設計

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

# 外部ネイティブAI（オプション）
# 設定しない場合: プロジェクト内のFX分析AIエージェントが自動的に使用されます
# NATIVE_AI_URL=https://your-ai.example.com/chat
# NATIVE_AI_API_KEY=your_api_key_here

# TradingEconomics API（オプション、guest:guestでも可）
TE_API_KEY=guest:guest

# ポート（ローカル開発時のみ、Renderでは自動設定）
PORT=5000
```

> **重要**: `NATIVE_AI_URL` は**オプション**です。設定しない場合、プロジェクト内のFX分析AIエージェントが自動的に使用されます。詳細は `ENV_VARIABLES.md` を参照してください。

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

**方法A: 既存のDukascopyパイプライン（推奨）**

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

**方法B: マルチデータソース統合パイプライン（新規）**

```bash
# 複数ソースからデータを取得・統合（推奨）
./run_multi_source_pipeline.sh 7

# または個別に実行
# Yahoo Financeから取得
python jobs/download_yahoo_finance.py --pair USDJPY --start-date 2025-01-01 --end-date 2025-01-02 --interval 1h

# OANDAから取得（OANDA_API_KEY環境変数が必要）
python jobs/download_oanda.py --pair USDJPY --start "2025-01-01T00:00:00" --end "2025-01-02T00:00:00" --granularity H1

# データをマージ
python jobs/merge_data_sources.py --pair USDJPY --start-date 2025-01-01 --end-date 2025-01-02
```

**モデル学習（オプション）**

```bash
python jobs/train_fx_model.py \
  --features data/features/USDJPY/M5_features.parquet \
  --output models/fx_usdjpy_model.pkl \
  --train-start 2020-01-01 \
  --train-end 2024-12-31 \
  --forward-bars 60
```

> **Note**: 
> - モデル学習は任意です。モデルが無い場合は、高精度ルールベース分析が自動的に使用されます。
> - マルチデータソースの詳細は `MULTI_SOURCE_DATA.md` を参照してください。

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
| `NATIVE_AI_URL` | （あなたのAI API URL） | オプション | 外部AI APIのURL（未設定時はFX分析AIエージェントを使用） |
| `NATIVE_AI_API_KEY` | （APIキー） | オプション | 外部AI APIの認証キー（必要な場合） |
| `TE_API_KEY` | `guest:guest` | オプション | TradingEconomics APIキー |

> **重要**: `NATIVE_AI_URL` は**オプション**です。設定しない場合、プロジェクト内のFX分析AIエージェントが自動的に使用されます。詳細は `ENV_VARIABLES.md` を参照してください。

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
├── fx_ai_agent.py        # FX分析AIエージェント（高精度分析）
├── jobs/                  # データ処理ジョブ
│   ├── download_bi5.py           # Dukascopyからティックデータ取得
│   ├── download_yahoo_finance.py # Yahoo FinanceからOHLCVデータ取得（新規）
│   ├── download_oanda.py         # OANDA APIからOHLCVデータ取得（新規）
│   ├── merge_data_sources.py     # 複数データソースをマージ（新規）
│   ├── build_m1_from_bi5.py     # M1バー生成
│   ├── build_bars_from_m1.py    # 全時間足生成（M5/H1/D1/1M/6M）
│   ├── fetch_macro_events.py    # TradingEconomics経済指標取得
│   ├── fetch_rss_events.py      # 中央銀行RSS取得
│   ├── build_features.py        # 特徴量生成
│   └── train_fx_model.py        # 高精度分析モデル学習
├── models/                # 学習済みモデル保存先（.gitignore対象）
│   └── fx_usdjpy_model.pkl      # FX予測モデル（学習後）
├── data/                  # データ保存先（.gitignore対象）
│   ├── raw_bi5/          # Dukascopy生データ（.bi5）
│   ├── bars/              # Dukascopy OHLCバー（Parquet）
│   ├── yahoo_finance/     # Yahoo Financeデータ（Parquet、新規）
│   ├── oanda/             # OANDAデータ（Parquet、新規）
│   ├── merged/            # マージされたデータ（Parquet、新規）
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

#### FX価格データ（複数ソース対応）
- **Dukascopy**: 無料ヒストリカルティックデータ（2003年〜現在、推奨）
- **Yahoo Finance**: 無料OHLCVデータ（yfinanceライブラリ経由、新規）
- **OANDA**: 公式API経由のOHLCVデータ（7日間無料トライアル、新規）
- **データマージ**: 複数ソースを統合してデータ品質を向上（`jobs/merge_data_sources.py`）

#### イベントデータ
- **TradingEconomics**: 経済指標カレンダー（重要度2&3、方向付きサプライズ）
- **中央銀行RSS**: BOJ/ECB/Fed/BoEの公式発表・要人発言

詳細は `MULTI_SOURCE_DATA.md` を参照してください。

### 分析機能
- **マルチ時間足**: M1/M5/H1/D1/1M/6Mの全時間軸分析
- **テクニカル指標**: RSI, ATR, MA, ボラティリティ
- **ファンダメンタル**: 経済指標サプライズ、要人発言イベント
- **予測**: 短期（イベント反応）〜中長期（トレンド）まで対応

### 高精度分析AIエージェント

**FX分析AIエージェント** (`fx_ai_agent.py`) は、以下の機能を提供します：

- **モデルベース分析**: LightGBM学習済みモデルによる高精度予測
- **ルールベース分析**: モデル未学習時も高精度なルールベース分析を実行
- **自然言語レポート**: 分析結果を自然言語で説明
- **主要要因抽出**: 判断に影響した要因を自動抽出
- **リスク評価**: ボラティリティ・スプレッドからリスクレベルを評価

**使い方**:

1. **モデル学習**（推奨）:
   ```bash
   python jobs/train_fx_model.py \
     --features data/features/USDJPY/M5_features.parquet \
     --output models/fx_usdjpy_model.pkl
   ```

2. **LINE Botから使用**:
   - 「予測」コマンド: 高精度予測を取得
   - 「分析」コマンド: 現在の市場状況を分析
   - FX関連の質問: 自動的にAIエージェントが回答

3. **Pythonコードから使用**:
   ```python
   from fx_ai_agent import analyze_fx
   
   # FX分析を実行
   result = analyze_fx("現在の相場状況を教えて", pair="USDJPY")
   print(result)
   ```

**出力例**:
```
💹 USDJPY 予測

方向: 買い
信頼度: 75%
現在価格: 150.25

📊 主要指標
RSI(14): 35.20
ATR(14): 0.0125
MA(20): 150.10

📈 イベント（24時間）
マクロ: 2件
ニュース: 1件

📋 詳細分析
市場は売られすぎの状態です。
最近の経済指標は強気のサプライズが多く、上昇要因となっています。

判断: 買い（信頼度: 75%）

🔑 主要要因
1. RSI売られすぎ
2. マクロイベント影響（+0.65）
```

### 将来の拡張（サッカー分析対応）

このプロジェクトは**分析特化型エージェント**として設計されており、将来的にサッカー勝敗分析にも対応可能です。

- **設計**: データソースを抽象化し、FX分析とサッカー分析を同じフレームワークで扱える構造
- **詳細**: `ARCHITECTURE.md` を参照

実装計画:
1. ✅ Phase 1: FX分析の高精度化（現在）
2. ⏳ Phase 2: データソース抽象化レイヤー実装
3. ⏳ Phase 3: サッカーデータソース実装
4. ⏳ Phase 4: サッカー分析エージェント実装

### LINEボット機能
- **分析結果表示**: 最新のテクニカル・イベント状況を表示
- **データ更新**: LINEからデータ取得を実行
- **予測表示**: 高精度AIエージェントによる売買判断の提案
- **AIエージェント**: プロジェクト内のFX分析AIエージェントが自動的に回答
- **外部AI連携**: オプションで外部HTTP APIを呼び出し（`NATIVE_AI_URL`設定時）

**LINE Botコマンド**:
- `分析`: 現在の市場状況を分析
- `予測`: 高精度AIエージェントによる予測を取得
- `データ更新`: データ取得ジョブを実行
- `イベント更新`: 経済指標・ニュースイベントを更新
- `ヘルプ`: コマンド一覧を表示

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

1. ✅ **モデル学習**: 特徴量を使って機械学習モデルを構築（`jobs/train_fx_model.py`）
2. **バックテスト**: walk-forward検証で性能評価
3. **モデル最適化**: ハイパーパラメータチューニング、特徴量選択
4. **自動取引**: 条件付きエントリー/エグジットの実装
5. **他通貨対応**: EURUSD, GBPUSD, AUDUSDなどの追加
6. **レポート生成**: 日次/週次レポートの自動生成
7. **サッカー分析対応**: データソース抽象化 → サッカー分析エージェント実装

## 関連ドキュメント

- `ARCHITECTURE.md`: アーキテクチャ設計（FX + 将来のサッカー分析対応）
- `DEPLOY.md`: Renderデプロイ詳細手順
- `QUICKSTART.md`: クイックスタートガイド
- `LINE_SETUP_GUIDE.md`: LINE Bot設定詳細ガイド

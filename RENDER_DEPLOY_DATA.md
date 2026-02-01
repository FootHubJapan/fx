# Renderデプロイ時のデータ問題解決ガイド

## 問題

RenderにデプロイしたLINE Botで「分析」コマンドを実行すると、「特徴量ファイルが見つかりません」というエラーが表示されます。

**原因**: `data/`ディレクトリは`.gitignore`に含まれているため、GitHubにpushされず、Renderの環境にはデータファイルが存在しません。

## 解決策

### オプション1: Render起動時にデータパイプラインを実行（推奨）

Renderの起動時に自動的にデータを生成する方法です。

#### 1. 起動スクリプトを作成

`start_render.sh`を作成：

```bash
#!/bin/bash
# Render起動スクリプト

# データディレクトリを作成
mkdir -p data/{raw_bi5,bars,features,events,logs,merged,yahoo_finance,oanda}

# データパイプラインを実行（最新7日分）
python3 jobs/download_yahoo_finance.py --pair USDJPY --start-date $(date -u -v-7d +%Y-%m-%d) --end-date $(date -u +%Y-%m-%d) --interval 1h || true

# M1バーを生成（Yahoo Financeデータから）
# または、直接M5バーを生成する場合はスキップ

# 特徴量を生成
python3 jobs/build_features.py --pair USDJPY --timeframe M5 || true

# アプリを起動
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

#### 2. `render.yaml`を更新

```yaml
services:
  - type: web
    name: fx-analysis-line-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: bash start_render.sh
    # ... その他の設定
```

**注意**: この方法は初回起動に時間がかかる可能性があります（数分）。

### オプション2: データが無い場合のフォールバック（現在の実装）

現在の実装では、データが無い場合にエラーメッセージを返します。これは正常な動作ですが、ユーザーには「データ更新」コマンドを実行するよう案内します。

**改善点**: `fx_ai_agent.py`を修正して、データが無い場合でも簡易的な分析を返すようにできます。

### オプション3: 外部ストレージからデータを取得

Google Drive、S3、またはGitHub Releasesにデータをアップロードし、起動時にダウンロードする方法です。

#### 例: GitHub Releasesからダウンロード

```bash
# start_render.sh
if [ ! -f "data/features/USDJPY/M5_features.parquet" ]; then
    # GitHub Releasesから最新のデータをダウンロード
    curl -L https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/features.zip -o /tmp/features.zip
    unzip -q /tmp/features.zip -d data/
fi
```

## 推奨アプローチ

**短期的**: オプション1（Render起動時にデータパイプラインを実行）

**長期的**: 
1. 定期的にデータを更新するCronジョブを設定（RenderのCron Jobs機能）
2. または、外部ストレージ（Google Drive/S3）にデータを保存し、起動時にダウンロード

## 実装手順（オプション1）

### ステップ1: 起動スクリプトを作成

`start_render.sh`を作成（上記参照）

### ステップ2: `render.yaml`を更新

`startCommand`を`bash start_render.sh`に変更

### ステップ3: GitHubにpush

```bash
git add start_render.sh render.yaml
git commit -m "feat: Add data pipeline to Render startup"
git push origin main
```

### ステップ4: Renderで再デプロイ

Render Dashboardで **Manual Deploy** を実行

## 注意事項

1. **起動時間**: データパイプラインの実行により、初回起動に数分かかる可能性があります
2. **タイムアウト**: Renderのタイムアウト設定（現在120秒）を確認してください
3. **エラーハンドリング**: データパイプラインが失敗してもアプリは起動するように`|| true`を追加しています

## トラブルシューティング

### 起動がタイムアウトする場合

1. `render.yaml`の`startCommand`のタイムアウトを延長
2. または、データパイプラインを非同期で実行（バックグラウンドジョブ）

### データが生成されない場合

1. Renderの **Logs** タブでエラーを確認
2. 環境変数（`TE_API_KEY`など）が設定されているか確認
3. ネットワーク接続を確認（外部APIへのアクセスが必要）

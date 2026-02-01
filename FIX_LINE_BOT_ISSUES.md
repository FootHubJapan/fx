# LINE Bot問題解決ガイド

画像で確認された問題を解決する手順です。

## 確認された問題

1. **外部AI接続エラー**: `your-ai-api.example.com` への接続エラー
2. **データ不足**: M1ファイルが見つからない
3. **特徴量データ不足**: USDJPYの特徴量データが見つからない

## 解決手順

### ステップ1: アプリケーションを再起動

修正を反映するために、アプリを再起動してください。

```bash
# 現在実行中のアプリを停止（Ctrl+C）

# 再起動
source venv/bin/activate
python3 app.py
```

**修正内容**:
- FXクエリは内部のFX分析AIエージェントで処理されます
- プレースホルダーURLの外部AIは呼び出されません

### ステップ2: データパイプラインを実行

データがないため、まずデータを生成する必要があります。

#### 方法A: 自動スクリプトを使用（推奨）

```bash
# 過去7日間のデータを取得・処理
./run_data_pipeline.sh 7

# 過去30日間のデータを取得・処理（より多くのデータ）
./run_data_pipeline.sh 30
```

#### 方法B: 手動で実行

```bash
# 1. BI5ダウンロード（過去7日間）
python3 jobs/download_bi5.py \
  --pair USDJPY \
  --start 2025-01-25T00 \
  --end 2025-02-01T00

# 2. M1バー生成
python3 jobs/build_m1_from_bi5.py \
  --pair USDJPY \
  --start-date 2025-01-25 \
  --end-date 2025-02-01

# 3. 全時間足バー生成
python3 jobs/build_bars_from_m1.py --pair USDJPY

# 4. イベントデータ取得（オプション）
python3 jobs/fetch_macro_events.py
python3 jobs/fetch_rss_events.py

# 5. 特徴量生成
python3 jobs/build_features.py --pair USDJPY --timeframe M5
```

**注意**: 
- 日付は実際の日付に合わせて変更してください
- データ量が多い場合、処理に時間がかかります（数分～数十分）

### ステップ3: LINE Botでテスト

データが生成されたら、LINE Botで以下を試してください：

1. **「分析」** - 最新の分析結果を表示
2. **「予測」** - AIによる高精度予測を表示
3. **「USD/JPY」** または **「usdjpy」** - FX分析を実行

## トラブルシューティング

### "No M1 parquet files found" エラー

→ ステップ2の「M1バー生成」が完了していない可能性があります。`build_m1_from_bi5.py` を実行してください。

### "USDJPYの特徴量データが見つかりません" エラー

→ ステップ2の「特徴量生成」が完了していない可能性があります。`build_features.py` を実行してください。

### 外部AI接続エラーが続く

→ `.env` ファイルを確認し、`NATIVE_AI_URL` が設定されている場合は空にするか削除してください：

```bash
# .env ファイルを編集
# NATIVE_AI_URL=  # この行をコメントアウトまたは削除
```

その後、アプリを再起動してください。

### ダウンロードが遅い

→ Dukascopyのサーバー負荷により時間がかかることがあります。時間をずらして再試行してください。

## データ保存場所の確認

データが正しく生成されているか確認：

```bash
# M1バーの確認
ls -la data/bars/USDJPY/tf=M1/date=*/

# 特徴量の確認
ls -la data/features/USDJPY/
```

## 次のステップ

データが生成されたら：

1. **モデル学習**: `python3 jobs/train_fx_model.py` を実行
2. **自動学習設定**: `jobs/auto_train_model.py` を `launchd` で定期実行
3. **LINE Bot活用**: 日常的に「分析」「予測」コマンドを使用

## 参考ドキュメント

- `DATA_PIPELINE_SETUP.md` - データパイプラインの詳細説明
- `RESTART_APP.md` - アプリ再起動の詳細
- `ENV_VARIABLES.md` - 環境変数の設定方法

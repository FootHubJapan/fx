# データパイプライン実行ガイド

FX分析に必要なデータを生成するための手順です。

## 前提条件

- Python 3.11以上がインストールされていること
- 仮想環境が有効化されていること（`source venv/bin/activate`）

## データパイプラインの流れ

```
1. BI5ファイルのダウンロード (download_bi5.py)
   ↓
2. M1バーの生成 (build_m1_from_bi5.py)
   ↓
3. 全時間足バーの生成 (build_bars_from_m1.py)
   ↓
4. 特徴量の生成 (build_features.py)
```

## 手順

### 1. BI5ファイルのダウンロード

Dukascopyから過去のティックデータをダウンロードします。

```bash
# 過去7日間のデータをダウンロード（例）
python3 jobs/download_bi5.py \
  --pair USDJPY \
  --start 2025-01-25T00 \
  --end 2025-02-01T00

# 過去30日間のデータをダウンロード（推奨）
python3 jobs/download_bi5.py \
  --pair USDJPY \
  --start 2025-01-01T00 \
  --end 2025-02-01T00
```

**注意**: 
- `--start`と`--end`はUTC時刻で指定します
- データ量が多い場合、ダウンロードに時間がかかります
- ダウンロードしたファイルは `data/raw_bi5/USDJPY/` に保存されます

### 2. M1バーの生成

BI5ファイルから1分足（M1）のOHLCVバーを生成します。

```bash
# 過去7日間のM1バーを生成
python3 jobs/build_m1_from_bi5.py \
  --pair USDJPY \
  --start-date 2025-01-25 \
  --end-date 2025-02-01

# 過去30日間のM1バーを生成（推奨）
python3 jobs/build_m1_from_bi5.py \
  --pair USDJPY \
  --start-date 2025-01-01 \
  --end-date 2025-02-01
```

**注意**:
- `--start-date`と`--end-date`は日付のみ（YYYY-MM-DD形式）
- 生成されたM1バーは `data/bars/USDJPY/tf=M1/date=YYYY-MM-DD/` に保存されます

### 3. 全時間足バーの生成

M1バーから他の時間足（M5, M15, H1, H4, D1, W1, 1M, 6M）を生成します。

```bash
python3 jobs/build_bars_from_m1.py --pair USDJPY
```

**注意**:
- M1バーが存在しない場合、エラーになります
- 生成されたバーは `data/bars/USDJPY/tf=<TIMEFRAME>/` に保存されます

### 4. 特徴量の生成

テクニカル指標やイベントデータを含む特徴量を生成します。

```bash
# イベントデータを先に取得（推奨）
python3 jobs/fetch_macro_events.py
python3 jobs/fetch_rss_events.py

# 特徴量を生成
python3 jobs/build_features.py \
  --pair USDJPY \
  --timeframe M5
```

**注意**:
- `--timeframe`は分析に使用する時間足を指定（M5, M15, H1など）
- 生成された特徴量は `data/features/USDJPY/M5_features.parquet` に保存されます
- イベントデータがない場合でも実行可能ですが、ファンダメンタル分析の精度が下がります

## 一括実行スクリプト

すべてのステップを一度に実行する場合：

```bash
#!/bin/bash
# 過去7日間のデータを取得・処理

PAIR=USDJPY
START_DATE=2025-01-25
END_DATE=2025-02-01
START_DATETIME="${START_DATE}T00"
END_DATETIME="${END_DATE}T00"

echo "1. BI5ダウンロード中..."
python3 jobs/download_bi5.py --pair $PAIR --start $START_DATETIME --end $END_DATETIME

echo "2. M1バー生成中..."
python3 jobs/build_m1_from_bi5.py --pair $PAIR --start-date $START_DATE --end-date $END_DATE

echo "3. 全時間足バー生成中..."
python3 jobs/build_bars_from_m1.py --pair $PAIR

echo "4. イベントデータ取得中..."
python3 jobs/fetch_macro_events.py
python3 jobs/fetch_rss_events.py

echo "5. 特徴量生成中..."
python3 jobs/build_features.py --pair $PAIR --timeframe M5

echo "✅ 完了！"
```

## LINE Botから実行

LINE Botから「データ更新」コマンドを送信すると、過去24時間のデータを自動的に取得・処理します。

## トラブルシューティング

### "No M1 parquet files found" エラー

- M1バーが生成されていない可能性があります
- ステップ2（`build_m1_from_bi5.py`）を実行してください

### "特徴量データが見つかりません" エラー

- 特徴量が生成されていない可能性があります
- ステップ4（`build_features.py`）を実行してください

### ダウンロードが遅い

- Dukascopyのサーバー負荷やネットワーク状況により時間がかかることがあります
- 時間をずらして再試行してください

### メモリ不足エラー

- データ量が多い場合、メモリ不足になることがあります
- 期間を短くして実行してください（例：7日間 → 3日間）

## データ保存場所

```
data/
├── raw_bi5/          # ダウンロードしたBI5ファイル
│   └── USDJPY/
├── bars/             # 生成されたOHLCVバー
│   └── USDJPY/
│       └── tf=M1/
│       └── tf=M5/
│       └── ...
└── features/         # 生成された特徴量
    └── USDJPY/
        └── M5_features.parquet
```

## 次のステップ

データが生成されたら：

1. LINE Botで「分析」または「予測」コマンドを試す
2. モデル学習を実行（`python3 jobs/train_fx_model.py`）
3. 自動学習を設定（`jobs/auto_train_model.py`）

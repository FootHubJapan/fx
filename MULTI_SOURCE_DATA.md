# マルチデータソース統合ガイド

複数のデータソース（Dukascopy、Yahoo Finance、OANDA）からFXデータを取得し、統合する方法です。

## 対応データソース

### 1. Dukascopy（既存・推奨）
- **特徴**: 高精度なティックデータ、無料
- **データ形式**: BI5ファイル → M1バー
- **期間**: 過去データも豊富
- **スクリプト**: `jobs/download_bi5.py`

### 2. Yahoo Finance（新規・無料）
- **特徴**: 簡単にアクセス可能、無料
- **データ形式**: 直接OHLCVバーを取得
- **期間**: 過去データも取得可能
- **スクリプト**: `jobs/download_yahoo_finance.py`
- **ライブラリ**: `yfinance`（無料）

### 3. OANDA（新規・無料トライアル）
- **特徴**: 公式API、7日間無料トライアル
- **データ形式**: REST API経由でOHLCVバーを取得
- **期間**: 32年以上の履歴データ
- **スクリプト**: `jobs/download_oanda.py`
- **APIキー**: [OANDA無料トライアル](https://www.oanda.com/foreign-exchange-data-services/en/exchange-rates-api/free-trial/)で取得

## セットアップ

### 1. 依存関係のインストール

```bash
pip install yfinance
```

または、requirements.txtから一括インストール：

```bash
pip install -r requirements.txt
```

### 2. OANDA APIキーの設定（オプション）

OANDAを使用する場合、無料トライアルでAPIキーを取得：

1. [OANDA無料トライアル](https://www.oanda.com/foreign-exchange-data-services/en/exchange-rates-api/free-trial/)に登録
2. APIキーを取得
3. 環境変数に設定：

```bash
export OANDA_API_KEY="your_api_key_here"
```

または、`.env`ファイルに追加：

```env
OANDA_API_KEY=your_api_key_here
```

## 使用方法

### Yahoo Financeからデータを取得

```bash
# 過去7日間の1時間足データを取得
python3 jobs/download_yahoo_finance.py \
  --pair USDJPY \
  --start-date 2026-01-25 \
  --end-date 2026-02-01 \
  --interval 1h

# 5分足データを取得
python3 jobs/download_yahoo_finance.py \
  --pair USDJPY \
  --start-date 2026-01-25 \
  --end-date 2026-02-01 \
  --interval 5m
```

**利用可能な時間足**: `1m`, `5m`, `15m`, `30m`, `1h`, `1d`

### OANDAからデータを取得

```bash
# 過去7日間の1時間足データを取得
python3 jobs/download_oanda.py \
  --pair USDJPY \
  --start "2026-01-25T00:00:00" \
  --end "2026-02-01T00:00:00" \
  --granularity H1

# 5分足データを取得
python3 jobs/download_oanda.py \
  --pair USDJPY \
  --start "2026-01-25T00:00:00" \
  --end "2026-02-01T00:00:00" \
  --granularity M5
```

**利用可能な時間足**: `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D`

### 複数ソースをマージ

複数のデータソースから取得したデータを統合：

```bash
python3 jobs/merge_data_sources.py \
  --pair USDJPY \
  --start-date 2026-01-25 \
  --end-date 2026-02-01 \
  --priority dukascopy,yahoo,oanda
```

**優先順位**:
- 同じタイムスタンプのデータがある場合、優先順位の高いソースのデータを使用
- デフォルト: `dukascopy` > `yahoo` > `oanda`

## データソースの比較

| ソース | 無料 | データ精度 | 取得速度 | 過去データ | 推奨用途 |
|--------|------|-----------|---------|-----------|---------|
| Dukascopy | ✅ | ⭐⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐⭐ | 高精度分析、バックテスト |
| Yahoo Finance | ✅ | ⭐⭐⭐⭐ | 速 | ⭐⭐⭐⭐ | クイック分析、補完データ |
| OANDA | トライアル | ⭐⭐⭐⭐⭐ | 速 | ⭐⭐⭐⭐⭐ | リアルタイム、公式データ |

## 統合データパイプライン

複数のソースからデータを取得して統合するスクリプト：

```bash
# 1. Dukascopyからデータ取得（既存）
python3 jobs/download_bi5.py --pair USDJPY --start 2026-01-25T00 --end 2026-02-01T00
python3 jobs/build_m1_from_bi5.py --pair USDJPY --start-date 2026-01-25 --end-date 2026-02-01

# 2. Yahoo Financeからデータ取得（補完）
python3 jobs/download_yahoo_finance.py --pair USDJPY --start-date 2026-01-25 --end-date 2026-02-01 --interval 1h

# 3. OANDAからデータ取得（オプション）
python3 jobs/download_oanda.py --pair USDJPY --start "2026-01-25T00:00:00" --end "2026-02-01T00:00:00" --granularity H1

# 4. データをマージ
python3 jobs/merge_data_sources.py --pair USDJPY --start-date 2026-01-25 --end-date 2026-02-01

# 5. マージされたデータから特徴量生成（既存のbuild_features.pyを拡張）
python3 jobs/build_features.py --pair USDJPY --timeframe M5 --data-source merged
```

## データ保存場所

```
data/
├── raw_bi5/              # Dukascopy BI5ファイル
│   └── USDJPY/
├── bars/                 # Dukascopy M1バー（処理済み）
│   └── USDJPY/
├── yahoo_finance/        # Yahoo Financeデータ（新規）
│   └── USDJPY/
│       └── USDJPY_1h_20260125_20260201.parquet
├── oanda/                # OANDAデータ（新規）
│   └── USDJPY/
│       └── USDJPY_H1_20260125T000000_20260201T000000.parquet
└── merged/               # マージされたデータ（新規）
    └── USDJPY/
        └── USDJPY_merged_2026-01-25_2026-02-01.parquet
```

## トラブルシューティング

### Yahoo Financeでデータが取得できない

- インターネット接続を確認
- ティッカーシンボルが正しいか確認（`USDJPY=X`）
- 期間が長すぎる場合は、期間を短くして再試行

### OANDA APIエラー

- APIキーが正しく設定されているか確認（`OANDA_API_KEY`環境変数）
- 無料トライアルの期間が切れていないか確認
- リクエスト制限（1,000 quotes/トライアル）を超えていないか確認

### マージ時にデータが重複する

- 優先順位を確認（`--priority`オプション）
- 各ソースのタイムスタンプがUTCで統一されているか確認

## 次のステップ

1. **データ品質の検証**: 各ソースのデータを比較して品質を確認
2. **特徴量生成の拡張**: マージされたデータを使用して特徴量を生成
3. **自動データ取得**: 定期的に複数ソースからデータを取得するスクリプトを作成

## 参考リンク

- [Yahoo Finance (yfinance)](https://github.com/ranaroussi/yfinance)
- [OANDA API Documentation](https://developer.oanda.com/)
- [OANDA無料トライアル](https://www.oanda.com/foreign-exchange-data-services/en/exchange-rates-api/free-trial/)

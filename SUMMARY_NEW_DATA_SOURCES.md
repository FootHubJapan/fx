# 新規データソース統合 - 実装完了サマリー

## 実装内容

ユーザーからの要望に基づき、以下のデータソースを統合しました：

1. **Yahoo Finance** - `yfinance`ライブラリ経由（無料）
2. **OANDA** - 公式API経由（7日間無料トライアル）
3. **ADVFN** - 調査済み（スクレイピング対応は将来実装可能）
4. **TradingView / Investing.com** - 参考情報として記録

## 作成・更新したファイル

### 新規作成

1. **`jobs/download_yahoo_finance.py`**
   - Yahoo FinanceからFXデータを取得
   - `yfinance`ライブラリを使用
   - 1m, 5m, 15m, 30m, 1h, 1dなどの時間足に対応

2. **`jobs/download_oanda.py`**
   - OANDA APIからFXデータを取得
   - REST API経由でOHLCVデータを取得
   - M1, M5, M15, H1, H4, Dなどの時間足に対応

3. **`jobs/merge_data_sources.py`**
   - 複数のデータソースを統合
   - 優先順位に基づいてデータをマージ
   - 同じタイムスタンプのデータは優先順位の高いソースを使用

4. **`run_multi_source_pipeline.sh`**
   - マルチデータソース統合パイプラインの自動実行スクリプト
   - Dukascopy、Yahoo Finance、OANDAを順次実行して統合

5. **`MULTI_SOURCE_DATA.md`**
   - マルチデータソース統合の詳細ガイド
   - 各データソースの使用方法、比較表、トラブルシューティング

6. **`SUMMARY_NEW_DATA_SOURCES.md`**（このファイル）
   - 実装内容のサマリー

### 更新

1. **`requirements.txt`**
   - `yfinance==0.2.40` を追加

2. **`ARCHITECTURE.md`**
   - データフロー図を更新（複数データソース対応）
   - データ収集層に新規スクリプトを追加

3. **`README.md`**
   - データ収集セクションを更新
   - ディレクトリ構造に新規ディレクトリを追加
   - データ処理ジョブセクションにマルチソース統合を追加

4. **`.env.example`**
   - `OANDA_API_KEY` の設定例を追加

## データソースの比較

| ソース | 無料 | データ精度 | 取得速度 | 過去データ | 推奨用途 |
|--------|------|-----------|---------|-----------|---------|
| Dukascopy | ✅ | ⭐⭐⭐⭐⭐ | 中 | ⭐⭐⭐⭐⭐ | 高精度分析、バックテスト |
| Yahoo Finance | ✅ | ⭐⭐⭐⭐ | 速 | ⭐⭐⭐⭐ | クイック分析、補完データ |
| OANDA | トライアル | ⭐⭐⭐⭐⭐ | 速 | ⭐⭐⭐⭐⭐ | リアルタイム、公式データ |

## 使用方法

### クイックスタート

```bash
# 1. 依存関係をインストール
pip install yfinance

# 2. マルチデータソース統合パイプラインを実行
./run_multi_source_pipeline.sh 7

# 3. データ品質を確認
./CHECK_PIPELINE_STATUS.sh
```

### 個別実行

```bash
# Yahoo Financeから取得
python3 jobs/download_yahoo_finance.py \
  --pair USDJPY \
  --start-date 2026-01-25 \
  --end-date 2026-02-01 \
  --interval 1h

# OANDAから取得（OANDA_API_KEY環境変数が必要）
export OANDA_API_KEY="your_api_key"
python3 jobs/download_oanda.py \
  --pair USDJPY \
  --start "2026-01-25T00:00:00" \
  --end "2026-02-01T00:00:00" \
  --granularity H1

# データをマージ
python3 jobs/merge_data_sources.py \
  --pair USDJPY \
  --start-date 2026-01-25 \
  --end-date 2026-02-01 \
  --priority dukascopy,yahoo,oanda
```

## データ保存場所

```
data/
├── raw_bi5/              # Dukascopy BI5ファイル（既存）
├── bars/                 # Dukascopy M1バー（既存）
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

## 次のステップ

1. **データ品質の検証**: 各ソースのデータを比較して品質を確認
2. **特徴量生成の拡張**: マージされたデータを使用して特徴量を生成する機能を追加
3. **自動データ取得**: 定期的に複数ソースからデータを取得するスクリプトを作成
4. **ADVFN対応**: 必要に応じてADVFNのスクレイピング機能を実装

## 参考リンク

- [Yahoo Finance (yfinance)](https://github.com/ranaroussi/yfinance)
- [OANDA API Documentation](https://developer.oanda.com/)
- [OANDA無料トライアル](https://www.oanda.com/foreign-exchange-data-services/en/exchange-rates-api/free-trial/)
- [jp.advfn.com FX Data Download](https://jp.advfn.com/fx/data-download)

## 注意事項

- **OANDA API**: 無料トライアルは7日間、1,000 quotesまで
- **Yahoo Finance**: 利用規約に注意（個人利用・研究目的）
- **データマージ**: 優先順位を適切に設定してデータ品質を確保
- **利用規約**: 各データソースの利用規約を確認して使用してください

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
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成：

```bash
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
TE_API_KEY=your_tradingeconomics_key  # オプション（guest:guestでも可）
```

### 3. ローカル実行

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

### 4. LINEボット起動

```bash
python app.py
```

## Renderデプロイ

1. GitHubリポジトリにpush
2. RenderでNew Web Serviceを作成
3. リポジトリを選択
4. 環境変数を設定（LINE_CHANNEL_ACCESS_TOKEN等）
5. Deploy

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

## 次のステップ

1. **モデル学習**: 特徴量を使って機械学習モデルを構築
2. **バックテスト**: walk-forward検証で性能評価
3. **自動取引**: 条件付きエントリー/エグジットの実装
4. **他通貨対応**: EURUSD, GBPUSD, AUDUSDなどの追加
5. **レポート生成**: 日次/週次レポートの自動生成

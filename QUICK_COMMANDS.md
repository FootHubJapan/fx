# クイックコマンド集

## 前提条件

1. **仮想環境をアクティベート**:
   ```bash
   source venv/bin/activate
   ```

2. **依存関係がインストールされていること**:
   ```bash
   pip install -r requirements.txt
   ```

## よく使うコマンド

### モデル学習

```bash
# 自動判定で学習（必要時のみ）
python3 jobs/auto_train_model.py --pair USDJPY

# 強制学習
python3 jobs/auto_train_model.py --pair USDJPY --force
```

### データ更新

```bash
# データ取得
python3 jobs/download_bi5.py --pair USDJPY --start 2025-01-01T00 --end 2025-01-02T00

# M1バー生成
python3 jobs/build_m1_from_bi5.py --pair USDJPY --start-date 2025-01-01 --end-date 2025-01-02

# 全時間足生成
python3 jobs/build_bars_from_m1.py --pair USDJPY

# 特徴量生成
python3 jobs/build_features.py --bars data/bars/USDJPY/tf=M5/all.parquet --out data/features/USDJPY/M5_features.parquet --events-cache data/events/events_cache.parquet
```

## 注意事項

- **Macでは `python3` を使用**（`python` ではなく）
- **コメント行（`#` で始まる行）は実行しない**
- **仮想環境をアクティベートしてから実行**

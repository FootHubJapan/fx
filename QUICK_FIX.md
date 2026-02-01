# クイック修正ガイド

## 現在の状況

ネットワーク接続の問題により、新しいパッケージのインストールができません。

## 解決方法

### オプション1: ネットワーク接続を確認

```bash
# インターネット接続を確認
ping -c 3 8.8.8.8

# DNS解決を確認
nslookup pypi.org
```

### オプション2: 既存のパッケージで動作確認

以前にインストールしたパッケージが残っている可能性があります：

```bash
cd "/Users/isomurayuuki/fx agent"
source venv/bin/activate

# インストール済みパッケージを確認
pip list

# 不足しているパッケージのみ個別にインストール（ネットワーク接続が復旧したら）
pip install pandas numpy requests flask line-bot-sdk --no-cache-dir
```

### オプション3: 既存のデータで特徴量生成を試す

既にM1バーが生成されているので、それを使って特徴量生成を試せます：

```bash
cd "/Users/isomurayuuki/fx agent"
source venv/bin/activate

# 既存のM1バーからM5バーを生成（build_bars_from_m1.pyを使用）
python3 jobs/build_bars_from_m1.py --pair USDJPY

# 特徴量生成（既存のデータを使用）
python3 jobs/build_features.py --pair USDJPY --timeframe M5
```

## 現在利用可能なデータ

- ✅ M1バー: `data/bars/USDJPY/tf=M1/` (7,184バー)
- ✅ マージデータ: `data/merged/USDJPY/USDJPY_merged_2026-01-25_2026-02-01.parquet`

## 次のステップ

1. **ネットワーク接続を復旧**
2. **依存関係をインストール**: `pip install -r requirements.txt`
3. **特徴量生成を実行**: `python3 jobs/build_features.py --pair USDJPY --timeframe M5`
4. **LINE Botでテスト**: 「分析」または「予測」コマンド

# build_m1_from_bi5.py エラー修正ガイド

## 問題

`build_m1_from_bi5.py`を実行すると、セグメンテーションフォルト（exit code 139）が発生します。

## エラー内容

```
ValueError: invalid literal for int() with base 10: 'USDJPY'
```

その後、修正しましたが、セグメンテーションフォルトが発生しています。

## 修正内容

### 1. パス解析の修正

ファイルパス構造: `data/raw_bi5/USDJPY/2026/00/27/10h_ticks.bi5`

```python
# 修正前
year = int(parts[-5])  # 'USDJPY' になってエラー

# 修正後
year = int(parts[-4])  # '2026' が正しい
month0 = int(parts[-3])  # '00' が正しい
day = int(parts[-2])  # '27' が正しい
```

### 2. エラーハンドリングの改善

`lzma.open`のコンテキストマネージャーを使用し、エラーハンドリングを追加しました。

## 一時的な回避策

DukascopyのBI5処理に問題がある場合、Yahoo Financeのデータを使用できます：

```bash
# Yahoo Financeからデータを取得
python3 jobs/download_yahoo_finance.py \
  --pair USDJPY \
  --start-date 2026-01-25 \
  --end-date 2026-02-01 \
  --interval 1h

# その後、Yahoo Financeのデータから直接特徴量を生成
# （build_bars_from_m1.pyをスキップ）
```

## 次のステップ

1. **セグメンテーションフォルトの原因を特定**
   - `lzma`モジュールの問題か確認
   - メモリ不足の可能性を確認
   - pandas/numpyのバージョン互換性を確認

2. **代替データソースを使用**
   - Yahoo Financeからデータを取得
   - OANDAからデータを取得（APIキーが必要）

3. **データマージ機能を使用**
   - 複数のデータソースを統合
   - `jobs/merge_data_sources.py`を使用

## デバッグ方法

```bash
# 1. ファイルが正常に読み込めるか確認
python3 -c "import lzma; from pathlib import Path; p = Path('data/raw_bi5/USDJPY/2026/00/27/10h_ticks.bi5'); f = lzma.open(p, 'rb'); buf = f.read(); print(f'File size: {len(buf)} bytes'); f.close()"

# 2. パス解析を確認
python3 -c "from pathlib import Path; p = Path('data/raw_bi5/USDJPY/2026/00/27/10h_ticks.bi5'); print('Parts:', p.parts); print('Year:', p.parts[-4]); print('Month:', p.parts[-3]); print('Day:', p.parts[-2])"

# 3. メモリ使用量を確認
python3 -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

## 参考

- `MULTI_SOURCE_DATA.md` - マルチデータソース統合ガイド
- `jobs/download_yahoo_finance.py` - Yahoo Financeデータ取得
- `jobs/download_oanda.py` - OANDAデータ取得

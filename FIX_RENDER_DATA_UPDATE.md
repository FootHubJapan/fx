# Render環境でのデータ更新問題の修正

## 問題

Render環境でLINE Botの「データ更新」コマンドを実行すると、「No M1 parquet files found」エラーが発生していました。

## 原因

1. Render環境には初期データファイルが存在しない（`.gitignore`で除外されている）
2. `update_data()`関数はDukascopyのBI5ファイルからM1バーを生成することを前提としていた
3. BI5ダウンロードやM1生成が失敗すると、後続の処理が全て失敗する

## 修正内容

### 1. `app.py`の`update_data()`関数を改善

- **複数データソース対応**: Yahoo Financeを優先的に使用（最も確実で簡単）
- **エラーハンドリング改善**: 一部の処理が失敗しても続行
- **Yahoo Financeデータの変換**: `data/yahoo_finance/`から`data/bars/`に自動変換

### 2. `build_features.py`の改善

- **Yahoo Financeデータのフォールバック**: H1時間足の場合、Yahoo Financeデータを直接使用可能

## 動作フロー

1. **Yahoo Financeからデータ取得**（優先）
   - 過去7日分の1hデータを取得
   - `data/yahoo_finance/USDJPY/1h.parquet`に保存

2. **バーデータの変換**
   - Yahoo Financeデータを`data/bars/USDJPY/tf=H1/all.parquet`にコピー
   - `build_features.py`が読み込める形式に変換

3. **Dukascopyデータ取得**（オプション）
   - 成功した場合のみM1バーを生成
   - 失敗しても続行

4. **特徴量生成**
   - 利用可能なデータから特徴量を生成

## 使用方法

LINE Botで「データ更新」コマンドを送信するだけです：

```
データ更新
```

処理が完了すると、以下のようなメッセージが返ってきます：

```
✅ Yahoo Financeデータ取得完了
✅ H1バーデータを準備完了
✅ イベントデータ取得完了
✅ 特徴量生成完了

✅ データ更新完了！「分析」コマンドを試してください。
```

## トラブルシューティング

### まだエラーが発生する場合

1. **Renderのログを確認**
   - Render Dashboard → Logsタブでエラー内容を確認

2. **タイムアウトエラー**
   - データ取得に時間がかかる場合、タイムアウトが発生する可能性があります
   - 数分待ってから再度「データ更新」を試してください

3. **ネットワークエラー**
   - Yahoo Finance APIへの接続が失敗する場合があります
   - しばらく待ってから再試行してください

## 次のステップ

データ更新が完了したら：

1. ✅ LINE Botで「分析」コマンドをテスト
2. ✅ LINE Botで「予測」コマンドをテスト

問題が続く場合は、`DEPLOY_CHECKLIST.md`を参照してください。

# 緊急デプロイ手順

## 現在の状況

Renderにデプロイされていますが、最新の修正が反映されていません。「データ更新」コマンドで「No M1 parquet files found」エラーが発生しています。

## 即座に実行すべき手順

### ステップ1: 最新のコードをGitHubにpush

```bash
cd "/Users/isomurayuuki/fx agent"
git add .
git commit -m "fix: Use H1 timeframe for Yahoo Finance data and improve feature file detection"
git push origin main
```

### ステップ2: Renderで再デプロイ

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. `fx-analysis-line-bot` サービスを選択
3. **Manual Deploy** → **Deploy latest commit** をクリック
4. デプロイが完了するまで待つ（2-3分）

### ステップ3: LINE Botでテスト

デプロイが完了したら：

1. LINE Botで「データ更新」と送信
2. 処理が完了するまで待つ（数分かかる場合があります）
3. 「分析」コマンドを試す

## 修正内容

1. **`app.py`**: Yahoo Financeデータ（H1）を使用してH1特徴量を生成するように変更
2. **`fx_ai_agent.py`**: H1特徴量ファイルを優先的に探すように変更（M5が無い場合のフォールバック）

## トラブルシューティング

### まだエラーが発生する場合

1. **Renderのログを確認**:
   - Render Dashboard → Logsタブ
   - エラーメッセージを確認

2. **デプロイが完了しているか確認**:
   - Render Dashboard → Eventsタブ
   - 最新のデプロイが成功しているか確認

3. **コードが最新か確認**:
   ```bash
   git log --oneline -5
   ```
   - 最新のコミットが含まれているか確認

## 期待される動作

デプロイ後、「データ更新」コマンドを実行すると：

1. ✅ Yahoo FinanceからH1データを取得
2. ✅ H1バーデータを準備
3. ✅ H1特徴量を生成
4. ✅ 「分析」コマンドが動作する

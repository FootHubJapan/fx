# Renderデプロイチェックリスト

## ✅ デプロイ前の確認事項

### 1. コードの準備
- [ ] すべての変更をコミット
- [ ] GitHubにpush済み
- [ ] `render.yaml`が正しく設定されている

### 2. 環境変数の設定
Render Dashboardの **Environment** タブで以下を設定：

- [ ] `LINE_CHANNEL_ACCESS_TOKEN` - LINE Developersから取得
- [ ] `LINE_CHANNEL_SECRET` - LINE Developersから取得
- [ ] `TE_API_KEY` - TradingEconomics APIキー（`guest:guest`でも可）
- [ ] `NATIVE_AI_URL` - 外部AIを使用する場合（オプション）
- [ ] `NATIVE_AI_API_KEY` - 外部AIのAPIキー（オプション）

### 3. LINE Developers設定
- [ ] Webhook URLが正しく設定されている（`https://your-app.onrender.com/callback`）
- [ ] Webhookが有効化されている
- [ ] Channel Access Tokenが発行されている

## 🚀 デプロイ手順

### ステップ1: GitHubにpush

```bash
cd "/Users/isomurayuuki/fx agent"
git add .
git commit -m "feat: Fix feature file path resolution and improve error messages"
git push origin main
```

### ステップ2: Renderでデプロイ

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. あなたのWebサービス（`fx-analysis-line-bot`）を選択
3. **Manual Deploy** → **Deploy latest commit** をクリック
4. デプロイが完了するまで待つ（数分）

### ステップ3: 動作確認

1. **ヘルスチェック**:
   ```bash
   curl https://your-app.onrender.com/health
   ```
   → `{"status":"ok",...}` が返れば成功

2. **LINE Botでテスト**:
   - 「ヘルプ」と送信 → コマンド一覧が表示される
   - 「分析」と送信 → データが無い場合は適切なメッセージが表示される
   - 「データ更新」と送信 → データパイプラインが実行される

## ⚠️ データファイルについて

**重要**: `data/`ディレクトリは`.gitignore`に含まれているため、GitHubにpushされません。

### 解決策

#### オプションA: LINE Botで「データ更新」コマンドを実行（推奨）

1. LINE Botで「データ更新」と送信
2. データパイプラインが実行され、特徴量ファイルが生成される
3. その後、「分析」コマンドが動作する

**注意**: Renderの無料プランでは、スリープ後にデータが失われる可能性があります。

#### オプションB: Render起動時にデータを生成

`start_render.sh`スクリプトを使用して、起動時に自動的にデータを生成できます。

**設定方法**:
1. `render.yaml`の`startCommand`を以下に変更：
   ```yaml
   startCommand: bash start_render.sh
   ```
2. GitHubにpushして再デプロイ

**注意**: 初回起動に数分かかる可能性があります。

#### オプションC: 外部ストレージを使用

Google Drive、S3、またはGitHub Releasesにデータを保存し、起動時にダウンロードする方法もあります。

詳細は `RENDER_DEPLOY_DATA.md` を参照してください。

## 🔍 トラブルシューティング

### 問題1: 「特徴量ファイルが見つかりません」エラー

**原因**: Render環境にデータファイルが存在しない

**解決策**:
1. LINE Botで「データ更新」コマンドを実行
2. または、`start_render.sh`を使用して起動時にデータを生成

### 問題2: Webhookが404エラーを返す

**原因**: Webhook URLが正しく設定されていない

**解決策**:
1. LINE Developers ConsoleでWebhook URLを確認
2. `https://your-app.onrender.com/callback` の形式になっているか確認
3. 末尾に `/callback` が付いているか確認

### 問題3: 503 Service Unavailable

**原因**: LINE_CHANNEL_ACCESS_TOKEN または LINE_CHANNEL_SECRET が設定されていない

**解決策**:
1. Render Dashboardの **Environment** タブで環境変数を確認
2. LINE Developers Consoleから正しい値をコピー

### 問題4: デプロイが失敗する

**原因**: 依存関係のインストールエラー、またはビルドエラー

**解決策**:
1. Render Dashboardの **Logs** タブでエラーを確認
2. `requirements.txt`のパッケージ名・バージョンを確認
3. Pythonバージョンが3.11.0になっているか確認（`runtime.txt`）

## 📝 次のステップ

デプロイが完了したら：

1. ✅ LINE Botで「ヘルプ」コマンドをテスト
2. ✅ LINE Botで「データ更新」コマンドを実行
3. ✅ LINE Botで「分析」コマンドをテスト
4. ✅ LINE Botで「予測」コマンドをテスト

問題が発生した場合は、`RENDER_DEPLOY_DATA.md` または `TROUBLESHOOTING_503.md` を参照してください。

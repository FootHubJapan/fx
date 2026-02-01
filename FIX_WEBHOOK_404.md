# Webhook 404エラー解決ガイド

## 問題

LINE Developers Consoleで「404 Not Found」エラーが発生しています。

**原因**: Webhook URLがプレースホルダー（`https://your-app.onrender.com/callback`）のままになっています。

## 解決方法

### ステップ1: Renderの実際のURLを確認

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. あなたのWebサービス（`fx-analysis-line-bot`など）を選択
3. 上部に表示されているURLを確認
   - 例: `https://fx-orm5.onrender.com`
   - または: `https://your-service-name.onrender.com`

### ステップ2: LINE Developers ConsoleでWebhook URLを更新

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. チャネル（Molt bot+）を選択
3. **Messaging API** タブを開く
4. **Webhook URL** の **編集** ボタンをクリック
5. 実際のRender URLを入力：
   ```
   https://your-actual-render-url.onrender.com/callback
   ```
   **重要**: 末尾に `/callback` を必ず付けてください
6. **更新** をクリック

### ステップ3: Webhook検証

1. **検証** ボタンをクリック
2. ✅ **200 OK** が返れば成功
3. ❌ **404 Not Found** が続く場合：
   - Renderにデプロイされているか確認
   - Renderのログでエラーがないか確認
   - `/callback` エンドポイントが正しく実装されているか確認

### ステップ4: Renderのデプロイ確認

Render Dashboardで以下を確認：

1. **Logs** タブでエラーがないか確認
2. **Events** タブでデプロイが成功しているか確認
3. **ヘルスチェック**: `https://your-actual-render-url.onrender.com/health` にアクセス
   - ✅ `{"status": "ok", ...}` が返れば正常

## よくある間違い

### ❌ 間違い
```
https://your-app.onrender.com/callback  # プレースホルダーのまま
https://your-app.onrender.com/          # /callbackが抜けている
```

### ✅ 正しい
```
https://fx-orm5.onrender.com/callback   # 実際のRender URL + /callback
```

## 確認チェックリスト

- [ ] Renderにデプロイされている
- [ ] RenderのURLを確認した
- [ ] LINE DevelopersでWebhook URLを実際のRender URLに更新した
- [ ] Webhook URLの末尾に `/callback` が付いている
- [ ] Webhook検証で200 OKが返る
- [ ] Renderのログにエラーがない

## 次のステップ

Webhook URLを正しく設定したら：

1. LINEアプリでボットに「ヘルプ」と送信
2. 応答があれば成功！
3. 「分析」や「予測」コマンドを試す

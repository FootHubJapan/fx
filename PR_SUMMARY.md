# PR: Renderデプロイ対応

## 目的
Renderにデプロイして `/health` が200を返すことを確実にする

## 変更内容

### 1. `/health` エンドポイントの改善
- **ファイル**: `app.py`
- **変更**: 明示的に200ステータスコードを返すように修正
- **理由**: Renderのヘルスチェックで確実に200を返すため

```python
# 変更前
return {"status": "ok", "timestamp": ...}

# 変更後
return jsonify({
    "status": "ok",
    "timestamp": ...
}), 200
```

### 2. Render設定の最適化
- **ファイル**: `render.yaml`
- **変更**: `healthCheckPath: /health` を追加
- **理由**: Renderが自動でヘルスチェックを行うように設定

### 3. 環境変数テンプレートの簡素化
- **ファイル**: `.env.example`
- **変更**: 冗長なコメントを削除し、必要最小限のキーだけ列挙
- **理由**: シンプルで分かりやすく、秘密情報を含まない

### 4. READMEの更新
- **ファイル**: `README.md`
- **変更**:
  - Render設定方針を明記
  - ローカル起動手順を追加
  - Renderデプロイ手順を詳細化
  - 環境変数一覧を表形式で追加
  - ヘルスチェックURLを明記

## 動作確認

### ローカル
```bash
python app.py
curl http://localhost:5000/health
# → 200 OK, {"status": "ok", "timestamp": "..."}
```

### Render
1. GitHubにpush
2. Renderで `render.yaml` を適用
3. 環境変数を設定（LINE Botを使う場合のみ）
4. `https://your-app.onrender.com/health` にアクセス
5. → 200 OK を確認

## 完了条件チェック

- ✅ ローカルで起動し `/health` が200を返す
- ✅ Renderの設定方針がREADMEに明記
- ✅ 余計な秘密情報はコミットしない（.env.exampleはプレースホルダーのみ）

## 次のステップ

1. このブランチをGitHubにpush
2. GitHub上でPRを作成
3. レビュー後、mainにマージ
4. Renderでデプロイして動作確認

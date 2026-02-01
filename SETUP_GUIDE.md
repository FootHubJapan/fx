# セットアップガイド

## 前提条件

- Python 3.11以上
- インターネット接続（依存関係のインストールに必要）

## セットアップ手順

### 1. 仮想環境の作成

```bash
cd "/Users/isomurayuuki/fx agent"
python3 -m venv venv
```

### 2. 仮想環境のアクティベート

```bash
source venv/bin/activate
```

**確認**: プロンプトに `(venv)` が表示されればOK

### 3. 依存関係のインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**注意**: インターネット接続が必要です。エラーが出る場合は：
- インターネット接続を確認
- プロキシ設定を確認
- ファイアウォール設定を確認

### 4. インストール確認

```bash
python3 -c "import pandas; import lightgbm; print('OK')"
```

エラーが出ない場合はインストール成功です。

## トラブルシューティング

### エラー: "ModuleNotFoundError: No module named 'pandas'"

**原因**: 依存関係がインストールされていない

**解決方法**:
1. 仮想環境がアクティベートされているか確認（プロンプトに `(venv)` が表示されているか）
2. 依存関係をインストール:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### エラー: "Could not find a version that satisfies the requirement"

**原因**: インターネット接続の問題

**解決方法**:
1. インターネット接続を確認
2. DNS設定を確認
3. プロキシ設定を確認（会社のネットワークなど）

### エラー: "nodename nor servname provided, or not known"

**原因**: DNS解決の問題

**解決方法**:
1. インターネット接続を確認
2. DNS設定を確認:
   ```bash
   ping google.com
   ```
3. ネットワーク設定を確認

### 仮想環境がアクティベートされない

**確認方法**:
```bash
which python3
```

仮想環境内のPythonが使われているか確認:
```bash
# 仮想環境内の場合
/Users/isomurayuuki/fx agent/venv/bin/python3

# システムのPythonの場合
/usr/bin/python3
```

**解決方法**:
```bash
source venv/bin/activate
which python3  # 再度確認
```

## 次のステップ

依存関係のインストールが完了したら：

1. **データ更新**:
   ```bash
   python3 jobs/download_bi5.py --pair USDJPY --start 2025-01-01T00 --end 2025-01-02T00
   ```

2. **モデル学習**:
   ```bash
   python3 jobs/auto_train_model.py --pair USDJPY
   ```

3. **アプリケーション起動**:
   ```bash
   python3 app.py
   ```

## よくある質問

### Q: 仮想環境を毎回アクティベートする必要がありますか？

**A: はい、必要です。**

新しいターミナルを開くたびに：
```bash
cd "/Users/isomurayuuki/fx agent"
source venv/bin/activate
```

### Q: 仮想環境を無効化するには？

**A: `deactivate` コマンドを使用**:
```bash
deactivate
```

### Q: 仮想環境を削除して作り直すには？

**A: 以下のコマンドで再作成**:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# インストールトラブルシューティング

## 現在のエラー

```
ERROR: Could not find a version that satisfies the requirement flask==3.0.0
ERROR: No matching distribution found for flask==3.0.0
```

または

```
nodename nor servname provided, or not known
```

## 原因

**DNS解決の問題**または**インターネット接続の問題**です。

## 解決手順

### 1. インターネット接続を確認

ターミナルで以下を実行：

```bash
ping google.com
```

**接続できる場合**: 手順2に進む
**接続できない場合**: ネットワーク設定を確認してください

### 2. DNS設定を確認

```bash
# DNS設定を確認
cat /etc/resolv.conf

# または
scutil --dns
```

### 3. 依存関係を個別にインストール（推奨）

ネットワーク接続が不安定な場合、パッケージを個別にインストール：

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# コアパッケージから順番にインストール
pip install pandas==2.1.4
pip install numpy==1.26.2
pip install flask==3.0.0
pip install line-bot-sdk==3.5.0
pip install pyarrow==14.0.2
pip install requests==2.31.0
pip install feedparser==6.0.10
pip install python-dotenv==1.0.0
pip install gunicorn==21.2.0
pip install lightgbm==4.5.0
pip install scikit-learn==1.4.2
```

### 4. 代替方法: バージョン指定を緩和

`requirements.txt` のバージョン指定を緩和：

```bash
# requirements.txt を一時的に編集
# 例: flask==3.0.0 → flask>=3.0.0
```

または、最新版をインストール：

```bash
pip install pandas numpy flask line-bot-sdk pyarrow requests feedparser python-dotenv gunicorn lightgbm scikit-learn
```

### 5. プロキシ設定（会社のネットワークなど）

プロキシを使用している場合：

```bash
# プロキシ設定
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# pipでプロキシを使用
pip install --proxy http://proxy.example.com:8080 -r requirements.txt
```

### 6. pipのキャッシュをクリア

```bash
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

### 7. ミラーサイトを使用（中国など）

```bash
# 中国のミラーサイトを使用
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

## 確認方法

インストールが完了したら確認：

```bash
python3 -c "import pandas; import lightgbm; import flask; print('OK')"
```

エラーが出ない場合は成功です。

## 次のステップ

依存関係のインストールが完了したら：

```bash
# モデル学習を試す
python3 jobs/auto_train_model.py --pair USDJPY
```

## それでも解決しない場合

1. **Pythonバージョンを確認**:
   ```bash
   python3 --version
   ```
   Python 3.11以上が必要です。

2. **仮想環境を再作成**:
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **システムのPythonを使用**（仮想環境を使わない）:
   ```bash
   # 仮想環境を無効化
   deactivate
   
   # システムのPythonでインストール（推奨しない）
   pip3 install -r requirements.txt
   ```

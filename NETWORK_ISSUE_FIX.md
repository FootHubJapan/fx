# ネットワーク接続問題の解決方法

## 問題

仮想環境の再構築時に、ネットワーク接続エラーが発生しています：

```
Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known
```

## 解決方法

### 方法1: ネットワーク接続を確認

```bash
# インターネット接続を確認
ping -c 3 pypi.org

# DNS解決を確認
nslookup pypi.org
```

### 方法2: pipの設定を確認

```bash
# pipの設定を確認
pip config list

# プロキシ設定がある場合は削除（必要に応じて）
pip config unset global.proxy
```

### 方法3: 既存の仮想環境を使用

ネットワーク接続の問題が解決できない場合、既存の仮想環境を使用：

```bash
cd "/Users/isomurayuuki/fx agent"
source venv/bin/activate

# 既存のパッケージを確認
pip list | grep -E "(pandas|yfinance|flask)"

# 不足しているパッケージのみインストール
pip install yfinance --no-cache-dir
```

### 方法4: オフラインインストール

ネットワーク接続が不安定な場合、オフラインでパッケージをダウンロード：

```bash
# 別のマシンでパッケージをダウンロード
pip download -r requirements.txt -d ./packages

# オフラインでインストール
pip install --no-index --find-links ./packages -r requirements.txt
```

### 方法5: キャッシュの権限を修正

```bash
# pipキャッシュの権限を修正
sudo chown -R $(whoami) /Users/isomurayuuki/Library/Caches/pip
```

## 現在の状況

- 仮想環境は再作成されましたが、依存関係がインストールされていません
- ネットワーク接続の問題により、pip installが失敗しています

## 推奨アクション

1. **ネットワーク接続を確認**
   ```bash
   ping -c 3 pypi.org
   ```

2. **既存の仮想環境を確認**
   - 以前にインストールしたパッケージが残っているか確認

3. **段階的にインストール**
   ```bash
   cd "/Users/isomurayuuki/fx agent"
   source venv/bin/activate
   pip install pandas numpy --no-cache-dir
   pip install yfinance --no-cache-dir
   pip install flask line-bot-sdk --no-cache-dir
   ```

4. **ネットワーク設定を確認**
   - VPNやプロキシ設定を確認
   - ファイアウォール設定を確認

## 次のステップ

ネットワーク接続が復旧したら：

```bash
cd "/Users/isomurayuuki/fx agent"
source venv/bin/activate
pip install -r requirements.txt
```

その後、データパイプラインを実行：

```bash
./run_data_pipeline.sh 7
```

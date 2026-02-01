# インストール問題の解決方法

## 現在の状況

✅ **インストール済み**:
- pandas, numpy, flask, requests, feedparser, python-dotenv, pyarrow, gunicorn, scikit-learn

❌ **問題あり**:
- `line-bot-sdk`: インストールエラー（再インストール必要）
- `lightgbm`: libompライブラリが必要

## 解決手順

### 1. Homebrewの権限を修正

```bash
sudo chown -R $(whoami) /opt/homebrew/Cellar
sudo chown -R $(whoami) /Users/$(whoami)/Library/Caches/Homebrew
```

### 2. libompをインストール

```bash
brew install libomp
```

### 3. line-bot-sdkを再インストール

```bash
source venv/bin/activate
pip install --force-reinstall --no-deps line-bot-sdk==3.5.0
pip install aiohttp pydantic requests  # 依存関係を個別にインストール
```

または、エラーを無視してインストール：

```bash
pip install line-bot-sdk==3.5.0 --no-build-isolation
```

### 4. lightgbmの確認

libompインストール後：

```bash
python3 -c "import lightgbm; print('LightGBM OK')"
```

## 一時的な回避策

**LightGBMが使えない場合でも、FX分析AIエージェントは動作します**（ルールベース分析を使用）。

確認：

```bash
source venv/bin/activate
python3 -c "from fx_ai_agent import analyze_fx; print('FX AI Agent OK')"
```

## 完全な再インストール（推奨）

問題が解決しない場合：

```bash
# 仮想環境を削除
rm -rf venv

# libompをインストール（Homebrew権限修正後）
brew install libomp

# 仮想環境を再作成
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

## 確認コマンド

```bash
source venv/bin/activate

# コアパッケージ
python3 -c "import pandas, flask, requests; print('✓ Core OK')"

# LINE Bot SDK
python3 -c "from linebot import LineBotApi; print('✓ LINE Bot SDK OK')"

# LightGBM
python3 -c "import lightgbm; print('✓ LightGBM OK')"

# FX AI Agent
python3 -c "from fx_ai_agent import analyze_fx; print('✓ FX AI Agent OK')"
```

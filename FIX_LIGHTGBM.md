# LightGBM インストール問題の解決方法

## エラー内容

```
OSError: dlopen(...): Library not loaded: @rpath/libomp.dylib
```

LightGBMはOpenMPライブラリ（`libomp`）が必要です。

## 解決方法

### 方法1: Homebrewでlibompをインストール（推奨）

```bash
# Homebrewがインストールされているか確認
which brew

# libompをインストール
brew install libomp
```

### 方法2: Homebrewがインストールされていない場合

1. **Homebrewをインストール**:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **libompをインストール**:
   ```bash
   brew install libomp
   ```

### 方法3: 仮想環境を再作成（libompインストール後）

```bash
# 仮想環境を削除
rm -rf venv

# 仮想環境を再作成
python3 -m venv venv
source venv/bin/activate

# 依存関係を再インストール
pip install -r requirements.txt
```

## 確認方法

```bash
source venv/bin/activate
python3 -c "import lightgbm; print('LightGBM OK')"
```

エラーが出なければ成功です。

## line-bot-sdk のエラーについて

`aenum` パッケージの構文エラーは無視して問題ありません。実際には `line-bot-sdk` はインストールされています。

確認：
```bash
python3 -c "import linebot; print('line-bot-sdk OK')"
```

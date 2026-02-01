# 自動モデル学習機能

FX分析AIエージェントのモデルを自動的に学習・更新する機能です。

## 機能概要

- **自動再学習判定**: 新しいデータが追加されたら自動的にモデルを再学習
- **定期学習**: 一定期間（デフォルト7日）経過したら自動的に再学習
- **LINE Botコマンド**: LINE Botから「モデル学習」コマンドで手動実行可能

## 使い方

### 1. LINE Botから実行

```
モデル学習
```

または

```
train_model
```

### 2. コマンドラインから実行

**重要**: Macでは `python3` を使用してください。

```bash
# 仮想環境をアクティベート（推奨）
source venv/bin/activate

# 自動判定で学習（必要時のみ）
python3 jobs/auto_train_model.py --pair USDJPY

# 強制学習（判定をスキップ）
python3 jobs/auto_train_model.py --pair USDJPY --force

# 再学習判定の最小日数を変更（デフォルト: 7日）
python3 jobs/auto_train_model.py --pair USDJPY --min-days 3
```

**注意**: コメント行（`#` で始まる行）は実行しないでください。コマンドのみをコピー&ペーストしてください。

### 3. 定期自動実行（Mac: launchd）

`~/Library/LaunchAgents/com.fx.auto_train.plist` を作成：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fx.auto_train</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/fx-agent/jobs/auto_train_model.py</string>
        <string>--pair</string>
        <string>USDJPY</string>
    </array>
    <key>StartInterval</key>
    <integer>604800</integer>  <!-- 7日 = 604800秒 -->
    <key>StandardOutPath</key>
    <string>/path/to/fx-agent/logs/auto_train.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/fx-agent/logs/auto_train_error.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

ロード：

```bash
launchctl load ~/Library/LaunchAgents/com.fx.auto_train.plist
```

## 再学習判定ロジック

以下の条件のいずれかを満たす場合、モデルを再学習します：

1. **モデルファイルが存在しない** → 初回学習
2. **特徴量ファイルがモデルより新しい** → 新しいデータが追加された
3. **前回学習から一定期間（デフォルト7日）経過** → 定期更新

## 注意事項

- **データ量**: 最低1000行のデータが必要です
- **実行時間**: データ量によっては30分以上かかる場合があります
- **LINE Bot実行**: LINE Botから実行する場合、タイムアウト（30分）に注意してください
- **バックグラウンド実行**: 長時間かかる場合は、コマンドラインやcron/launchdで実行することを推奨します

## 環境変数（オプション）

`.env` ファイルに以下を追加可能（将来実装予定）：

```bash
# 自動学習設定
AUTO_TRAIN_ENABLED=true
AUTO_TRAIN_MIN_DAYS=7
AUTO_TRAIN_PAIR=USDJPY
```

## トラブルシューティング

### エラー: "Features file not found"

特徴量データが生成されていません。まず以下を実行：

```bash
python jobs/build_features.py --bars data/bars/USDJPY/tf=M5/all.parquet --out data/features/USDJPY/M5_features.parquet --events-cache data/events/events_cache.parquet
```

### エラー: "Insufficient data"

データが1000行未満です。データ更新を実行：

```bash
# LINE Botから「データ更新」コマンドを実行
# または
python jobs/download_bi5.py --pair USDJPY --start 2024-01-01T00 --end 2025-02-01T00
python jobs/build_m1_from_bi5.py --pair USDJPY --start-date 2024-01-01 --end-date 2025-02-01
python jobs/build_bars_from_m1.py --pair USDJPY
python jobs/build_features.py ...
```

### タイムアウト

LINE Botから実行する場合、30分でタイムアウトします。大量データの場合は、コマンドラインから実行してください。

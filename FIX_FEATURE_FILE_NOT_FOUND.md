# 特徴量ファイルが見つからない問題の修正

## 問題

LINE Botで「分析」コマンドを実行すると、「特徴量ファイルが見つかりません。まずデータ更新を実行してください。」というエラーが表示されていました。

## 原因

1. `app.py`の`analyze`コマンドが`analyze_usdjpy()`を呼び出していましたが、この関数は相対パスでファイルを探していました
2. `fx_ai_agent.py`の`analyze_fx()`関数も相対パスを使用していたため、実行時の作業ディレクトリがプロジェクトルートでない場合、ファイルが見つかりませんでした

## 修正内容

### 1. `app.py`の`analyze_usdjpy()`関数を修正

- `analyze_usdjpy()`を`analyze_fx()`を使うように変更
- フォールバック時も絶対パスを使用するように修正

```python
def analyze_usdjpy() -> str:
    """USDJPY分析を実行して結果を返す（FX AIエージェントを使用）"""
    if FX_AI_AGENT_AVAILABLE:
        # FX AIエージェントを使用（高精度分析）
        return analyze_fx("現在の相場状況を分析してください", pair="USDJPY")
    else:
        # フォールバック: 簡易分析
        # プロジェクトルートからの絶対パスを使用
        project_root = Path(__file__).parent
        features_path = project_root / "data/features/USDJPY/M5_features.parquet"
        ...
```

### 2. `fx_ai_agent.py`の`analyze_fx()`関数を修正

- 相対パスから絶対パスに変更
- `__file__`を使用してプロジェクトルートを取得

```python
# 特徴量データを読み込む（プロジェクトルートからの絶対パスを使用）
try:
    project_root = Path(__file__).parent
except NameError:
    # __file__が定義されていない場合（例: インタラクティブシェル）
    project_root = Path.cwd()

features_path = project_root / f"data/features/{pair_normalized}/M5_features.parquet"
```

## 動作確認

1. アプリを再起動してください：
   ```bash
   ./restart_app.sh
   ```

2. LINE Botで「分析」コマンドを送信してください

3. 正常に動作する場合、以下のような分析結果が返ってきます：
   ```
   💹 USDJPY 予測
   
   方向: 買い/売り/様子見
   信頼度: XX%
   現在価格: XXX.XX
   
   📊 主要指標
   RSI(14): XX.XX
   ATR(14): X.XXXX
   MA(20): XXX.XX
   
   📈 イベント（24時間）
   マクロ: X件
   ニュース: X件
   ```

## トラブルシューティング

### まだエラーが表示される場合

1. **特徴量ファイルが存在するか確認**:
   ```bash
   ls -la data/features/USDJPY/M5_features.parquet
   ```

2. **ファイルが存在しない場合、データパイプラインを実行**:
   ```bash
   ./run_data_pipeline.sh 7
   ```

3. **アプリのログを確認**:
   - ローカル: ターミナルの出力を確認
   - Render: Render DashboardのLogsタブを確認

4. **パスが正しいか確認**:
   ```bash
   python3 -c "from pathlib import Path; print(Path('fx_ai_agent.py').resolve().parent)"
   ```

## 次のステップ

修正が完了したら、LINE Botで以下を試してください：

- 「分析」: 現在の相場状況を分析
- 「予測」: 高精度予測を取得
- 「データ更新」: 最新データを取得
- 「ヘルプ」: 利用可能なコマンドを表示

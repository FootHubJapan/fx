# アーキテクチャ設計：分析特化型AIエージェント

## 設計思想

このプロジェクトは**「分析特化型AIエージェント」**として設計されています。

- **現在**: FX分析に特化
- **将来**: サッカー勝敗分析など、他の分析タスクにも拡張可能

## 現在の実装（FX分析）

### データフロー

```
Dukascopy → Tickデータ → M1バー → 全時間足 → 特徴量生成
                                                      ↓
TradingEconomics/RSS → イベントデータ ────────────→ 特徴量生成
                                                      ↓
                                            FX分析AIエージェント
                                                      ↓
                                            LINE Bot → ユーザー
```

### コンポーネント

1. **データ収集層**
   - `jobs/download_bi5.py`: Dukascopyからティックデータ取得
   - `jobs/fetch_macro_events.py`: 経済指標取得
   - `jobs/fetch_rss_events.py`: 要人発言取得

2. **データ処理層**
   - `jobs/build_m1_from_bi5.py`: M1バー生成
   - `jobs/build_bars_from_m1.py`: 全時間足生成
   - `jobs/build_features.py`: 特徴量生成（テクニカル＋ファンダ）

3. **AI推論層**
   - `fx_ai_agent.py`: FX分析AIエージェント（高精度分析）
   - `jobs/train_fx_model.py`: モデル学習スクリプト

4. **インターフェース層**
   - `app.py`: LINE Bot Webhook + コマンド処理

## 将来の拡張（サッカー分析対応）

### 設計方針

**データソースを抽象化**して、FX分析とサッカー分析を同じフレームワークで扱えるようにします。

### 拡張アーキテクチャ

```
抽象化レイヤー
├─ DataSource (インターフェース)
│   ├─ FXDataSource (Dukascopy)
│   └─ SoccerDataSource (API/スクレイピング)
│
├─ FeatureBuilder (インターフェース)
│   ├─ FXFeatureBuilder (テクニカル＋ファンダ)
│   └─ SoccerFeatureBuilder (チーム統計＋選手データ)
│
└─ AnalysisAgent (インターフェース)
    ├─ FXAnalysisAgent (現在の実装)
    └─ SoccerAnalysisAgent (将来実装)
```

### 実装例（将来）

```python
# 抽象化された分析エージェント
class AnalysisAgent(ABC):
    @abstractmethod
    def analyze(self, features_df: pd.DataFrame, **kwargs) -> Dict:
        pass

# FX分析エージェント（現在）
class FXAnalysisAgent(AnalysisAgent):
    def analyze(self, features_df: pd.DataFrame, pair: str = "USDJPY") -> Dict:
        # 現在の実装
        pass

# サッカー分析エージェント（将来）
class SoccerAnalysisAgent(AnalysisAgent):
    def analyze(self, features_df: pd.DataFrame, match_id: str = None) -> Dict:
        # サッカー分析ロジック
        # 特徴量: チーム統計、選手データ、過去対戦成績など
        # 出力: 勝敗予測、スコア予測、主要要因
        pass
```

## 高精度分析モデル

### 現在の実装

- **モデル**: LightGBM（勾配ブースティング）
- **予測タスク**: 3クラス分類（買い/売り/様子見）
- **特徴量**: テクニカル指標 + ファンダメンタル + イベント特徴量

### モデル学習

```bash
# モデル学習
python jobs/train_fx_model.py \
  --features data/features/USDJPY/M5_features.parquet \
  --output models/fx_usdjpy_model.pkl \
  --train-start 2020-01-01 \
  --train-end 2024-12-31 \
  --forward-bars 60
```

### 予測精度向上のポイント

1. **特徴量エンジニアリング**
   - マルチ時間足特徴量（M5/H1/D1）
   - イベント特徴量（サプライズ・重要度）
   - 時間帯特徴量（セッション）

2. **モデル最適化**
   - ハイパーパラメータチューニング
   - 特徴量選択
   - アンサンブル

3. **検証方法**
   - Walk-forward検証（時系列分割）
   - リーク防止
   - 実運用シミュレーション

## サッカー分析への拡張（将来実装）

### 必要なデータソース

1. **試合データ**
   - 過去の試合結果
   - スコア、得点者、カード
   - 試合統計（シュート、パス成功率など）

2. **チームデータ**
   - チーム統計（勝率、得失点差など）
   - ホーム/アウェイ成績
   - 直近の調子

3. **選手データ**
   - 選手統計（得点、アシストなど）
   - 怪我・出場停止情報
   - フォーメーション

### 特徴量設計（サッカー）

```python
# サッカー特徴量の例
features = {
    # チーム統計
    'home_win_rate': 0.65,
    'away_win_rate': 0.45,
    'home_goals_avg': 1.8,
    'away_goals_avg': 1.2,
    
    # 直近の調子
    'home_form_last_5': [1, 1, 0, 1, 1],  # 1=勝, 0=負
    'away_form_last_5': [0, 1, 1, 0, 1],
    
    # 対戦成績
    'h2h_home_wins': 3,
    'h2h_draws': 2,
    'h2h_away_wins': 1,
    
    # イベント
    'home_key_player_injured': 0,  # 0=なし, 1=あり
    'away_key_player_injured': 1,
}
```

### 実装計画

1. **Phase 1**: FX分析の高精度化（現在）
2. **Phase 2**: データソース抽象化レイヤー実装
3. **Phase 3**: サッカーデータソース実装
4. **Phase 4**: サッカー分析エージェント実装
5. **Phase 5**: マルチタスク対応（FX + サッカー）

## 現在の実装状況

- ✅ FXデータ収集パイプライン
- ✅ 特徴量生成（テクニカル＋ファンダ）
- ✅ FX分析AIエージェント（ルールベース + モデル対応）
- ✅ モデル学習スクリプト
- ⏳ モデル学習（データが必要）
- ⏳ サッカー分析対応（将来）

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FX分析特化型AIエージェント（高精度分析モデル）
将来的にサッカー分析などにも拡張可能な設計
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("[WARN] LightGBM not available. Install with: pip install lightgbm")


class FXAnalysisAgent:
    """
    FX分析特化型AIエージェント
    
    高精度な分析・予測を行う。将来的にサッカー分析などにも拡張可能。
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: 学習済みモデルのパス（.pkl）。Noneの場合は簡易ルールベース分析
        """
        self.model = None
        self.model_path = model_path
        self.feature_columns = None
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        elif model_path:
            print(f"[WARN] Model file not found: {model_path}. Using rule-based analysis.")
    
    def load_model(self, model_path: str):
        """学習済みモデルを読み込む"""
        if not LIGHTGBM_AVAILABLE:
            print("[WARN] LightGBM not available. Cannot load model.")
            return
        
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data.get('model')
                self.feature_columns = data.get('feature_columns')
            print(f"[INFO] Model loaded from {model_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            self.model = None
    
    def analyze(self, features_df: pd.DataFrame, pair: str = "USDJPY") -> Dict:
        """
        FX分析を実行して予測・判断を返す
        
        Args:
            features_df: 特徴量DataFrame（最新1行以上）
            pair: 通貨ペア
        
        Returns:
            {
                "direction": "buy" | "sell" | "hold",
                "confidence": 0.0-1.0,
                "prediction": "予測テキスト",
                "analysis": "詳細分析",
                "key_factors": ["要因1", "要因2", ...],
                "risk_level": "low" | "medium" | "high"
            }
        """
        if features_df.empty:
            return {
                "direction": "hold",
                "confidence": 0.0,
                "prediction": "データが不足しています",
                "analysis": "特徴量データが見つかりません",
                "key_factors": [],
                "risk_level": "high"
            }
        
        latest = features_df.iloc[-1].copy()
        
        # モデル推論（学習済みモデルがある場合）
        if self.model is not None and LIGHTGBM_AVAILABLE:
            return self._predict_with_model(latest, features_df)
        else:
            # ルールベース分析（高精度版）
            return self._analyze_with_rules(latest, features_df)
    
    def _predict_with_model(self, latest: pd.Series, features_df: pd.DataFrame) -> Dict:
        """学習済みモデルで予測"""
        try:
            # 特徴量を準備
            if self.feature_columns:
                X = latest[self.feature_columns].values.reshape(1, -1)
            else:
                # 数値特徴量のみ選択
                numeric_cols = latest.select_dtypes(include=[np.number]).index.tolist()
                X = latest[numeric_cols].fillna(0).values.reshape(1, -1)
            
            # 予測
            pred_proba = self.model.predict_proba(X)[0]
            pred_class = self.model.predict(X)[0]
            
            # クラス定義: 0=売り, 1=様子見, 2=買い
            direction_map = {0: "sell", 1: "hold", 2: "buy"}
            direction = direction_map.get(pred_class, "hold")
            confidence = float(max(pred_proba))
            
            # 詳細分析を生成
            analysis = self._generate_analysis(latest, features_df, direction, confidence)
            key_factors = self._extract_key_factors(latest, direction)
            risk_level = self._assess_risk(latest, features_df)
            
            return {
                "direction": direction,
                "confidence": confidence,
                "prediction": self._format_prediction(direction, confidence, latest),
                "analysis": analysis,
                "key_factors": key_factors,
                "risk_level": risk_level
            }
        except Exception as e:
            print(f"[ERROR] Model prediction failed: {e}")
            return self._analyze_with_rules(latest, features_df)
    
    def _analyze_with_rules(self, latest: pd.Series, features_df: pd.DataFrame) -> Dict:
        """高精度ルールベース分析（モデル未学習時）"""
        # テクニカル指標から判断
        rsi = latest.get('rsi_14', 50)
        atr = latest.get('atr_14', 0)
        ma_20 = latest.get('ma_20', latest.get('close', 0))
        close = latest.get('close', 0)
        
        # イベント要因
        macro_cnt_24h = latest.get('macro_cnt_24H', 0)
        macro_sent_24h = latest.get('macro_sent_24H', 0)
        news_cnt_24h = latest.get('news_cnt_24H', 0)
        
        # ボラティリティ
        vol_20 = latest.get('vol_20', 0)
        
        # 判断ロジック（高精度版）
        signals = []
        direction_score = 0.0
        
        # RSI判断
        if rsi < 30:
            signals.append("RSIが売られすぎ（30以下）→ 買いシグナル")
            direction_score += 0.3
        elif rsi > 70:
            signals.append("RSIが買われすぎ（70以上）→ 売りシグナル")
            direction_score -= 0.3
        
        # 移動平均判断
        if close > ma_20 * 1.01:
            signals.append("価格がMA20を1%以上上回る → 上昇トレンド")
            direction_score += 0.2
        elif close < ma_20 * 0.99:
            signals.append("価格がMA20を1%以上下回る → 下降トレンド")
            direction_score -= 0.2
        
        # ファンダメンタル判断
        if macro_sent_24h > 0.5:
            signals.append(f"マクロイベントが強気（サプライズ+{macro_sent_24h:.2f}）→ 買い要因")
            direction_score += 0.25
        elif macro_sent_24h < -0.5:
            signals.append(f"マクロイベントが弱気（サプライズ{macro_sent_24h:.2f}）→ 売り要因")
            direction_score -= 0.25
        
        # ボラティリティ判断
        if vol_20 > features_df['vol_20'].quantile(0.8) if len(features_df) > 20 else False:
            signals.append("ボラティリティが高水準 → リスク増大")
        
        # 方向決定
        if direction_score > 0.3:
            direction = "buy"
            confidence = min(0.7 + abs(direction_score) * 0.3, 0.95)
        elif direction_score < -0.3:
            direction = "sell"
            confidence = min(0.7 + abs(direction_score) * 0.3, 0.95)
        else:
            direction = "hold"
            confidence = 0.5
        
        # リスク評価
        risk_level = self._assess_risk(latest, features_df)
        
        # 分析テキスト生成
        analysis = self._generate_analysis(latest, features_df, direction, confidence)
        
        return {
            "direction": direction,
            "confidence": confidence,
            "prediction": self._format_prediction(direction, confidence, latest),
            "analysis": analysis,
            "key_factors": signals[:5],  # 上位5つ
            "risk_level": risk_level
        }
    
    def _generate_analysis(self, latest: pd.Series, features_df: pd.DataFrame, 
                          direction: str, confidence: float) -> str:
        """詳細分析テキストを生成"""
        rsi = latest.get('rsi_14', 50)
        atr = latest.get('atr_14', 0)
        close = latest.get('close', 0)
        macro_sent = latest.get('macro_sent_24H', 0)
        
        analysis_parts = []
        
        # 現在の市場状況
        if rsi < 40:
            analysis_parts.append("市場は売られすぎの状態です。")
        elif rsi > 60:
            analysis_parts.append("市場は買われすぎの状態です。")
        else:
            analysis_parts.append("市場は中立的な状態です。")
        
        # ファンダメンタル
        if abs(macro_sent) > 0.5:
            if macro_sent > 0:
                analysis_parts.append("最近の経済指標は強気のサプライズが多く、上昇要因となっています。")
            else:
                analysis_parts.append("最近の経済指標は弱気のサプライズが多く、下落要因となっています。")
        
        # 判断
        direction_jp = {"buy": "買い", "sell": "売り", "hold": "様子見"}[direction]
        conf_percent = int(confidence * 100)
        analysis_parts.append(f"\n判断: {direction_jp}（信頼度: {conf_percent}%）")
        
        return "\n".join(analysis_parts)
    
    def _extract_key_factors(self, latest: pd.Series, direction: str) -> List[str]:
        """主要要因を抽出"""
        factors = []
        
        rsi = latest.get('rsi_14', 50)
        if rsi < 30:
            factors.append("RSI売られすぎ")
        elif rsi > 70:
            factors.append("RSI買われすぎ")
        
        macro_sent = latest.get('macro_sent_24H', 0)
        if abs(macro_sent) > 0.5:
            factors.append(f"マクロイベント影響（{macro_sent:+.2f}）")
        
        vol = latest.get('vol_20', 0)
        if vol > latest.get('vol_60', vol) * 1.5:
            factors.append("ボラティリティ急上昇")
        
        return factors
    
    def _assess_risk(self, latest: pd.Series, features_df: pd.DataFrame) -> str:
        """リスクレベルを評価"""
        vol = latest.get('vol_20', 0)
        spread = latest.get('spread', 0)
        
        # ボラティリティが高い
        if len(features_df) > 20:
            vol_p95 = features_df['vol_20'].quantile(0.95)
            if vol > vol_p95:
                return "high"
        
        # スプレッドが広い
        if spread > latest.get('spread_ma_60', spread) * 1.5:
            return "high"
        
        # イベントが多い
        if latest.get('macro_cnt_24H', 0) > 3:
            return "medium"
        
        return "low"
    
    def _format_prediction(self, direction: str, confidence: float, latest: pd.Series) -> str:
        """予測テキストをフォーマット"""
        direction_jp = {"buy": "買い", "sell": "売り", "hold": "様子見"}[direction]
        conf_percent = int(confidence * 100)
        close = latest.get('close', 0)
        
        return f"""💹 USDJPY 予測

方向: {direction_jp}
信頼度: {conf_percent}%
現在価格: {close:.2f}

📊 主要指標
RSI(14): {latest.get('rsi_14', 'N/A'):.2f}
ATR(14): {latest.get('atr_14', 'N/A'):.4f}
MA(20): {latest.get('ma_20', 'N/A'):.2f}

📈 イベント（24時間）
マクロ: {latest.get('macro_cnt_24H', 0):.0f}件
ニュース: {latest.get('news_cnt_24H', 0):.0f}件"""


def create_fx_agent(model_path: Optional[str] = None) -> FXAnalysisAgent:
    """FX分析エージェントを作成"""
    default_model_path = "models/fx_usdjpy_model.pkl"
    if model_path is None:
        model_path = default_model_path if Path(default_model_path).exists() else None
    
    return FXAnalysisAgent(model_path=model_path)


def analyze_fx(user_text: str, pair: str = "USDJPY") -> str:
    """
    FX分析を実行して自然言語で返答
    
    Args:
        user_text: ユーザーの質問・メッセージ
        pair: 通貨ペア
    
    Returns:
        分析結果のテキスト
    """
    # 特徴量データを読み込む
    features_path = Path(f"data/features/{pair}/M5_features.parquet")
    if not features_path.exists():
        return f"⚠️ {pair}の特徴量データが見つかりません。まずデータ更新を実行してください。"
    
    try:
        features_df = pd.read_parquet(features_path)
        if features_df.empty:
            return "⚠️ 特徴量データが空です。"
        
        # エージェントを作成
        agent = create_fx_agent()
        
        # 分析実行
        result = agent.analyze(features_df, pair=pair)
        
        # 自然言語で返答を生成
        response_parts = [result["prediction"]]
        
        if result["analysis"]:
            response_parts.append("\n📋 詳細分析")
            response_parts.append(result["analysis"])
        
        if result["key_factors"]:
            response_parts.append("\n🔑 主要要因")
            for i, factor in enumerate(result["key_factors"], 1):
                response_parts.append(f"{i}. {factor}")
        
        # リスク警告
        if result["risk_level"] == "high":
            response_parts.append("\n⚠️ リスク: 高（ボラティリティ・スプレッドに注意）")
        elif result["risk_level"] == "medium":
            response_parts.append("\n⚠️ リスク: 中")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"⚠️ 分析エラー: {str(e)}"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FX予測モデル学習スクリプト（高精度分析用）
LightGBMを使用して買い/売り/様子見を予測
"""

import argparse
import pickle
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import lightgbm as lgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import classification_report, confusion_matrix
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("[ERROR] LightGBM and scikit-learn required. Install with: pip install lightgbm scikit-learn")


def create_target(features_df: pd.DataFrame, forward_bars: int = 60) -> pd.Series:
    """
    ターゲット変数を作成（将来の価格変動から買い/売り/様子見を判定）
    
    Args:
        features_df: 特徴量DataFrame
        forward_bars: 何バー先の価格と比較するか（デフォルト: 60バー = 5時間）
    
    Returns:
        0=売り, 1=様子見, 2=買い
    """
    if 'close' not in features_df.columns:
        # closeが無い場合はlogretから復元
        if 'logret_1' in features_df.columns:
            close = np.exp(features_df['logret_1'].cumsum())
        else:
            raise ValueError("close or logret_1 column required")
    else:
        close = features_df['close']
    
    # 将来の価格変動率
    future_return = (close.shift(-forward_bars) / close - 1.0)
    
    # 閾値で分類（調整可能）
    buy_threshold = 0.001   # 0.1%以上上昇 → 買い
    sell_threshold = -0.001  # 0.1%以上下落 → 売り
    
    target = pd.Series(1, index=features_df.index, dtype=int)  # デフォルト: 様子見
    target[future_return > buy_threshold] = 2   # 買い
    target[future_return < sell_threshold] = 0  # 売り
    
    # 未来データが無い行はNaN
    target[future_return.isna()] = np.nan
    
    return target


def prepare_features(features_df: pd.DataFrame) -> pd.DataFrame:
    """特徴量を準備（NaN処理・型変換）"""
    # 数値特徴量のみ選択
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # 除外する列（ターゲットやIDなど）
    exclude_cols = ['ts', 'timestamp', 'date', 'target', 'y']
    feature_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    X = features_df[feature_cols].copy()
    
    # NaN処理
    X = X.fillna(0)
    
    # 無限大の処理
    X = X.replace([np.inf, -np.inf], 0)
    
    return X, feature_cols


def train_model(features_path: str, output_path: str, 
                train_start: str = None, train_end: str = None,
                forward_bars: int = 60):
    """
    モデルを学習
    
    Args:
        features_path: 特徴量Parquetファイルのパス
        output_path: モデル保存先パス
        train_start: 学習開始日（YYYY-MM-DD）
        train_end: 学習終了日（YYYY-MM-DD）
        forward_bars: 予測先のバー数
    """
    if not LIGHTGBM_AVAILABLE:
        raise ImportError("LightGBM and scikit-learn required")
    
    print(f"[INFO] Loading features from {features_path}")
    features_df = pd.read_parquet(features_path)
    
    # タイムスタンプ処理
    if 'ts' in features_df.columns:
        features_df['ts'] = pd.to_datetime(features_df['ts'], utc=True, errors='coerce')
        features_df = features_df.set_index('ts').sort_index()
    elif features_df.index.dtype == 'datetime64[ns]':
        pass  # 既にインデックスがdatetime
    else:
        raise ValueError("Timestamp column 'ts' or datetime index required")
    
    # 日付フィルタ
    if train_start:
        features_df = features_df[features_df.index >= train_start]
    if train_end:
        features_df = features_df[features_df.index < train_end]
    
    print(f"[INFO] Data shape: {features_df.shape}")
    print(f"[INFO] Date range: {features_df.index.min()} to {features_df.index.max()}")
    
    # ターゲット作成
    print("[INFO] Creating target variable...")
    target = create_target(features_df, forward_bars=forward_bars)
    
    # 特徴量準備
    X, feature_cols = prepare_features(features_df)
    
    # 有効なデータのみ選択（ターゲットがNaNでない）
    valid_mask = ~target.isna()
    X = X[valid_mask]
    y = target[valid_mask]
    
    print(f"[INFO] Valid samples: {len(X)}")
    print(f"[INFO] Target distribution:\n{y.value_counts().sort_index()}")
    
    if len(X) < 100:
        raise ValueError(f"Insufficient data: {len(X)} samples. Need at least 100.")
    
    # 時系列分割（walk-forward検証）
    tscv = TimeSeriesSplit(n_splits=3)
    train_scores = []
    val_scores = []
    
    print("[INFO] Training model with time series cross-validation...")
    
    best_model = None
    best_score = 0
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # LightGBMモデル
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        params = {
            'objective': 'multiclass',
            'num_class': 3,
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        model = lgb.train(
            params,
            train_data,
            valid_sets=[val_data],
            num_boost_round=100,
            callbacks=[lgb.early_stopping(10), lgb.log_evaluation(10)]
        )
        
        # 評価
        train_pred = model.predict(X_train, num_iteration=model.best_iteration)
        val_pred = model.predict(X_val, num_iteration=model.best_iteration)
        
        train_acc = (train_pred.argmax(axis=1) == y_train.values).mean()
        val_acc = (val_pred.argmax(axis=1) == y_val.values).mean()
        
        train_scores.append(train_acc)
        val_scores.append(val_acc)
        
        print(f"[INFO] Fold {fold+1}: Train Acc={train_acc:.3f}, Val Acc={val_acc:.3f}")
        
        if val_acc > best_score:
            best_score = val_acc
            best_model = model
    
    # 最終モデル（全データで学習）
    print("[INFO] Training final model on all data...")
    train_data = lgb.Dataset(X, label=y)
    final_model = lgb.train(
        params,
        train_data,
        num_boost_round=best_model.best_iteration if best_model else 100,
        callbacks=[lgb.log_evaluation(10)]
    )
    
    # 保存
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    model_data = {
        'model': final_model,
        'feature_columns': feature_cols,
        'forward_bars': forward_bars,
        'train_date_range': (features_df.index.min(), features_df.index.max()),
        'target_distribution': y.value_counts().to_dict(),
        'cv_scores': {
            'train_mean': np.mean(train_scores),
            'val_mean': np.mean(val_scores),
            'val_std': np.std(val_scores)
        }
    }
    
    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"[OK] Model saved to {output_path}")
    print(f"[INFO] Cross-validation scores: Train={np.mean(train_scores):.3f}, Val={np.mean(val_scores):.3f}±{np.std(val_scores):.3f}")
    
    # 特徴量重要度
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': final_model.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    print("\n[INFO] Top 10 important features:")
    print(feature_importance.head(10).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True, help="Features parquet path")
    ap.add_argument("--output", default="models/fx_usdjpy_model.pkl", help="Output model path")
    ap.add_argument("--train-start", help="Training start date (YYYY-MM-DD)")
    ap.add_argument("--train-end", help="Training end date (YYYY-MM-DD)")
    ap.add_argument("--forward-bars", type=int, default=60, help="Forward bars for target (default: 60)")
    args = ap.parse_args()
    
    train_model(
        features_path=args.features,
        output_path=args.output,
        train_start=args.train_start,
        train_end=args.train_end,
        forward_bars=args.forward_bars
    )


if __name__ == "__main__":
    main()

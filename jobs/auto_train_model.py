#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動モデル学習スクリプト（定期実行用）
新しいデータが追加されたら自動的にモデルを再学習
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pandas as pd

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from jobs.train_fx_model import train_model


def should_retrain(model_path: str, features_path: str, min_days_since_train: int = 7) -> bool:
    """
    モデルを再学習すべきか判定
    
    Args:
        model_path: モデルファイルのパス
        features_path: 特徴量ファイルのパス
        min_days_since_train: 前回学習から何日経過したら再学習するか
    
    Returns:
        True: 再学習すべき, False: 不要
    """
    model_file = Path(model_path)
    features_file = Path(features_path)
    
    # 特徴量ファイルが存在しない
    if not features_file.exists():
        print(f"[INFO] Features file not found: {features_path}. Skipping retrain.")
        return False
    
    # モデルファイルが存在しない → 初回学習
    if not model_file.exists():
        print(f"[INFO] Model file not found: {model_path}. Will train initial model.")
        return True
    
    # モデルの更新日時を取得
    model_mtime = datetime.fromtimestamp(model_file.stat().st_mtime, tz=timezone.utc)
    
    # 特徴量の更新日時を取得
    features_mtime = datetime.fromtimestamp(features_file.stat().st_mtime, tz=timezone.utc)
    
    # 特徴量がモデルより新しい → 再学習が必要
    if features_mtime > model_mtime:
        print(f"[INFO] Features updated after model. Retraining needed.")
        return True
    
    # 前回学習から一定期間経過 → 再学習
    days_since_train = (datetime.now(timezone.utc) - model_mtime).days
    if days_since_train >= min_days_since_train:
        print(f"[INFO] {days_since_train} days since last training. Retraining.")
        return True
    
    print(f"[INFO] Model is up to date. Last trained: {model_mtime}, Features updated: {features_mtime}")
    return False


def auto_train(pair: str = "USDJPY", 
               features_tf: str = "M5",
               model_path: str = None,
               min_days_since_train: int = 7,
               force: bool = False):
    """
    自動モデル学習を実行
    
    Args:
        pair: 通貨ペア
        features_tf: 特徴量の時間足
        model_path: モデル保存先（Noneの場合はデフォルト）
        min_days_since_train: 再学習判定の最小日数
        force: 強制再学習（判定をスキップ）
    """
    if model_path is None:
        model_path = f"models/fx_{pair.lower()}_model.pkl"
    
    features_path = f"data/features/{pair}/{features_tf}_features.parquet"
    
    # 再学習判定
    if not force and not should_retrain(model_path, features_path, min_days_since_train):
        print("[INFO] Model retraining not needed. Use --force to force retraining.")
        return
    
    # 特徴量データを確認
    if not Path(features_path).exists():
        print(f"[ERROR] Features file not found: {features_path}")
        return
    
    # データ量を確認
    try:
        df = pd.read_parquet(features_path)
        if len(df) < 1000:
            print(f"[WARN] Insufficient data: {len(df)} rows. Need at least 1000 rows.")
            return
    except Exception as e:
        print(f"[ERROR] Failed to read features: {e}")
        return
    
    # 学習期間を自動設定
    try:
        if 'ts' in df.columns:
            df['ts'] = pd.to_datetime(df['ts'], utc=True, errors='coerce')
            df = df.set_index('ts').sort_index()
        elif df.index.dtype == 'datetime64[ns]':
            pass
        else:
            print("[WARN] No timestamp found. Using all data.")
            train_start = None
            train_end = None
    except Exception:
        train_start = None
        train_end = None
    else:
        # 最新1年分で学習（または全データ）
        # 必要に応じて調整可能
        train_start = None  # 全データを使用
        train_end = None
    
    print(f"[INFO] Starting model training...")
    print(f"[INFO] Features: {features_path}")
    print(f"[INFO] Output: {model_path}")
    print(f"[INFO] Data rows: {len(df)}")
    
    try:
        train_model(
            features_path=features_path,
            output_path=model_path,
            train_start=train_start,
            train_end=train_end,
            forward_bars=60
        )
        print(f"[OK] Model training completed: {model_path}")
    except Exception as e:
        print(f"[ERROR] Model training failed: {e}")
        raise


def main():
    import argparse
    
    ap = argparse.ArgumentParser(description="Auto train FX model")
    ap.add_argument("--pair", default="USDJPY", help="Currency pair")
    ap.add_argument("--features-tf", default="M5", help="Features timeframe")
    ap.add_argument("--model-path", help="Model output path (default: models/fx_{pair}_model.pkl)")
    ap.add_argument("--min-days", type=int, default=7, help="Minimum days since last training to retrain")
    ap.add_argument("--force", action="store_true", help="Force retraining regardless of conditions")
    args = ap.parse_args()
    
    auto_train(
        pair=args.pair,
        features_tf=args.features_tf,
        model_path=args.model_path,
        min_days_since_train=args.min_days,
        force=args.force
    )


if __name__ == "__main__":
    main()

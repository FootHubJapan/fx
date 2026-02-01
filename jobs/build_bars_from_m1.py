#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
import pandas as pd


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample M1 to higher timeframes"""
    try:
        # 必要なカラムが存在するか確認
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # resampleを実行
        o = df["open"].resample(rule).first()
        h = df["high"].resample(rule).max()
        l = df["low"].resample(rule).min()
        c = df["close"].resample(rule).last()
        
        # ボリュームとスプレッド（オプション）
        v = df.get("vol", pd.Series(index=df.index, dtype=float)).resample(rule).sum() if "vol" in df.columns else pd.Series(index=o.index, dtype=float)
        s = df.get("spread", pd.Series(index=df.index, dtype=float)).resample(rule).mean() if "spread" in df.columns else pd.Series(index=o.index, dtype=float)
        
        out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "vol": v, "spread": s})
        return out.dropna(subset=["open","high","low","close"])
    except Exception as e:
        print(f"[ERROR] Resample failed with rule {rule}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def build_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Build monthly bars"""
    return resample_ohlc(df, "M")


def build_6m_from_1m(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Build 6-month bars from monthly"""
    return resample_ohlc(df_1m, "6M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--m1-root", default="data/bars", help="bars root with tf=M1/date=...")
    ap.add_argument("--out-root", default="data/bars")
    ap.add_argument("--tfs", default="M5,M15,H1,H4,D1,W1,1M,6M")
    args = ap.parse_args()

    pair = args.pair.upper()
    m1_root = Path(args.m1_root) / pair / "tf=M1"
    out_root = Path(args.out_root) / pair

    files = sorted(m1_root.glob("date=*/part-*.parquet"))
    if not files:
        raise SystemExit("No M1 parquet files found")

    # Load all M1 data
    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(f)
            df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
            df = df.dropna(subset=["ts"]).set_index("ts").sort_index()
            dfs.append(df)
        except Exception as e:
            print(f"[WARN] Failed to read {f}: {e}")
            continue

    if not dfs:
        raise SystemExit("No valid M1 data found")

    m1 = pd.concat(dfs).sort_index()

    # 時間足のマッピング（pandas resample形式）
    tf_map = {
        "M5": "5T",    # 5分
        "M15": "15T",  # 15分
        "H1": "1H",    # 1時間
        "H4": "4H",    # 4時間
        "D1": "1D",    # 1日
        "W1": "1W",    # 1週間
    }
    
    tf_list = [x.strip() for x in args.tfs.split(",") if x.strip()]
    for tf in tf_list:
        if tf == "1M":
            bars = build_monthly(m1)
            rule_name = "1M"
        elif tf == "6M":
            m_1m = build_monthly(m1)
            bars = build_6m_from_1m(m_1m)
            rule_name = "6M"
        else:
            # 時間足をpandas resample形式に変換
            rule = tf_map.get(tf, tf)
            bars = resample_ohlc(m1, rule)
            rule_name = tf

        if bars.empty:
            print(f"[WARN] No bars for {rule_name}")
            continue

        out_dir = out_root / f"tf={rule_name}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "all.parquet"
        bars.reset_index().to_parquet(out_path, index=False)
        print(f"[OK] wrote {out_path} rows={len(bars)}")


if __name__ == "__main__":
    main()

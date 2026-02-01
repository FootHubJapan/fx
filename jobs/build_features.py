#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import numpy as np
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    roll_up = up.ewm(alpha=1/period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = roll_up / (roll_down.replace(0, np.nan))
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high-low), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def build_event_rolling(index_utc: pd.DatetimeIndex, events: pd.DataFrame, prefix: str, windows):
    """Build rolling event features"""
    out = pd.DataFrame(index=index_utc)
    if events is None or events.empty:
        for w in windows:
            out[f"{prefix}_cnt_{w}"] = 0.0
            out[f"{prefix}_sent_{w}"] = 0.0
        return out

    ev = events.copy()
    ev["ts"] = pd.to_datetime(ev["ts"], utc=True, errors="coerce")
    ev = ev.dropna(subset=["ts"]).sort_values("ts")
    if ev.empty:
        return out

    # Use sentiment_w if available
    if "sentiment_w" in ev.columns:
        ev_val = ev[["ts", "sentiment_w"]].rename(columns={"sentiment_w": "val"})
    else:
        ev_val = ev[["ts", "sentiment"]].rename(columns={"sentiment": "val"})
        ev_val["val"] = ev_val["val"].fillna(0.0)

    # Bin to bar frequency
    freq = pd.infer_freq(index_utc) or "T"
    ev_val["bin"] = ev_val["ts"].dt.floor(freq)
    b = ev_val.groupby("bin")["val"].agg(["count", "sum"]).rename(columns={"count": "cnt", "sum": "sum"})
    b = b.reindex(index_utc, fill_value=0.0)

    for w in windows:
        out[f"{prefix}_cnt_{w}"] = b["cnt"].rolling(w, min_periods=1).sum().values
        out[f"{prefix}_sent_{w}"] = b["sum"].rolling(w, min_periods=1).sum().values

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", required=True, help="bars parquet path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--events-cache", required=True)
    ap.add_argument("--windows", default="15T,1H,6H,24H,72H,168H")
    args = ap.parse_args()

    # Load bars
    bars = pd.read_parquet(args.bars)
    bars["ts"] = pd.to_datetime(bars["ts"], utc=True, errors="coerce")
    bars = bars.dropna(subset=["ts"]).set_index("ts").sort_index()

    # Technical features
    feat = pd.DataFrame(index=bars.index)
    feat["logret_1"] = np.log(bars["close"]).diff()
    for n in [5, 20, 60]:
        feat[f"ma_{n}"] = bars["close"].rolling(n).mean()
        feat[f"vol_{n}"] = feat["logret_1"].rolling(n).std()

    feat["rsi_14"] = rsi(bars["close"], 14)
    feat["atr_14"] = atr(bars, 14)

    # Time features
    idx = feat.index
    feat["hour_utc"] = idx.hour
    feat["dow_utc"] = idx.dayofweek

    # Spread features
    if "spread" in bars.columns:
        feat["spread"] = bars["spread"]
        feat["spread_ma_60"] = bars["spread"].rolling(60).mean()

    # Event features
    events = pd.read_parquet(args.events_cache) if os.path.exists(args.events_cache) else pd.DataFrame()
    windows = [w.strip() for w in args.windows.split(",") if w.strip()]

    news = events[events.get("category", "") == "news"] if not events.empty else pd.DataFrame()
    macro = events[events.get("category", "") == "macro"] if not events.empty else pd.DataFrame()

    feat = feat.join(build_event_rolling(feat.index, news, "news", windows))
    feat = feat.join(build_event_rolling(feat.index, macro, "macro", windows))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    feat.reset_index().to_parquet(args.out, index=False)
    print(f"[OK] wrote features {args.out} rows={len(feat)} cols={feat.shape[1]}")


if __name__ == "__main__":
    main()

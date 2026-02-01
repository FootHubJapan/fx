#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import argparse
import lzma
import struct
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

RECORD = struct.Struct(">3I2f")  # time(ms), ask(int), bid(int), askVol(float), bidVol(float)


def parse_bi5(path: Path, price_scale: int) -> pd.DataFrame:
    """Parse .bi5 file to tick DataFrame"""
    parts = path.parts
    hour = int(path.name.split("h_")[0])
    # パス構造: data/raw_bi5/USDJPY/2026/00/27/10h_ticks.bi5
    # parts[-4] = 年, parts[-3] = 月(00-11), parts[-2] = 日
    year = int(parts[-4])
    month0 = int(parts[-3])  # 00-11
    day = int(parts[-2])
    base = datetime(year, month0 + 1, day, hour, 0, 0, tzinfo=timezone.utc)

    try:
        with lzma.open(path, "rb") as f:
            buf = f.read()
        if not buf:
            print(f"[WARN] Empty file: {path}")
            return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

    rows = []
    record_count = len(buf) // RECORD.size
    if record_count == 0:
        print(f"[WARN] No records in {path}")
        return pd.DataFrame()
    
    print(f"[DEBUG] Processing {record_count} records from {path.name}")
    for off in range(0, len(buf), RECORD.size):
        if off + RECORD.size > len(buf):
            break
        try:
            t_ms, ask_i, bid_i, ask_v, bid_v = RECORD.unpack_from(buf, off)
            ts = base + timedelta(milliseconds=int(t_ms))
            ask = ask_i / price_scale
            bid = bid_i / price_scale
            rows.append((ts, bid, ask, float(bid_v), float(ask_v)))
        except Exception as e:
            print(f"[WARN] Failed to unpack record at offset {off}: {e}")
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["ts", "bid", "ask", "bid_vol", "ask_vol"])
    df = df.sort_values("ts")
    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    df["spread"] = df["ask"] - df["bid"]
    return df


def ticks_to_m1(ticks: pd.DataFrame) -> pd.DataFrame:
    """Convert ticks to M1 OHLC bars"""
    if ticks.empty:
        return pd.DataFrame()
    t = ticks.set_index("ts")
    out = pd.DataFrame({
        "open": t["mid"].resample("1min").first(),
        "high": t["mid"].resample("1min").max(),
        "low":  t["mid"].resample("1min").min(),
        "close":t["mid"].resample("1min").last(),
        "vol":  (t["bid_vol"] + t["ask_vol"]).resample("1min").sum(),
        "spread": t["spread"].resample("1min").mean(),
    })
    return out.dropna(subset=["open","high","low","close"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--in-root", default="data/raw_bi5")
    ap.add_argument("--out-root", default="data/bars")
    ap.add_argument("--price-scale", type=int, default=1000, help="USDJPY: 1000 or 100000")
    ap.add_argument("--start-date", required=True, help="UTC date like 2025-01-01")
    ap.add_argument("--end-date", required=True, help="UTC date like 2025-01-03 (exclusive)")
    args = ap.parse_args()

    pair = args.pair.upper()
    in_root = Path(args.in_root) / pair
    out_root = Path(args.out_root) / pair / "tf=M1"

    start = datetime.fromisoformat(args.start_date).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end_date).replace(tzinfo=timezone.utc)

    day = start
    while day < end:
        day_str = day.strftime("%Y-%m-%d")
        bi5s = sorted((in_root / f"{day.year}" / f"{day.month-1:02d}" / f"{day.day:02d}").glob("*h_ticks.bi5"))
        if not bi5s:
            print(f"[WARN] no bi5 for {day_str}")
            day += timedelta(days=1)
            continue

        m1_list = []
        for f in bi5s:
            ticks = parse_bi5(f, price_scale=args.price_scale)
            if not ticks.empty:
                m1 = ticks_to_m1(ticks)
                if not m1.empty:
                    m1_list.append(m1)

        if m1_list:
            m1_all = pd.concat(m1_list).sort_index()
            out_dir = out_root / f"date={day_str}"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "part-000.parquet"
            df_out = m1_all.reset_index().rename(columns={"ts": "ts"})
            df_out.to_parquet(out_path, index=False)
            print(f"[OK] wrote {out_path} rows={len(df_out)}")
        else:
            print(f"[WARN] no M1 data for {day_str}")

        day += timedelta(days=1)


if __name__ == "__main__":
    main()

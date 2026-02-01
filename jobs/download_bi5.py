#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


BASE = "https://datafeed.dukascopy.com/datafeed"


def month0(dt: datetime) -> str:
    """Dukascopyは月が0始まり（01月=00）"""
    return f"{dt.month - 1:02d}"


def bi5_url(pair: str, dt_utc: datetime) -> str:
    y = dt_utc.year
    m = month0(dt_utc)
    d = f"{dt_utc.day:02d}"
    h = f"{dt_utc.hour:02d}"
    return f"{BASE}/{pair}/{y}/{m}/{d}/{h}h_ticks.bi5"


def download(url: str, out_path: Path, timeout: int = 60) -> bool:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 0:
        return True

    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200 or not r.content:
            return False
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True, help="e.g. USDJPY")
    ap.add_argument("--start", required=True, help="UTC start like 2025-01-01T00")
    ap.add_argument("--end", required=True, help="UTC end like 2025-01-02T00 (exclusive)")
    ap.add_argument("--out-root", default="data/raw_bi5", help="Output root")
    args = ap.parse_args()

    pair = args.pair.upper()
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)

    out_root = Path(args.out_root) / pair
    cur = start
    ok = 0
    ng = 0

    while cur < end:
        url = bi5_url(pair, cur)
        out = out_root / f"{cur.year}" / month0(cur) / f"{cur.day:02d}" / f"{cur.hour:02d}h_ticks.bi5"
        if download(url, out):
            ok += 1
        else:
            ng += 1
        cur += timedelta(hours=1)

    print(f"[OK] done pair={pair} ok_hours={ok} missing_hours={ng}")


if __name__ == "__main__":
    main()

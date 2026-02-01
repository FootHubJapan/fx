#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import hashlib
from datetime import datetime, timezone
import pandas as pd
import feedparser

RSS = {
    "boj": "https://www.boj.or.jp/rss/whatsnew.rdf",
    "ecb": "https://www.ecb.europa.eu/rss/press.html",
    "fed": "https://www.federalreserve.gov/feeds/press_all.xml",
    "boe": "https://www.bankofengland.co.uk/rss/speeches"
}


def make_id(src: str, link: str, title: str) -> str:
    h = hashlib.sha1(f"{src}|{link}|{title}".encode("utf-8")).hexdigest()
    return f"rss_{h}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events-cache", required=True)
    args = ap.parse_args()

    if os.path.exists(args.events_cache):
        try:
            cache = pd.read_parquet(args.events_cache)
            cache["ts"] = pd.to_datetime(cache["ts"], utc=True, errors="coerce")
        except Exception:
            cache = pd.DataFrame()
    else:
        cache = pd.DataFrame()

    rows = []
    for src, url in RSS.items():
        try:
            d = feedparser.parse(url)
            for e in d.entries[:200]:
                title = getattr(e, "title", "") or ""
                link = getattr(e, "link", "") or ""
                published = getattr(e, "published", "") or ""
                ts = pd.to_datetime(published, utc=True, errors="coerce")
                if pd.isna(ts):
                    ts = datetime.now(timezone.utc)

                rows.append({
                    "id": make_id(src, link, title),
                    "ts": ts,
                    "source": src,
                    "category": "news",
                    "importance": 2,
                    "weight": 0.35,
                    "sentiment": 0.0,
                    "sentiment_w": 0.0,
                    "event": title,
                    "url": link
                })
        except Exception as e:
            print(f"[WARN] Failed to fetch {src}: {e}")

    if rows:
        new_df = pd.DataFrame(rows)
        new_df["ts"] = pd.to_datetime(new_df["ts"], utc=True, errors="coerce")
        merged = pd.concat([cache, new_df], ignore_index=True) if not cache.empty else new_df
        merged = merged.dropna(subset=["ts"]).drop_duplicates(subset=["id"], keep="last").sort_values("ts")
    else:
        merged = cache

    os.makedirs(os.path.dirname(args.events_cache), exist_ok=True)
    merged.to_parquet(args.events_cache, index=False)
    print(f"[OK] rss merged rows={len(merged)} -> {args.events_cache}")


if __name__ == "__main__":
    main()

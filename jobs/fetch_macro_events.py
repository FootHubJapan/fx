#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
import requests

WEIGHT_BY_IMPORTANCE = {3: 1.0, 2: 0.35, 1: 0.15}


def usd_jpy_direction(event: str, country: str) -> float:
    """USDJPY向けの方向付きサプライズ符号"""
    e = (event or "").lower()
    c = (country or "").lower()

    if "unemployment" in e and "rate" in e:
        return -1.0
    if "jobless" in e or "claims" in e:
        return -1.0

    infl_kw = ["cpi", "pce", "ppi", "inflation", "deflator", "core"]
    labor_kw = ["payroll", "employment", "wage", "earnings"]
    rates_kw = ["interest rate", "rate decision", "fomc", "fed", "powell", "minutes", "policy", "statement", "boj"]
    growth_kw = ["gdp", "pmi", "ism", "retail sales", "industrial", "production", "tankan"]

    is_us = ("united states" in c) or (c == "us") or ("u.s." in c)
    is_jp = ("japan" in c) or (c == "jp")

    if is_us and any(k in e for k in infl_kw + labor_kw + rates_kw + growth_kw):
        return +1.0
    if is_jp and any(k in e for k in infl_kw + labor_kw + rates_kw + growth_kw):
        return -1.0

    return +1.0


def te_get_calendar_country(countries: str, start: str, end: str, key: str, importance: int):
    """TradingEconomics calendar API"""
    base = f"https://api.tradingeconomics.com/calendar/country/{countries}/{start}/{end}"
    params = {"c": key, "f": "json", "importance": str(importance), "values": "true"}
    try:
        r = requests.get(base, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERROR] TE API error: {e}")
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events-cache", required=True)
    ap.add_argument("--te-key", default=os.getenv("TE_API_KEY", "guest:guest"))
    ap.add_argument("--countries", default="japan,united%20states")
    ap.add_argument("--importance-list", default="2,3")
    ap.add_argument("--days-back", type=int, default=21)
    ap.add_argument("--chunk-days", type=int, default=7)
    args = ap.parse_args()

    importance_list = [int(x.strip()) for x in args.importance_list.split(",") if x.strip()]
    now = datetime.now(timezone.utc)
    start_dt = (now - timedelta(days=args.days_back)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = now

    # Load cache
    if os.path.exists(args.events_cache):
        try:
            cache = pd.read_parquet(args.events_cache)
            cache["ts"] = pd.to_datetime(cache["ts"], utc=True, errors="coerce")
        except Exception:
            cache = pd.DataFrame()
    else:
        cache = pd.DataFrame()

    rows = []
    cur = start_dt
    while cur < end_dt:
        nxt = min(cur + timedelta(days=args.chunk_days), end_dt)
        s = cur.strftime("%Y-%m-%d")
        e = nxt.strftime("%Y-%m-%d")

        for imp in importance_list:
            data = te_get_calendar_country(args.countries, s, e, args.te_key, imp)
            if isinstance(data, dict) and data.get("status"):
                continue

            for it in (data or []):
                cal_id = it.get("CalendarId") or it.get("CalendarID")
                ts = pd.to_datetime(it.get("Date"), utc=True, errors="coerce")
                if pd.isna(ts):
                    continue

                event = it.get("Event", "") or ""
                country = it.get("Country", "") or ""
                url = it.get("URL", "") or ""

                actual = it.get("ActualValue")
                forecast = it.get("ForecastValue")
                previous = it.get("PreviousValue")

                surprise = None
                if actual is not None and forecast is not None:
                    try:
                        surprise = float(actual) - float(forecast)
                    except Exception:
                        surprise = None

                try:
                    importance = int(it.get("Importance", imp))
                except Exception:
                    importance = imp

                weight = WEIGHT_BY_IMPORTANCE.get(importance, 0.2)
                dir_sign = usd_jpy_direction(event, country)
                dir_surprise = (float(surprise) * dir_sign) if surprise is not None else 0.0

                rows.append({
                    "id": str(cal_id) if cal_id is not None else f"te_{country}_{event}_{ts.isoformat()}",
                    "ts": ts,
                    "source": "te",
                    "category": "macro",
                    "importance": importance,
                    "weight": weight,
                    "sentiment": dir_surprise,
                    "sentiment_w": dir_surprise * weight,
                    "country": country,
                    "event": event,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous,
                    "surprise": surprise,
                    "dir_sign": dir_sign,
                    "dir_surprise": dir_surprise,
                    "url": url,
                })

        cur = nxt

    merged = cache
    if rows:
        new_df = pd.DataFrame(rows)
        new_df["ts"] = pd.to_datetime(new_df["ts"], utc=True, errors="coerce")
        merged = pd.concat([cache, new_df], ignore_index=True) if not cache.empty else new_df
        merged = merged.dropna(subset=["ts"]).drop_duplicates(subset=["id"], keep="last").sort_values("ts")

    os.makedirs(os.path.dirname(args.events_cache), exist_ok=True)
    merged.to_parquet(args.events_cache, index=False)
    print(f"[OK] events_cache updated rows={len(merged)} -> {args.events_cache}")


if __name__ == "__main__":
    main()

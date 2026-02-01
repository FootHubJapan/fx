#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OANDA APIからFXデータをダウンロード
無料トライアル: 7日間、1,000 quotes
"""

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import requests
from typing import Optional

# OANDA API設定
OANDA_API_BASE = "https://api-fxpractice.oanda.com"  # デモ環境
# OANDA_API_BASE = "https://api-fxtrade.oanda.com"  # 本番環境（有料）

DEFAULT_TIMEOUT = 30


def download_oanda_candles(
    pair: str,
    start: datetime,
    end: datetime,
    granularity: str = "H1",
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    OANDA APIからキャンドルデータを取得
    
    Args:
        pair: 通貨ペア（例: "USD_JPY"）
        start: 開始時刻（UTC）
        end: 終了時刻（UTC）
        granularity: 時間足（"M1", "M5", "M15", "H1", "H4", "D"など）
        api_key: OANDA APIキー（環境変数OANDA_API_KEYからも取得可能）
    
    Returns:
        DataFrame with OHLCV data
    """
    api_key = api_key or os.getenv("OANDA_API_KEY")
    if not api_key:
        raise ValueError("OANDA_API_KEY not set. Set environment variable or pass as argument.")
    
    # 通貨ペアをOANDA形式に変換（USDJPY -> USD_JPY）
    oanda_pair = pair[:3] + "_" + pair[3:] if len(pair) == 6 else pair
    
    url = f"{OANDA_API_BASE}/v3/instruments/{oanda_pair}/candles"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {
        "granularity": granularity,
        "from": start.isoformat(),
        "to": end.isoformat(),
        "price": "M"  # Mid price
    }
    
    print(f"[INFO] Downloading {oanda_pair} from OANDA...")
    print(f"[INFO] Period: {start} to {end}, Granularity: {granularity}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candles' not in data or not data['candles']:
            print(f"[WARN] No candles returned for {oanda_pair}")
            return pd.DataFrame()
        
        # データをDataFrameに変換
        rows = []
        for candle in data['candles']:
            if candle['complete']:  # 完全なキャンドルのみ
                rows.append({
                    'ts': pd.to_datetime(candle['time']),
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'vol': int(candle.get('volume', 0))
                })
        
        if not rows:
            print(f"[WARN] No complete candles found")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows)
        
        # UTCタイムゾーンに統一
        if df['ts'].dt.tz is None:
            df['ts'] = df['ts'].dt.tz_localize('UTC')
        else:
            df['ts'] = df['ts'].dt.tz_convert('UTC')
        
        # ソート
        df = df.sort_values('ts').reset_index(drop=True)
        
        print(f"[OK] Downloaded {len(df)} candles")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] OANDA API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[ERROR] Response: {e.response.text}")
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Failed to download from OANDA: {e}")
        return pd.DataFrame()


def main():
    ap = argparse.ArgumentParser(description="Download FX data from OANDA API")
    ap.add_argument("--pair", required=True, help="Currency pair (e.g., USDJPY)")
    ap.add_argument("--start", required=True, help="Start datetime (YYYY-MM-DDTHH:MM:SS)")
    ap.add_argument("--end", required=True, help="End datetime (YYYY-MM-DDTHH:MM:SS)")
    ap.add_argument("--granularity", default="H1", help="Granularity (M1, M5, M15, H1, H4, D)")
    ap.add_argument("--api-key", help="OANDA API key (or set OANDA_API_KEY env var)")
    ap.add_argument("--out-dir", default="data/oanda", help="Output directory")
    args = ap.parse_args()
    
    pair = args.pair.upper()
    out_dir = Path(args.out_dir) / pair
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 日時をパース
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    
    # データをダウンロード
    df = download_oanda_candles(
        pair=pair,
        start=start,
        end=end,
        granularity=args.granularity,
        api_key=args.api_key
    )
    
    if df.empty:
        print("[ERROR] No data downloaded")
        return
    
    # ファイル名を生成
    start_str = start.strftime("%Y%m%dT%H%M%S")
    end_str = end.strftime("%Y%m%dT%H%M%S")
    filename = f"{pair}_{args.granularity}_{start_str}_{end_str}.parquet"
    out_path = out_dir / filename
    
    # Parquet形式で保存
    df.to_parquet(out_path, index=False, compression='snappy')
    print(f"[OK] Saved to {out_path}")
    print(f"[INFO] Data shape: {df.shape}")
    print(f"[INFO] Date range: {df['ts'].min()} to {df['ts'].max()}")


if __name__ == "__main__":
    main()

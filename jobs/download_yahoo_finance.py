#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Yahoo FinanceからFXデータをダウンロード
yfinanceライブラリを使用（無料・簡単）
"""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("[ERROR] yfinance not installed. Install with: pip install yfinance")


def download_yahoo_fx(pair: str, start_date: str, end_date: str, interval: str = "1h") -> pd.DataFrame:
    """
    Yahoo FinanceからFXデータをダウンロード
    
    Args:
        pair: 通貨ペア（例: "USDJPY"）
        start_date: 開始日（YYYY-MM-DD）
        end_date: 終了日（YYYY-MM-DD）
        interval: 時間足（"1m", "5m", "15m", "30m", "1h", "1d"など）
    
    Returns:
        DataFrame with OHLCV data
    """
    if not YFINANCE_AVAILABLE:
        raise ImportError("yfinance not available. Install with: pip install yfinance")
    
    # Yahoo Financeのティッカーシンボル形式に変換
    # USDJPY -> USDJPY=X
    ticker_symbol = f"{pair}=X"
    
    print(f"[INFO] Downloading {ticker_symbol} from Yahoo Finance...")
    print(f"[INFO] Period: {start_date} to {end_date}, Interval: {interval}")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # データを取得
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=True,
            prepost=False
        )
        
        if df.empty:
            print(f"[WARN] No data returned for {ticker_symbol}")
            return pd.DataFrame()
        
        # カラム名を標準化（Open, High, Low, Close, Volume）
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'vol'
        })
        
        # インデックスをリセット（timestampをカラムに）
        df = df.reset_index()
        
        # タイムスタンプカラムを探す（Date, Datetime, またはインデックス名）
        ts_col = None
        for col in ['Date', 'Datetime', 'DatetimeIndex']:
            if col in df.columns:
                ts_col = col
                break
        
        # インデックス名を確認
        if ts_col is None and df.index.name:
            df = df.reset_index()
            if df.index.name in ['Date', 'Datetime']:
                ts_col = df.index.name
        
        # タイムスタンプカラムを'ts'にリネーム
        if ts_col:
            df = df.rename(columns={ts_col: 'ts'})
        else:
            # インデックスがDatetimeIndexの場合を確認
            if isinstance(df.index, pd.DatetimeIndex):
                df['ts'] = df.index
                df = df.reset_index(drop=True)
            else:
                # 最初のカラムが日時か確認
                first_col = df.columns[0]
                if pd.api.types.is_datetime64_any_dtype(df[first_col]):
                    df = df.rename(columns={first_col: 'ts'})
                else:
                    # 最後の手段: インデックスを確認
                    if df.index.name in ['Date', 'Datetime']:
                        df['ts'] = df.index
                        df = df.reset_index(drop=True)
                    else:
                        raise ValueError(f"Could not find timestamp column in Yahoo Finance data. Columns: {df.columns.tolist()}, Index: {df.index.name}")
        
        # UTCタイムゾーンに統一
        if 'ts' in df.columns:
            if df['ts'].dtype == 'object':
                df['ts'] = pd.to_datetime(df['ts'])
            if df['ts'].dt.tz is None:
                df['ts'] = df['ts'].dt.tz_localize('UTC')
            else:
                df['ts'] = df['ts'].dt.tz_convert('UTC')
        
        # 必要なカラムのみ選択
        required_cols = ['ts', 'open', 'high', 'low', 'close']
        if 'vol' in df.columns:
            required_cols.append('vol')
        
        df = df[required_cols].copy()
        
        # ソート
        df = df.sort_values('ts').reset_index(drop=True)
        
        print(f"[OK] Downloaded {len(df)} bars")
        return df
        
    except Exception as e:
        print(f"[ERROR] Failed to download from Yahoo Finance: {e}")
        return pd.DataFrame()


def main():
    ap = argparse.ArgumentParser(description="Download FX data from Yahoo Finance")
    ap.add_argument("--pair", required=True, help="Currency pair (e.g., USDJPY)")
    ap.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    ap.add_argument("--interval", default="1h", help="Interval (1m, 5m, 15m, 30m, 1h, 1d)")
    ap.add_argument("--out-dir", default="data/yahoo_finance", help="Output directory")
    args = ap.parse_args()
    
    if not YFINANCE_AVAILABLE:
        print("[ERROR] yfinance not installed. Install with: pip install yfinance")
        return
    
    pair = args.pair.upper()
    out_dir = Path(args.out_dir) / pair
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # データをダウンロード
    df = download_yahoo_fx(
        pair=pair,
        start_date=args.start_date,
        end_date=args.end_date,
        interval=args.interval
    )
    
    if df.empty:
        print("[ERROR] No data downloaded")
        return
    
    # ファイル名を生成（期間を含む）
    start_str = args.start_date.replace("-", "")
    end_str = args.end_date.replace("-", "")
    filename = f"{pair}_{args.interval}_{start_str}_{end_str}.parquet"
    out_path = out_dir / filename
    
    # Parquet形式で保存
    df.to_parquet(out_path, index=False, compression='snappy')
    print(f"[OK] Saved to {out_path}")
    print(f"[INFO] Data shape: {df.shape}")
    print(f"[INFO] Date range: {df['ts'].min()} to {df['ts'].max()}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
複数のデータソース（Dukascopy, Yahoo Finance, OANDA）をマージ
データの品質と可用性に基づいて優先順位を設定
"""

import argparse
from pathlib import Path
import pandas as pd
from typing import List, Optional


def load_dukascopy_data(m1_dir: Path, start_date: str, end_date: str) -> pd.DataFrame:
    """DukascopyのM1バーデータを読み込む"""
    dfs = []
    m1_path = m1_dir / "tf=M1"
    
    for date_dir in sorted(m1_path.glob("date=*")):
        date_str = date_dir.name.replace("date=", "")
        if start_date <= date_str <= end_date:
            for parquet_file in date_dir.glob("part-*.parquet"):
                try:
                    df = pd.read_parquet(parquet_file)
                    dfs.append(df)
                except Exception as e:
                    print(f"[WARN] Failed to load {parquet_file}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    result = pd.concat(dfs, ignore_index=True)
    result = result.sort_values('ts').reset_index(drop=True)
    result['source'] = 'dukascopy'
    return result


def load_yahoo_data(yahoo_dir: Path, start_date: str, end_date: str) -> pd.DataFrame:
    """Yahoo Financeのデータを読み込む"""
    dfs = []
    
    for parquet_file in sorted(yahoo_dir.glob("*.parquet")):
        try:
            df = pd.read_parquet(parquet_file)
            # 日付範囲でフィルタ
            df['date'] = pd.to_datetime(df['ts']).dt.date
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            if not df.empty:
                df = df.drop('date', axis=1)
                dfs.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {parquet_file}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    result = pd.concat(dfs, ignore_index=True)
    result = result.sort_values('ts').reset_index(drop=True)
    result['source'] = 'yahoo'
    return result


def load_oanda_data(oanda_dir: Path, start_date: str, end_date: str) -> pd.DataFrame:
    """OANDAのデータを読み込む"""
    dfs = []
    
    for parquet_file in sorted(oanda_dir.glob("*.parquet")):
        try:
            df = pd.read_parquet(parquet_file)
            # 日付範囲でフィルタ
            df['date'] = pd.to_datetime(df['ts']).dt.date
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            if not df.empty:
                df = df.drop('date', axis=1)
                dfs.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {parquet_file}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    result = pd.concat(dfs, ignore_index=True)
    result = result.sort_values('ts').reset_index(drop=True)
    result['source'] = 'oanda'
    return result


def merge_data_sources(
    dukascopy_dir: Optional[Path] = None,
    yahoo_dir: Optional[Path] = None,
    oanda_dir: Optional[Path] = None,
    start_date: str = None,
    end_date: str = None,
    priority: List[str] = None
) -> pd.DataFrame:
    """
    複数のデータソースをマージ
    
    Args:
        dukascopy_dir: Dukascopy M1バーのディレクトリ
        yahoo_dir: Yahoo Financeデータのディレクトリ
        oanda_dir: OANDAデータのディレクトリ
        start_date: 開始日（YYYY-MM-DD）
        end_date: 終了日（YYYY-MM-DD）
        priority: データソースの優先順位（例: ['dukascopy', 'yahoo', 'oanda']）
    
    Returns:
        マージされたDataFrame
    """
    if priority is None:
        priority = ['dukascopy', 'yahoo', 'oanda']
    
    all_data = {}
    
    # Dukascopyデータを読み込む
    if dukascopy_dir and dukascopy_dir.exists():
        print("[INFO] Loading Dukascopy data...")
        df_duka = load_dukascopy_data(dukascopy_dir, start_date, end_date)
        if not df_duka.empty:
            all_data['dukascopy'] = df_duka
            print(f"[OK] Loaded {len(df_duka)} bars from Dukascopy")
    
    # Yahoo Financeデータを読み込む
    if yahoo_dir and yahoo_dir.exists():
        print("[INFO] Loading Yahoo Finance data...")
        df_yahoo = load_yahoo_data(yahoo_dir, start_date, end_date)
        if not df_yahoo.empty:
            all_data['yahoo'] = df_yahoo
            print(f"[OK] Loaded {len(df_yahoo)} bars from Yahoo Finance")
    
    # OANDAデータを読み込む
    if oanda_dir and oanda_dir.exists():
        print("[INFO] Loading OANDA data...")
        df_oanda = load_oanda_data(oanda_dir, start_date, end_date)
        if not df_oanda.empty:
            all_data['oanda'] = df_oanda
            print(f"[OK] Loaded {len(df_oanda)} bars from OANDA")
    
    if not all_data:
        print("[WARN] No data sources available")
        return pd.DataFrame()
    
    # 優先順位に基づいてマージ
    # 同じタイムスタンプのデータがある場合、優先順位の高いソースを使用
    merged_df = None
    
    for source in priority:
        if source in all_data:
            df = all_data[source].copy()
            
            if merged_df is None:
                merged_df = df
            else:
                # 既存データとマージ（同じタイムスタンプは優先順位の高いソースで上書き）
                # まず、既存データにないタイムスタンプを追加
                existing_ts = set(merged_df['ts'])
                new_rows = df[~df['ts'].isin(existing_ts)]
                
                if not new_rows.empty:
                    merged_df = pd.concat([merged_df, new_rows], ignore_index=True)
                    merged_df = merged_df.sort_values('ts').reset_index(drop=True)
    
    if merged_df is not None:
        print(f"[OK] Merged data: {len(merged_df)} bars")
        print(f"[INFO] Sources: {merged_df['source'].value_counts().to_dict()}")
    
    return merged_df if merged_df is not None else pd.DataFrame()


def main():
    ap = argparse.ArgumentParser(description="Merge data from multiple sources")
    ap.add_argument("--pair", required=True, help="Currency pair (e.g., USDJPY)")
    ap.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    ap.add_argument("--dukascopy-dir", default="data/bars", help="Dukascopy M1 bars directory")
    ap.add_argument("--yahoo-dir", default="data/yahoo_finance", help="Yahoo Finance data directory")
    ap.add_argument("--oanda-dir", default="data/oanda", help="OANDA data directory")
    ap.add_argument("--priority", default="dukascopy,yahoo,oanda", 
                    help="Data source priority (comma-separated)")
    ap.add_argument("--out-dir", default="data/merged", help="Output directory")
    args = ap.parse_args()
    
    pair = args.pair.upper()
    priority = [s.strip() for s in args.priority.split(",")]
    
    # ディレクトリパス
    dukascopy_dir = Path(args.dukascopy_dir) / pair if args.dukascopy_dir else None
    yahoo_dir = Path(args.yahoo_dir) / pair if args.yahoo_dir else None
    oanda_dir = Path(args.oanda_dir) / pair if args.oanda_dir else None
    
    # データをマージ
    merged_df = merge_data_sources(
        dukascopy_dir=dukascopy_dir,
        yahoo_dir=yahoo_dir,
        oanda_dir=oanda_dir,
        start_date=args.start_date,
        end_date=args.end_date,
        priority=priority
    )
    
    if merged_df.empty:
        print("[ERROR] No data to merge")
        return
    
    # 出力ディレクトリを作成
    out_dir = Path(args.out_dir) / pair
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル名を生成
    filename = f"{pair}_merged_{args.start_date}_{args.end_date}.parquet"
    out_path = out_dir / filename
    
    # Parquet形式で保存
    merged_df.to_parquet(out_path, index=False, compression='snappy')
    print(f"[OK] Saved merged data to {out_path}")
    print(f"[INFO] Data shape: {merged_df.shape}")
    print(f"[INFO] Date range: {merged_df['ts'].min()} to {merged_df['ts'].max()}")


if __name__ == "__main__":
    main()

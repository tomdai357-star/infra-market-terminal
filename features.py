import logging
import pandas as pd
from ingest import fetch_asset_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def add_market_features(df: pd.DataFrame, drop_nan: bool = False) -> pd.DataFrame:
    """
    Appends 90-day and 180-day moving averages along with daily returns 
    to smooth daily price volatility for macro correlation testing.
    
    Args:
        df (pd.DataFrame): Cleaned dataframe from ingest.py (requires 'date' and 'close')
        drop_nan (bool): If True, discards rows before the 180-day window fills up.
        
    Returns:
        pd.DataFrame: Enriched dataframe with columns: [..., close_ma_90, close_ma_180, daily_return_pct]
    """
    if df.empty:
        logging.warning("Received empty DataFrame. Skipping feature engineering.")
        return df

    logging.info("Calculating technical smoothing features (90-day and 180-day MAs)...")

    # Ensure chronological order so rolling windows don't compute garbage data
    df = df.sort_values("date").reset_index(drop=True)

    # Calculate Moving Averages on the Closing Price
    df["close_ma_90"] = df["close"].rolling(window=90).mean()
    df["close_ma_180"] = df["close"].rolling(window=180).mean()

    # Calculate daily percentage returns (useful for short-term momentum checks later)
    df["daily_return_pct"] = df["close"].pct_change() * 100

    if drop_nan:
        original_len = len(df)
        df = df.dropna().reset_index(drop=True)
        logging.info(f"Dropped {original_len - len(df)} initial rows containing NaN window artifacts.")
    else:
        logging.info("Retained initial NaN window artifacts (first 179 rows will contain nulls).")

    logging.info("Feature engineering complete.")
    return df

if __name__ == "__main__":
    print("=== Testing Stage 2: Feature Engineering Engine ===")
    try:
        # 1. Pipeline Test: Fetch raw historical copper data (last 5 years)
        raw_copper = fetch_asset_data("HG=F", period="5y")
        
        # 2. Pipeline Test: Enrich with moving averages
        # We leave drop_nan=False for now so we can inspect the data structure integrity
        enriched_copper = add_market_features(raw_copper, drop_nan=False)
        
        print("\n--- Enriched Data Tail (Populated Features) ---")
        columns_to_show = ["date", "close", "close_ma_90", "close_ma_180", "daily_return_pct"]
        print(enriched_copper[columns_to_show].tail(10))
        
        print("\n--- Checking Data Types & Null Counts ---")
        enriched_copper.info()
        
    except Exception as e:
        print(f"\n[!] Feature engineering test failed: {e}")
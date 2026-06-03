import logging
import pandas as pd
import yfinance as yf
from typing import Optional

# Configure robust logging for pipeline observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_asset_data(ticker_symbol: str = "HG=F", period: str = "max") -> pd.DataFrame:
    """
    Fetches, normalizes, and cleans daily historical data for a given 
    ticker asset (commodity or equity) using yfinance.
    
    Args:
        ticker_symbol (str): The Yahoo Finance ticker symbol (e.g., 'HG=F' for Copper, 'FM.TO' for First Quantum)
        period (str): The historical time horizon to fetch (default: 'max')
        
    Returns:
        pd.DataFrame: Cleaned data with schema [date, open, high, low, close, volume]
    """
    logging.info(f"Initiating data extraction from yfinance for ticker: {ticker_symbol}")

    # 1. Resilience: Network extraction with error handling
    try:
        ticker_obj = yf.Ticker(ticker_symbol)
        # Fetch daily data
        raw_df = ticker_obj.history(period=period, interval="1d")
    except Exception as e:
        logging.error(f"Network error or invalid ticker while fetching {ticker_symbol}: {e}")
        raise RuntimeError(f"Failed to fetch data for {ticker_symbol}. Reason: {e}") from e

    if raw_df.empty:
        logging.warning(f"yfinance returned an empty DataFrame for ticker: {ticker_symbol}")
        return pd.DataFrame()

    # 2. Schema Normalization
    # yfinance places the timestamp into a timezone-aware Index. We need to reset it to a column.
    df = raw_df.reset_index()
    
    # Normalize column headers to strict lowercase
    df.columns = [col.lower() for col in df.columns]

    # Map the standard yfinance headers to our precise target schema
    # (Note: 'date' comes from the reset index. We explicitly ignore 'dividends' and 'stock splits')
    required_columns = ["date", "open", "high", "low", "close", "volume"]
    
    # Validate column integrity
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Extracted data is missing expected columns: {missing_cols}. yfinance schema mapping failed.")

    # Filter strictly to our required layout
    df = df[required_columns].copy()

    # 3. Data Cleaning
    # Remove timezone localization to achieve strict 'datetime64[ns]' format
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    
    # Drop rows with missing values and eliminate duplicate records
    df = df.dropna()
    df = df.drop_duplicates(subset=["date"])

    # 4. Strict Type Casting
    price_cols = ["open", "high", "low", "close"]
    df[price_cols] = df[price_cols].astype(float)
    df["volume"] = df["volume"].astype("int64")

    # Chronological sort guarantees window functions perform correctly downstream
    df = df.sort_values("date").reset_index(drop=True)

    logging.info(f"Successfully processed {len(df)} records for {ticker_symbol}.")
    return df

if __name__ == "__main__":
    print("=== Testing Stage 1 (yfinance): Data Ingestion Engine ===")
    try:
        # Fetching COMEX Copper Futures
        copper_df = fetch_asset_data("HG=F", period="5y")
        
        print("\n--- DataFrame Head ---")
        print(copper_df.head())
        
        print("\n--- DataFrame Tail ---")
        print(copper_df.tail())
        
        print("\n--- DataFrame Info ---")
        copper_df.info()
        
    except Exception as e:
        print(f"\n[!] Ingestion test failed: {e}")
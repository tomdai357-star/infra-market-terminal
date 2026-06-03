import logging
import duckdb
import pandas as pd
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def store_market_data(
    df: pd.DataFrame, 
    ticker_symbol: str, 
    db_path: str = "terminal_data.db"
) -> None:
    """
    Saves enriched market dataframe into a local DuckDB instance.
    Uses a 'delete-and-replace' strategy per ticker to ensure idempotency 
    and prevent duplicate date entries.
    
    Args:
        df (pd.DataFrame): Enriched dataframe from features.py
        ticker_symbol (str): The asset identifier (e.g., 'HG=F')
        db_path (str): The local file path for the database
    """
    if df.empty:
        logging.warning("Received empty DataFrame. Aborting database storage.")
        return

    logging.info(f"Connecting to DuckDB at '{db_path}'...")
    
    # 1. Connect to the embedded database (creates the file if it doesn't exist)
    with duckdb.connect(db_path) as conn:
        
        # 2. Inject the ticker symbol into the dataframe so the database knows 
        # which asset these rows belong to
        df_to_store = df.copy()
        df_to_store['ticker'] = ticker_symbol
        
        # 3. Define the strict analytical table schema
        # We use IF NOT EXISTS so this only runs on the very first execution
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_assets (
                ticker VARCHAR,
                date TIMESTAMP,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume BIGINT,
                close_ma_90 DOUBLE,
                close_ma_180 DOUBLE,
                daily_return_pct DOUBLE
            )
        """)
        
        # 4. Idempotency: Clear existing records for this specific ticker
        # This prevents duplicate dates if the script is run multiple times a day
        conn.execute("DELETE FROM daily_assets WHERE ticker = ?", (ticker_symbol,))
        
        # 5. Fast Columnar Insert
        # DuckDB can read directly from a pandas DataFrame registered in memory
        conn.register('df_view', df_to_store)
        conn.execute("INSERT INTO daily_assets SELECT * FROM df_view")
        
        # 6. Verification: Check how many rows we now have for this ticker
        result = conn.execute("SELECT COUNT(*) FROM daily_assets WHERE ticker = ?", (ticker_symbol,)).fetchone()
        row_count = result[0] if result else 0
        
        logging.info(f"Successfully committed {row_count} rows for {ticker_symbol} to the database.")

if __name__ == "__main__":
    from ingest import fetch_asset_data
    from features import add_market_features
    
    print("=== Testing Pipeline: Ingest -> Smooth -> Store ===")
    
    target_ticker = "HG=F"  # COMEX Copper
    
    try:
        # Stage 1: Ingest
        raw_df = fetch_asset_data(target_ticker, period="5y")
        
        # Stage 2: Smooth
        enriched_df = add_market_features(raw_df, drop_nan=False)
        
        # Stage 3: Store
        store_market_data(enriched_df, ticker_symbol=target_ticker)
        
        # Final Verification: Read it back from the database
        print("\n--- Verifying Data on Disk ---")
        with duckdb.connect("terminal_data.db") as check_conn:
            # Query the database to fetch the last 5 rows we just saved
            saved_data = check_conn.execute(f"""
                SELECT ticker, date, close, close_ma_90 
                FROM daily_assets 
                WHERE ticker = '{target_ticker}'
                ORDER BY date DESC 
                LIMIT 5
            """).df()
            print(saved_data)
            
    except Exception as e:
        print(f"\n[!] Pipeline test failed: {e}")
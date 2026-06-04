import duckdb
import pandas as pd
import logging

def store_market_data(df: pd.DataFrame, ticker_symbol: str, db_path: str = "terminal_data.db"):
    """
    Safely enforces schema alignment and stores the DataFrame into the local DuckDB database.
    """
    try:
        # 1. Create a clean copy to prevent altering the original dataframe
        insert_df = df.copy()
        
        # 2. Add the ticker identifier
        insert_df['ticker'] = ticker_symbol
        
        # 3. EXPLICIT ALIGNMENT: Order columns to match the database exactly
        cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
        
        # Append moving averages if the feature engineering stage generated them
        if 'close_ma_90' in insert_df.columns:
            cols.append('close_ma_90')
        if 'close_ma_180' in insert_df.columns:
            cols.append('close_ma_180')
            
        # Reorder the dataframe
        insert_df = insert_df[cols]
        
        # 4. Database Connection & Write
        with duckdb.connect(db_path) as conn:
            # Enforce the strict table schema
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
                    close_ma_180 DOUBLE
                )
            """)
            
            # Delete old records for this ticker to avoid duplicates if run multiple times
            conn.execute(f"DELETE FROM daily_assets WHERE ticker = '{ticker_symbol}'")
            
            # Insert the newly aligned data
            conn.execute("INSERT INTO daily_assets SELECT * FROM insert_df")
            
    except Exception as e:
        logging.error(f"Storage Layer Failure for {ticker_symbol}: {e}")
        raise
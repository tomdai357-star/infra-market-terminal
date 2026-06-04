import logging
import duckdb
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def calculate_time_lag_correlation(
    commodity_ticker: str, 
    equity_ticker: str, 
    db_path: str = "terminal_data.db",
    lags_to_test: list = [0, 30, 60, 90, 120, 180]
) -> pd.DataFrame:
    """
    Queries the local database, aligns dates, and tests multiple time-lags 
    to find the strongest predictive correlation between a commodity and an equity.
    
    Args:
        commodity_ticker (str): The input asset (e.g., 'HG=F')
        equity_ticker (str): The target asset (e.g., 'TECK-B.TO')
        db_path (str): Path to the DuckDB file
        lags_to_test (list): A list of trading day lags to test
        
    Returns:
        pd.DataFrame: A table of Pearson correlation coefficients sorted by strength
    """
    logging.info(f"Starting quantitative analysis: {commodity_ticker} vs {equity_ticker}")
    
    with duckdb.connect(db_path) as conn:
        # Step A: The Database JOIN
        # We specifically extract the 90-day smoothed commodity data 
        # and lock it to the daily closing price of the equity on the exact same date.
        query = f"""
            SELECT 
                c.date,
                c.close_ma_90 AS commodity_ma_90,
                e.close AS equity_close
            FROM daily_assets c
            JOIN daily_assets e ON c.date = e.date
            WHERE c.ticker = '{commodity_ticker}' 
              AND e.ticker = '{equity_ticker}'
            ORDER BY c.date ASC
        """
        df = conn.execute(query).df()
        
    if df.empty:
        logging.error("No overlapping historical data found for these tickers.")
        return pd.DataFrame()
        
    logging.info(f"Successfully aligned {len(df)} overlapping trading days.")
    
    # Step B & C: The Shift Operator & Statistical Matrix
    results = []
    
    for lag in lags_to_test:
        # We shift the equity price "up" (backwards in our table using a negative integer).
        # A shift of -90 aligns today's Copper MA with the Equity's price 90 trading days in the future.
        shifted_col_name = f'equity_shifted_{lag}'
        df[shifted_col_name] = df['equity_close'].shift(-lag)
        
        # Calculate Pearson correlation, which automatically ignores the NaNs created by shifting
        correlation = df['commodity_ma_90'].corr(df[shifted_col_name])
        
        results.append({
            "Lag_Days": lag,
            "Pearson_Correlation": round(correlation, 4)
        })
        
    # Step D: The Output DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by the absolute strength of the correlation to find the "sweet spot"
    results_df['Absolute_Strength'] = results_df['Pearson_Correlation'].abs()
    results_df = results_df.sort_values(by='Absolute_Strength', ascending=False).drop(columns=['Absolute_Strength'])
    
    logging.info("Correlation engine computation complete.")
    return results_df

if __name__ == "__main__":
    print("=== Testing Stage 5: Time-Lag Correlation Engine ===")
    
    # Target our primary commodity and one heavy-hitting infrastructure/mining equity
    target_commodity = "HG=F"
    target_equity = "TECK-B.TO"  
    
    try:
        correlation_results = calculate_time_lag_correlation(
            commodity_ticker=target_commodity,
            equity_ticker=target_equity
        )
        
        print(f"\n--- Statistical Correlation: {target_commodity} -> {target_equity} ---")
        print(correlation_results.to_string(index=False))
        
    except Exception as e:
        print(f"\n[!] Analysis failed: {e}")
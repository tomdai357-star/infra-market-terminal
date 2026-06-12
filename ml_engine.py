import duckdb
import pandas as pd
import xgboost as xgb
import logging
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def generate_forecast(commodity_ticker: str, equity_ticker: str, forecast_days: int = 5) -> pd.DataFrame:
    """Trains an XGBoost model on historical correlation to forecast future equity prices."""
    
    logging.info(f"Booting ML Engine for {equity_ticker} driven by {commodity_ticker}...")
    
    # 1. Pull the Normalized Data from DuckDB
    with duckdb.connect("terminal_data.db", read_only=True) as conn:
        query = f"""
            SELECT 
                c.date,
                c.close AS commodity_close,
                c.close_ma_90 AS commodity_ma_90,
                (e.close * fx.close) AS equity_close
            FROM daily_assets c
            JOIN daily_assets e ON c.date = e.date
            JOIN daily_assets fx ON c.date = fx.date
            WHERE c.ticker = '{commodity_ticker}' 
              AND e.ticker = '{equity_ticker}'
              AND fx.ticker = 'CADUSD=X'
            ORDER BY c.date ASC
        """
        df = conn.execute(query).df()

    if df.empty:
        raise ValueError("Insufficient data to train the model.")

    # 2. Feature Engineering for the AI
    # We create a 'target' column shifted backward. The AI tries to guess today's equity 
    # price based on what the commodity looked like 'forecast_days' ago.
    df['target_equity'] = df['equity_close'].shift(-forecast_days)
    
    # Drop rows where we don't have the future answer yet
    train_df = df.dropna().copy()
    
    # 3. Define the Inputs (X) and the Answer (y)
    X = train_df[['commodity_close', 'commodity_ma_90']]
    y = train_df['target_equity']
    
    # 4. Initialize XGBoost (Configured for performance)
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        tree_method='hist' # Highly optimized histogram algorithm
    )
    
    logging.info("Training XGBoost Regressor...")
    model.fit(X, y)
    
    # --- NEW: Future Prediction Logic ---
    logging.info(f"Projecting {forecast_days} days into the future...")
    
    # 5. Grab the most recent commodity data (the "blank zone" where future equity is unknown)
    future_zone = df.tail(forecast_days).copy()
    X_future = future_zone[['commodity_close', 'commodity_ma_90']]
    
    # 6. Ask the AI to predict the equity price based on these recent commodity movements
    predictions = model.predict(X_future)
    
    # 7. Generate future calendar dates for these predictions (skipping weekends)
    last_historical_date = pd.to_datetime(df['date'].dropna().iloc[-1])
    future_dates = pd.bdate_range(start=last_historical_date + pd.Timedelta(days=1), periods=forecast_days)
    
    # 8. Package the forecast into a clean DataFrame
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'predicted_equity': predictions
    })
    
    logging.info("Forecast generation complete.")
    return forecast_df

# Quick test execution
if __name__ == "__main__":
    generate_forecast("HG=F", "ARE.TO", 90)
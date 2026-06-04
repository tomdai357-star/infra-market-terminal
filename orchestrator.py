import json
import logging
import time
import pandas as pd
from ingest import fetch_asset_data
from features import add_market_features
from storage import store_market_data

# Configure central logging for the pipeline run
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_pipeline_config(config_path: str = "config.json") -> dict:
    """Loads and parses the external JSON configuration file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON formatting in {config_path}: {e}")
        raise

def run_pipeline() -> None:
    """Executes the complete data pipeline loop across the entire asset roster."""
    logging.info("Starting Master Pipeline Execution...")
    
    # 1. Initialize configuration and parameters
    config = load_pipeline_config()
    settings = config.get("settings", {})
    period = settings.get("historical_period", "5y")
    delay = settings.get("rate_limit_delay_seconds", 2)
    
    # 2. Flatten all asset categories into a single execution queue
    assets_config = config.get("assets", {})
    execution_queue = []
    
    for category, assets in assets_config.items():
        for asset in assets:
            execution_queue.append({
                "ticker": asset["ticker"],
                "name": asset["name"],
                "category": category
            })
            
    total_assets = len(execution_queue)
    logging.info(f"Successfully loaded {total_assets} assets into the execution queue.")
    
    # 3. Process each asset in a protective loop
    for index, asset in enumerate(execution_queue, start=1):
        ticker = asset["ticker"]
        name = asset["name"]
        
        logging.info(f"[{index}/{total_assets}] Processing {ticker} ({name})...")
        
        try:
            # Stage 1: Ingest raw data from yfinance
            raw_df = fetch_asset_data(ticker_symbol=ticker, period=period)
            
            if raw_df.empty:
                logging.warning(f"Skipping {ticker} due to empty data extraction.")
                continue
                
            # Stage 2: Feature Engineering (Calculate 90 and 180-day MAs)
            enriched_df = add_market_features(raw_df, drop_nan=False)
            
            # --- DEFENSIVE DATA ALIGNMENT FOR DUCKDB ---
            # If features.py set 'date' as the index, bring it back as a column
            if "date" not in enriched_df.columns and enriched_df.index.name == "date":
                enriched_df = enriched_df.reset_index()
            elif "date" not in enriched_df.columns:
                enriched_df = enriched_df.reset_index()
            
            # Ensure column names are explicitly lowercase strings to prevent schema mismatches
            enriched_df.columns = [str(col).lower() for col in enriched_df.columns]
            
            # Enforce that 'date' is positioned as the absolute first column
            if "date" in enriched_df.columns:
                cols = ["date"] + [col for col in enriched_df.columns if col != "date"]
                enriched_df = enriched_df[cols]
            # --------------------------------------------

            # Stage 3: Analytical Storage (Save to DuckDB)
            logging.info(f"Connecting to DuckDB to flush structured schema for {ticker}...")
            store_market_data(enriched_df, ticker_symbol=ticker)
            
            logging.info(f"[{index}/{total_assets}] Completed pipeline cycle for {ticker}.")
            
        except Exception as e:
            # Fault Tolerance: Catch errors so a single failed ticker won't kill the loop
            logging.error(f"CRITICAL FLUSH FAILURE for ticker {ticker}: {e}")
            logging.info(f"Continuing to next asset in queue...")
            
        # 4. Rate-Limiting: Pause execution to respect Yahoo Finance API constraints
        if index < total_assets:
            logging.info(f"Enforcing API rate limit etiquette. Sleeping for {delay} seconds...")
            time.sleep(delay)

    logging.info("Master Pipeline Execution finished successfully.")

if __name__ == "__main__":
    run_pipeline()
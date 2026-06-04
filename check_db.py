import duckdb
import pandas as pd

print("--- Database Diagnostic Report ---")
try:
    with duckdb.connect("terminal_data.db") as conn:
        # Check exactly what tickers exist, how many rows they have, and their date ranges
        query = """
            SELECT 
                ticker, 
                COUNT(*) as total_days, 
                MIN(date) as first_day, 
                MAX(date) as last_day
            FROM daily_assets 
            GROUP BY ticker
            ORDER BY ticker
        """
        df = conn.execute(query).df()
        
        if df.empty:
            print("[!] The database exists, but the table 'daily_assets' is completely empty.")
        else:
            print(df.to_string(index=False))
            
except Exception as e:
    print(f"[!] Critical Error: Cannot read database. {e}")
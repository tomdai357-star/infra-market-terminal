import yfinance as yf
import duckdb

print("--- Pipeline Diagnostic ---")
print("1. Fetching test data from yfinance...")
df = yf.download("ARE.TO", period="1mo", progress=False)

if df.empty:
    print("\n[!] FAIL: yfinance returned no data. You may be rate-limited or offline.")
else:
    print(f"[+] SUCCESS: Fetched {len(df)} rows.")
    print("2. Attempting to write to DuckDB...")
    try:
        with duckdb.connect("terminal_data.db") as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS debug_test AS SELECT * FROM df")
        print("[+] SUCCESS: Data written to DuckDB! The pipeline is healthy.")
    except Exception as e:
        print(f"\n[!] CRITICAL ERROR during database write:\n{e}")
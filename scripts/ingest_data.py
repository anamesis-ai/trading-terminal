import yfinance as yf
import sqlite3
import pandas as pd
from datetime import datetime

TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "CAC 40": "^FCHI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "SSE Composite": "000001.SS",
    "Gold": "GC=F",
    "Crude Oil": "CL=F",
    "USD Index": "DX-Y.NYB",
    "EUR/USD": "EURUSD=X",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Tesla": "TSLA"
}

conn = sqlite3.connect("db/market_data.db")
cursor = conn.cursor()

for name, ticker in TICKERS.items():
    print(f"Fetching data for {name} ({ticker})...")
    try:
        data = yf.download(ticker, period="5y", interval="1d", progress=False)
        data.dropna(inplace=True)
        data.reset_index(inplace=True)
        data['Ticker'] = ticker

        table_name = ticker.replace("^", "").replace("=", "").replace("-", "").replace(".", "_")
        data.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"✅ Stored {name} to table: {table_name}")
    except Exception as e:
        print(f"⚠️ Error fetching {ticker}: {e}")

conn.close()
print("✅ All data ingestion complete.")

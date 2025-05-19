import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import requests

st.set_page_config(page_title="Global Markets", layout="wide")

st.title("📉 Global Markets Dashboard")
st.markdown("Monitor live and historical data for global equity, FX, crypto, and bond markets.")
st.info("This dashboard will soon stream market data in real time and allow filtering by region, asset class, and time frame.")

TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "Gold": "GC=F",
    "Crude Oil": "CL=F",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "USD/EUR": "EURUSD=X"
}

def get_live_data(ticker_dict):
    results = []
    for asset, symbol in ticker_dict.items():
        try:
            df = yf.download(tickers=symbol, period="1d", interval="1m", progress=False, threads=False)
            if not df.empty:
                close_price = df["Close"].iloc[-1]
                results.append({"Asset": asset, "Ticker": symbol, "Price": round(float(close_price), 4)})
            else:
                results.append({"Asset": asset, "Ticker": symbol, "Price": None})
        except:
            results.append({"Asset": asset, "Ticker": symbol, "Price": None})
    return pd.DataFrame(results)

st.subheader("🌍 Live Market Prices")
with st.spinner("Fetching real-time market data..."):
    df = get_live_data(TICKERS)
    if not df.empty:
        st.dataframe(df.set_index("Asset"), use_container_width=True, height=400)
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("No live data available at this time.")

st.subheader("📈 Historical Price Trends (30 Days)")
selected_asset = st.selectbox("Select an asset to view its historical chart:", list(TICKERS.keys()))

def get_historical_data(ticker):
    df = yf.download(ticker, period="30d", interval="1d", progress=False, threads=False)
    if not df.empty:
        df = df['Close'].reset_index()
        df.columns = ['Date', 'Close']
        return df
    return pd.DataFrame(columns=["Date", "Close"])

with st.spinner(f"Loading 30-day chart for {selected_asset}..."):
    hist_df = get_historical_data(TICKERS[selected_asset])
    if not hist_df.empty:
        st.line_chart(data=hist_df, x="Date", y="Close", use_container_width=True)
    else:
        st.warning("No historical data available for this asset.")

st.subheader("🧠 Institutional Snapshot")
def calculate_technical_summary(ticker):
    df = yf.download(ticker, period="30d", interval="1d", progress=False, threads=False)
    if df.empty or 'Close' not in df.columns:
        return None
    df["Returns"] = df["Close"].pct_change()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    latest = df.dropna().iloc[-1]
    return {
        "30-Day Change (%)": round(float(((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100), 2),
        "Volatility (Std Dev)": round(float(df["Returns"].std() * 100), 2),
        "SMA (10-day)": round(float(latest["SMA_10"]), 2),
        "RSI (14-day)": round(float(latest["RSI"]), 2)
    }

with st.spinner(f"Calculating institutional indicators for {selected_asset}..."):
    summary = calculate_technical_summary(TICKERS[selected_asset])
    if summary:
        st.metric("📈 30-Day Change (%)", f"{summary['30-Day Change (%)']}%")
        st.metric("📉 Volatility (Std Dev)", f"{summary['Volatility (Std Dev)']}%")
        st.metric("🧽 SMA (10-day)", f"{summary['SMA (10-day)']}")
        st.metric("💪 RSI (14-day)", f"{summary['RSI (14-day)']}")
    else:
        st.warning("Could not calculate summary metrics for this asset.")

st.subheader("🌐 Macro Context Panel")

def fetch_fred_data(series_id, months_back=0):
    api_key = os.getenv("FRED_API_KEY")
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 13  # ensure at least 12 months of data
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["observations"]:
            observations = data["observations"]
            try:
                return float(observations[months_back]["value"])
            except:
                return None
    return None

cpi_now = fetch_fred_data("CPIAUCSL", 0)
cpi_last_year = fetch_fred_data("CPIAUCSL", 12)
cpi_yoy = ((cpi_now - cpi_last_year) / cpi_last_year * 100) if cpi_now and cpi_last_year else None

fed_rate = fetch_fred_data("FEDFUNDS", 0)
gdp = fetch_fred_data("GDP", 0)

def get_macro_alerts(cpi_yoy, fed_rate, gdp):
    return [
        {
            "Indicator": "U.S. CPI (YoY)",
            "Value": f"{float(cpi_yoy):.2f}%" if cpi_yoy else "N/A",
            "Insight": (
                "⚠️ Inflation Alert" if cpi_yoy and float(cpi_yoy) > 3
                else "Above Target" if cpi_yoy and float(cpi_yoy) > 2
                else "✅ Stable"
            )
        },
        {
            "Indicator": "Fed Funds Rate",
            "Value": f"{float(fed_rate):.2f}%" if fed_rate else "N/A",
            "Insight": (
                "⚠️ Restrictive" if fed_rate and float(fed_rate) > 5
                else "Neutral" if fed_rate and float(fed_rate) > 3
                else "✅ Accommodative"
            )
        },
        {
            "Indicator": "U.S. GDP (Annualized)",
            "Value": f"${float(gdp):,.2f}B" if gdp else "N/A",
            "Insight": (
                "⚠️ Weak Growth" if gdp and float(gdp) < 1
                else "Moderate" if gdp and float(gdp) < 2
                else "✅ Strong"
            )
        }
    ]

macro_data = get_macro_alerts(cpi_yoy, fed_rate, gdp)
macros_df = pd.DataFrame(macro_data)
with st.expander("View Macro Indicators"):
    st.dataframe(macros_df.set_index("Indicator"), use_container_width=True)

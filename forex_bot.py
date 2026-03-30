import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Forex Analyzer", layout="centered")

st.title("📊 Forex Market Analyzer")
st.write("Real-time basic forex signals (Educational Only)")

st.write(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

pairs = {
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'AUDUSD=X': 'AUD/USD',
    'USDCAD=X': 'USD/CAD',
    'XAUUSD=X:  'XAU/USD'
}

for symbol, name in pairs.items():
    try:
        df = yf.Ticker(symbol).history(period='5d', interval='1h')

        if len(df) < 20:
            st.warning(f"{name}: Not enough data")
            continue

        current = df['Close'].iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        signal = "⚖️ NEUTRAL"
        if current > sma20 and rsi < 70:
            signal = "🟢 BUY"
        elif current < sma20 and rsi > 30:
            signal = "🔴 SELL"

        st.subheader(name)
        st.write(f"💰 Price: {current:.5f}")
        st.write(f"📉 RSI: {rsi:.2f}")
        st.write(f"📊 Signal: {signal}")
        st.markdown("---")

    except Exception as e:
        st.error(f"{name}: Error loading data")

st.warning("⚠️ Educational purposes only. Not financial advice.")

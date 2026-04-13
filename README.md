# 🥇 ScalpBot Pro v2

Beautiful dark-themed trading signal bot for Streamlit Cloud.

## Features
- Dark pro UI with gradient signal cards, badges, score bars
- 7 instruments: Gold, EUR/USD, GBP/USD, USD/JPY, US30, Nasdaq, Silver  
- 6 indicators: RSI + MACD + Stochastic + Bollinger + ATR + Volume
- Multi-timeframe (1H signal + 4H bias confirmation)
- **Auto-send toggle** — sends signals automatically at your chosen interval (1m/2m/5m/10m/15m)
- Live countdown timer showing next signal
- Signal history table with stats (total, buy/sell count, avg confidence)
- Telegram push alerts
- Adjustable risk settings and signal weights

## Deploy in 3 steps

### 1. Push to GitHub
Create a new repo on github.com, then upload these 3 files:
- `app.py`
- `requirements.txt`  
- `README.md`

### 2. Deploy on Streamlit Cloud (free)
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click **New app**
4. Select your repo, branch = `main`, main file = `app.py`
5. Click **Deploy** — live in ~2 minutes

### 3. Configure in the app
- Set your account balance and risk % in the sidebar
- Paste your Telegram bot token and chat ID
- Click **▶ Start Auto** to enable auto-sending

## Getting Telegram credentials
1. Search `@BotFather` in Telegram → `/newbot` → copy the token
2. Search `@userinfobot` → it replies with your chat ID

## Auto-Send feature
- Click **▶ Start Auto** button above the analyze button
- Panel turns green with a live countdown timer
- Bot analyzes the market at your chosen interval and sends signals automatically
- Only sends when a valid signal is found (meets confidence + R/R filters)
- Click **⏹ Stop Auto** to pause at any time

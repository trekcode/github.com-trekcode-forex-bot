import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import requests

st.set_page_config(page_title="Forex Analyzer", layout="wide")

# ============================================
# DEFINE ALL INSTRUMENTS FIRST
# ============================================
pairs = {
    # Forex Pairs
    'EURUSD=X': {'name': 'EUR/USD', 'type': 'Forex', 'decimals': 5},
    'GBPUSD=X': {'name': 'GBP/USD', 'type': 'Forex', 'decimals': 5},
    'USDJPY=X': {'name': 'USD/JPY', 'type': 'Forex', 'decimals': 3},
    'AUDUSD=X': {'name': 'AUD/USD', 'type': 'Forex', 'decimals': 5},
    'USDCAD=X': {'name': 'USD/CAD', 'type': 'Forex', 'decimals': 5},
    'USDCHF=X': {'name': 'USD/CHF', 'type': 'Forex', 'decimals': 5},
    'NZDUSD=X': {'name': 'NZD/USD', 'type': 'Forex', 'decimals': 5},
    
    # Indices
    '^DJI': {'name': '🇺🇸 US30 (Dow Jones)', 'type': 'Index', 'decimals': 2},
    '^NDX': {'name': '🇺🇸 US100 (NASDAQ)', 'type': 'Index', 'decimals': 2},
    '^GSPC': {'name': '🇺🇸 S&P 500', 'type': 'Index', 'decimals': 2},
    
    # Commodities
    'GC=F': {'name': '🥇 Gold (XAU/USD)', 'type': 'Commodity', 'decimals': 2},
    'SI=F': {'name': '🥈 Silver', 'type': 'Commodity', 'decimals': 3},
}

# ============================================
# TELEGRAM NOTIFICATION CONFIGURATION
# ============================================
TELEGRAM_TOKEN = "8773664334:AAE4fd4Wpyd2ZQkWBsjlPby7qSGKp00jGng"
TELEGRAM_CHAT_ID = "2057396237"

# Gold Scalping Bot
GOLD_BOT_TOKEN = "8686418191:AAHtEBJ9Lyehb3geZS1WwWukmYZatqpAe-A"
GOLD_BOT_CHAT_ID = "2057396237"

def send_telegram_message(token, chat_id, message, parse_mode='HTML'):
    """Send message to Telegram using specified bot"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_consolidated_signal(results, min_confidence):
    """Send ONE consolidated message with all strong signals"""
    
    strong_signals = [r for r in results if r['action'] != 'NEUTRAL' and r['confidence'] >= min_confidence]
    
    if not strong_signals:
        return False
    
    current_hour = datetime.now().hour
    if 8 <= current_hour < 16:
        session = "🇬🇧 London Session"
        session_emoji = "🏛️"
    elif 13 <= current_hour < 22:
        session = "🇺🇸 New York Session"
        session_emoji = "🗽"
    else:
        session = "🌏 Asian Session"
        session_emoji = "🌏"
    
    message = f"""
<b>📊 DAILY FOREX SIGNAL REPORT</b>
{session_emoji} {session} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
{'='*40}

<b>🎯 STRONG TRADE SIGNALS FOUND: {len(strong_signals)}</b>

"""
    
    for i, r in enumerate(strong_signals, 1):
        if r['action'] == 'BUY':
            emoji = "🟢"
            action = "BUY"
        else:
            emoji = "🔴"
            action = "SELL"
        
        price_display = r['price_str']
        
        if r['stop_loss'] is not None:
            if r['type'] == 'Forex':
                sl_display = f"{r['stop_loss']:.5f}"
                tp_display = f"{r['take_profit']:.5f}" if r['take_profit'] else 'N/A'
            else:
                sl_display = f"{r['stop_loss']:.2f}"
                tp_display = f"{r['take_profit']:.2f}" if r['take_profit'] else 'N/A'
        else:
            sl_display = "N/A"
            tp_display = "N/A"
        
        rr_display = f"1:{r['risk_reward']}" if r['risk_reward'] else "N/A"
        
        message += f"""
{emoji} <b>#{i} {action} {r['name']}</b>
   └─ 💰 Price: {price_display}
   └─ 🎯 Confidence: {r['confidence']}%
   └─ 📊 RSI: {r['rsi']:.1f}
   └─ 🛑 Stop Loss: {sl_display}
   └─ 🎯 Take Profit: {tp_display}
   └─ 📈 Risk/Reward: {rr_display}
"""
    
    message += f"""
{'='*40}
<b>📝 QUICK TRADING TIPS:</b>
• Risk 1-2% per trade
• Wait for confirmation candle
• Use proper position sizing

<i>⚠️ Educational purposes only - Manage risk!</i>
"""
    
    success1 = send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
    return success1

# ============================================
# GOLD SCALPING FUNCTIONS
# ============================================

def analyze_gold_scalp():
    """Analyze Gold for scalping opportunities using multiple timeframes"""
    try:
        # Fetch data for multiple timeframes
        df_1m = yf.Ticker('GC=F').history(period='1d', interval='1m')  # 1-minute
        df_5m = yf.Ticker('GC=F').history(period='1d', interval='5m')  # 5-minute
        df_15m = yf.Ticker('GC=F').history(period='1d', interval='15m') # 15-minute
        
        if len(df_1m) < 20:
            return None
        
        # Current price
        current = df_1m['Close'].iloc[-1]
        
        # 1-minute indicators
        sma_5_1m = df_1m['Close'].rolling(5).mean().iloc[-1]
        sma_10_1m = df_1m['Close'].rolling(10).mean().iloc[-1]
        sma_20_1m = df_1m['Close'].rolling(20).mean().iloc[-1]
        
        # RSI for 1-minute
        delta = df_1m['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(7).mean()
        rs = gain / loss
        rsi_1m = 100 - (100 / (1 + rs)).iloc[-1]
        
        # ATR for 1-minute
        high_low = df_1m['High'] - df_1m['Low']
        high_close = abs(df_1m['High'] - df_1m['Close'].shift())
        low_close = abs(df_1m['Low'] - df_1m['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr_1m = tr.rolling(7).mean().iloc[-1]
        
        # Volume spike
        volume_sma = df_1m['Volume'].rolling(10).mean().iloc[-1]
        volume_ratio = df_1m['Volume'].iloc[-1] / volume_sma if volume_sma > 0 else 1
        
        # 5-minute indicators
        if len(df_5m) > 5:
            sma_5_5m = df_5m['Close'].rolling(5).mean().iloc[-1]
            sma_10_5m = df_5m['Close'].rolling(10).mean().iloc[-1]
            
            # 5m RSI
            delta_5m = df_5m['Close'].diff()
            gain_5m = (delta_5m.where(delta_5m > 0, 0)).rolling(7).mean()
            loss_5m = (-delta_5m.where(delta_5m < 0, 0)).rolling(7).mean()
            rs_5m = gain_5m / loss_5m
            rsi_5m = 100 - (100 / (1 + rs_5m)).iloc[-1]
        else:
            sma_5_5m = current
            sma_10_5m = current
            rsi_5m = 50
        
        # 15-minute trend
        if len(df_15m) > 5:
            sma_20_15m = df_15m['Close'].rolling(20).mean().iloc[-1]
            trend_15m = "UP" if current > sma_20_15m else "DOWN"
        else:
            trend_15m = "NEUTRAL"
        
        # Scalping signal scoring
        buy_score = 0
        sell_score = 0
        
        # 1-minute EMAs (fast scalping)
        if current > sma_5_1m and current > sma_10_1m:
            buy_score += 2
        elif current < sma_5_1m and current < sma_10_1m:
            sell_score += 2
        
        # RSI for scalping (tighter thresholds)
        if rsi_1m < 25:
            buy_score += 3
        elif rsi_1m > 75:
            sell_score += 3
        elif rsi_1m < 35:
            buy_score += 1
        elif rsi_1m > 65:
            sell_score += 1
        
        # Volume confirmation
        if volume_ratio > 1.5:
            if current > df_1m['Open'].iloc[-1]:
                buy_score += 2
            else:
                sell_score += 2
        
        # 5-minute momentum
        if sma_5_5m > sma_10_5m and rsi_5m < 70:
            buy_score += 1
        elif sma_5_5m < sma_10_5m and rsi_5m > 30:
            sell_score += 1
        
        # 15-minute trend alignment
        if trend_15m == "UP" and current > sma_20_1m:
            buy_score += 1
        elif trend_15m == "DOWN" and current < sma_20_1m:
            sell_score += 1
        
        # Determine signal
        if buy_score > sell_score and buy_score >= 3:
            signal = "BUY"
            confidence = min(95, 55 + (buy_score * 8))
            signal_emoji = "🟢⚡"
            # Tight stops for scalping
            stop_loss = current - (atr_1m * 1.2)
            take_profit = current + (atr_1m * 1.8)
        elif sell_score > buy_score and sell_score >= 3:
            signal = "SELL"
            confidence = min(95, 55 + (sell_score * 8))
            signal_emoji = "🔴⚡"
            stop_loss = current + (atr_1m * 1.2)
            take_profit = current - (atr_1m * 1.8)
        else:
            signal = "NEUTRAL"
            confidence = 0
            signal_emoji = "⏸️"
            stop_loss = None
            take_profit = None
        
        # Calculate risk/reward
        risk_reward = None
        if signal != "NEUTRAL":
            risk = abs(current - stop_loss)
            reward = abs(take_profit - current)
            risk_reward = round(reward / risk, 2) if risk > 0 else 0
        
        return {
            'price': current,
            'price_str': f"${current:.2f}",
            'signal': signal,
            'signal_emoji': signal_emoji,
            'confidence': confidence,
            'rsi_1m': rsi_1m,
            'volume_ratio': volume_ratio,
            'trend_15m': trend_15m,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
            'atr': atr_1m,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        print(f"Gold scalping error: {e}")
        return None

def send_gold_scalp_signal(signal_data):
    """Send gold scalping signal to Telegram"""
    if not signal_data or signal_data['signal'] == 'NEUTRAL':
        return False
    
    s = signal_data
    
    # Determine signal strength emoji
    if s['confidence'] >= 80:
        strength = "🔥 STRONG SCALP"
    elif s['confidence'] >= 65:
        strength = "⚡ SCALP OPPORTUNITY"
    else:
        strength = "📊 SCALP ALERT"
    
    message = f"""
<b>{s['signal_emoji']} GOLD SCALPING SIGNAL</b>

<b>{strength}</b>
<b>Signal:</b> {s['signal']}
<b>Confidence:</b> {s['confidence']}%

<b>💰 Current Price:</b> {s['price_str']}

<b>⚡ SCALPING LEVELS:</b>
• <b>Entry:</b> {s['price_str']}
• <b>Stop Loss:</b> ${s['stop_loss']:.2f}
• <b>Take Profit:</b> ${s['take_profit']:.2f}
• <b>Risk/Reward:</b> 1:{s['risk_reward']}

<b>📊 TECHNICALS:</b>
• <b>RSI (1m):</b> {s['rsi_1m']:.1f}
• <b>Volume Ratio:</b> {s['volume_ratio']:.1f}x
• <b>15m Trend:</b> {s['trend_15m']}
• <b>ATR (1m):</b> ${s['atr']:.2f}

<b>⏰ Time:</b> {s['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} UTC

<i>⚡ Scalping Tip: Quick entry/exit within 1-5 minutes</i>
<i>⚠️ Educational purposes only - High risk!</i>
"""
    
    return send_telegram_message(GOLD_BOT_TOKEN, GOLD_BOT_CHAT_ID, message)

# Custom CSS for notifications
st.markdown("""
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    padding: 15px 20px;
    border-radius: 10px;
    animation: slideIn 0.5s ease-out;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
.buy-notification {
    background: linear-gradient(135deg, #1a472a 0%, #0e2a1a 100%);
    border-left: 5px solid #00ff00;
    color: white;
}
.sell-notification {
    background: linear-gradient(135deg, #471a1a 0%, #2a0e0e 100%);
    border-left: 5px solid #ff4444;
    color: white;
}
.scalp-buy {
    background: linear-gradient(135deg, #2a5a2a 0%, #1a3a1a 100%);
    border-left: 5px solid #ffff00;
    color: white;
}
.scalp-sell {
    background: linear-gradient(135deg, #5a2a2a 0%, #3a1a1a 100%);
    border-left: 5px solid #ffaa00;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Forex & Indices Market Analyzer")
st.write("Daily consolidated signals + Gold Scalping Bot (Educational Only)")

# Initialize session state
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = {}
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'last_signal_sent' not in st.session_state:
    st.session_state.last_signal_sent = None
if 'last_daily_summary' not in st.session_state:
    st.session_state.last_daily_summary = None
if 'scalp_mode_enabled' not in st.session_state:
    st.session_state.scalp_mode_enabled = False
if 'last_scalp_signal' not in st.session_state:
    st.session_state.last_scalp_signal = None
if 'scalp_signal_count' not in st.session_state:
    st.session_state.scalp_signal_count = 0

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh (every 60 seconds)", 
                                                 value=st.session_state.auto_refresh)
    
    st.markdown("---")
    
    # ============================================
    # GOLD SCALPING SECTION
    # ============================================
    st.header("🥇 GOLD SCALPING MODE")
    
    # Big toggle button for scalp mode
    scalp_toggle = st.toggle(
        "⚡ ENABLE GOLD SCALPING MODE", 
        value=st.session_state.scalp_mode_enabled,
        help="When enabled, you'll receive frequent gold scalping signals (every 1-5 minutes). Turn OFF to avoid overwhelming messages."
    )
    
    if scalp_toggle != st.session_state.scalp_mode_enabled:
        st.session_state.scalp_mode_enabled = scalp_toggle
        if scalp_toggle:
            st.success("✅ Gold Scalping Mode ACTIVATED! You'll receive quick scalp signals.")
            send_telegram_message(GOLD_BOT_TOKEN, GOLD_BOT_CHAT_ID, 
                "⚡ <b>Gold Scalping Mode ACTIVATED!</b>\n\nYou will now receive frequent gold scalp signals.\n\nTurn off in settings to stop.")
        else:
            st.warning("⏸️ Gold Scalping Mode DEACTIVATED")
            send_telegram_message(GOLD_BOT_TOKEN, GOLD_BOT_CHAT_ID, 
                "⏸️ <b>Gold Scalping Mode DEACTIVATED</b>\n\nYou will no longer receive scalp signals.\n\nTurn on in settings to resume.")
    
    # Scalping parameters
    if st.session_state.scalp_mode_enabled:
        st.subheader("⚡ Scalping Parameters")
        min_scalp_confidence = st.slider("Min Scalp Confidence", 50, 90, 60, key="min_scalp_conf")
        scalp_frequency = st.selectbox("Scalp Signal Frequency", 
                                       ["Every minute", "Every 2 minutes", "Every 5 minutes"], 
                                       index=1)
        
        st.info(f"""
        ⚡ **Scalping Mode Active**
        • Signals every {scalp_frequency}
        • Min Confidence: {min_scalp_confidence}%
        • Tight stops (1.2x ATR)
        • Fast RSI (7-period)
        """)
        
        # Manual scalp check button
        if st.button("🔍 Check Gold Scalp NOW", use_container_width=True):
            with st.spinner("Analyzing gold for scalp opportunities..."):
                scalp_signal = analyze_gold_scalp()
                if scalp_signal:
                    if scalp_signal['confidence'] >= min_scalp_confidence:
                        send_gold_scalp_signal(scalp_signal)
                        st.success("✅ Scalp signal sent to Telegram!")
                    else:
                        st.info(f"⚠️ Signal confidence {scalp_signal['confidence']}% below {min_scalp_confidence}% threshold")
                else:
                    st.error("Error analyzing gold")
    
    st.markdown("---")
    
    # Main bot settings
    st.subheader("📱 Main Bot Settings")
    st.info(f"Main Bot: @{TELEGRAM_TOKEN.split(':')[0]}")
    
    if st.button("📨 Test Main Bot", use_container_width=True):
        test_msg = f"✅ Main Bot Online! Monitoring {len(pairs)} instruments"
        if send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, test_msg):
            st.success("✅ Test message sent!")
        else:
            st.error("❌ Failed to send")
    
    if st.button("🥇 Test Gold Scalp Bot", use_container_width=True):
        test_msg = "⚡ Gold Scalp Bot Online! Send a test scalp signal?"
        if send_telegram_message(GOLD_BOT_TOKEN, GOLD_BOT_CHAT_ID, test_msg):
            st.success("✅ Test message sent to Gold Bot!")
        else:
            st.error("❌ Failed to send")
    
    st.markdown("---")
    
    # Notification settings
    st.subheader("🔔 Signal Settings")
    min_confidence_notify = st.slider("Minimum confidence for main signals", 50, 90, 65)
    send_consolidated = st.checkbox("📦 Send ONE consolidated signal message", value=True)
    send_end_of_day = st.checkbox("📅 Send End-of-Day Summary", value=True)
    
    # Signal frequency
    st.subheader("⏰ Main Bot Frequency")
    signal_mode = st.radio("When to send main signals:", 
                          ["Daily (Once per day)", "Every 4 hours", "On every signal change"])
    
    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.caption(f"🥇 Gold Scalping: {'🟢 ACTIVE' if st.session_state.scalp_mode_enabled else '⚪ INACTIVE'}")

# Display current time
current_time = datetime.now()
st.write(f"⏰ Last update: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
if st.session_state.auto_refresh:
    st.info("🔄 Auto-refresh enabled - Page updates every 60 seconds")

# ============================================
# GOLD SCALPING ANALYSIS (if enabled)
# ============================================
if st.session_state.scalp_mode_enabled:
    # Get scalp frequency in seconds
    if scalp_frequency == "Every minute":
        scalp_interval = 60
    elif scalp_frequency == "Every 2 minutes":
        scalp_interval = 120
    else:
        scalp_interval = 300
    
    # Check if it's time for a scalp signal
    current_minute = datetime.now().minute
    if scalp_frequency == "Every minute":
        should_scalp = True
    elif scalp_frequency == "Every 2 minutes":
        should_scalp = current_minute % 2 == 0
    else:
        should_scalp = current_minute % 5 == 0
    
    if should_scalp and st.session_state.last_scalp_signal != datetime.now().strftime('%Y-%m-%d %H:%M'):
        st.session_state.last_scalp_signal = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        with st.spinner("Analyzing gold for scalp opportunities..."):
            scalp_signal = analyze_gold_scalp()
            if scalp_signal:
                if scalp_signal['confidence'] >= min_scalp_confidence:
                    send_gold_scalp_signal(scalp_signal)
                    st.session_state.scalp_signal_count += 1
                    st.toast(f"⚡ Gold scalp signal sent! (Confidence: {scalp_signal['confidence']}%)")
                else:
                    # Low confidence - no signal sent
                    pass

# ============================================
# MAIN ANALYSIS FUNCTION
# ============================================
def analyze_instrument(symbol, instrument_info):
    """Analyze a single instrument and return signal data"""
    try:
        name = instrument_info['name']
        instrument_type = instrument_info['type']
        
        # Adjust period based on instrument type
        if instrument_type == 'Index':
            df = yf.Ticker(symbol).history(period='1mo', interval='1h')
        elif instrument_type == 'Commodity':
            df = yf.Ticker(symbol).history(period='1wk', interval='1h')
        else:
            df = yf.Ticker(symbol).history(period='5d', interval='1h')

        if len(df) < 20:
            return None

        current = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma20
        
        # RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD Calculation
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_histogram = (macd - macd_signal).iloc[-1]
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        # Signal scoring
        buy_score = 0
        sell_score = 0
        
        if current > sma20:
            buy_score += 1
        else:
            sell_score += 1
        
        if sma20 > sma50:
            buy_score += 1
        else:
            sell_score += 1
        
        if rsi < 30:
            buy_score += 2
        elif rsi > 70:
            sell_score += 2
        elif rsi < 45:
            buy_score += 1
        elif rsi > 55:
            sell_score += 1
        
        if macd_histogram > 0:
            buy_score += 1
        else:
            sell_score += 1
        
        if buy_score > sell_score and buy_score >= 2:
            signal = "🟢 BUY"
            action = "BUY"
            confidence = min(90, 50 + (buy_score * 10))
            signal_strength = "Strong" if buy_score >= 4 else "Moderate"
            stop_loss = current - (atr * 1.5)
            take_profit = current + (atr * 2.5)
        elif sell_score > buy_score and sell_score >= 2:
            signal = "🔴 SELL"
            action = "SELL"
            confidence = min(90, 50 + (sell_score * 10))
            signal_strength = "Strong" if sell_score >= 4 else "Moderate"
            stop_loss = current + (atr * 1.5)
            take_profit = current - (atr * 2.5)
        else:
            signal = "⚖️ NEUTRAL"
            action = "NEUTRAL"
            confidence = 0
            signal_strength = "None"
            stop_loss = None
            take_profit = None
        
        risk_reward = None
        if action != "NEUTRAL":
            risk = abs(current - stop_loss)
            reward = abs(take_profit - current)
            risk_reward = round(reward / risk, 2) if risk > 0 else 0
        
        price_change = ((current - prev_close) / prev_close) * 100
        
        decimals = instrument_info['decimals']
        if decimals == 2:
            price_str = f"{current:,.2f}"
        elif decimals == 3:
            price_str = f"{current:.3f}"
        else:
            price_str = f"{current:.5f}"
        
        return {
            'symbol': symbol,
            'name': name,
            'type': instrument_type,
            'price': current,
            'price_str': price_str,
            'price_change': price_change,
            'signal': signal,
            'action': action,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'rsi': rsi,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
        }
        
    except Exception as e:
        return None

# Analyze all instruments
with st.spinner("Analyzing markets..."):
    results = []
    for symbol, info in pairs.items():
        result = analyze_instrument(symbol, info)
        if result:
            results.append(result)

# Main bot consolidated messages
current_hour = datetime.now().hour
current_day = datetime.now().strftime('%Y-%m-%d')

should_send = False

if signal_mode == "Daily (Once per day)":
    if current_hour in [8, 14] and st.session_state.last_signal_sent != current_day + str(current_hour):
        should_send = True
        st.session_state.last_signal_sent = current_day + str(current_hour)
elif signal_mode == "Every 4 hours":
    if current_hour % 4 == 0 and st.session_state.last_signal_sent != current_day + str(current_hour):
        should_send = True
        st.session_state.last_signal_sent = current_day + str(current_hour)
else:
    for r in results:
        prev = st.session_state.previous_signals.get(r['symbol'], {})
        if prev.get('action') != r['action'] and r['action'] != 'NEUTRAL':
            should_send = True
            break

if should_send and send_consolidated:
    send_consolidated_signal(results, min_confidence_notify)
    st.success("📱 Consolidated signal report sent to Telegram!")

if send_end_of_day and current_hour == 21 and st.session_state.last_daily_summary != current_day:
    total_signals = len([r for r in results if r['action'] != 'NEUTRAL'])
    buy_signals = len([r for r in results if r['action'] == 'BUY'])
    sell_signals = len([r for r in results if r['action'] == 'SELL'])
    
    summary = f"""
<b>📅 DAILY TRADING SUMMARY</b>
📊 Date: {datetime.now().strftime('%Y-%m-%d')}
{'='*30}

<b>📈 Signal Statistics:</b>
• Total Signals: {total_signals}
• 🟢 BUY Signals: {buy_signals}
• 🔴 SELL Signals: {sell_signals}

<b>🥇 Gold Scalping Stats:</b>
• Signals Today: {st.session_state.scalp_signal_count}
• Mode: {'ACTIVE' if st.session_state.scalp_mode_enabled else 'INACTIVE'}

<i>⚠️ Educational purposes only</i>
"""
    send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, summary)
    st.session_state.last_daily_summary = current_day
    st.info("📅 End-of-day summary sent to Telegram!")

# Update previous signals
for r in results:
    st.session_state.previous_signals[r['symbol']] = {
        'action': r['action'],
        'confidence': r['confidence']
    }

# ============================================
# DISPLAY TRADE SIGNALS TABLE
# ============================================
st.markdown("## 🎯 STRONG TRADE SIGNALS")
st.markdown("### What to Buy / Sell Today")

actionable_signals = [r for r in results if r['action'] != 'NEUTRAL' and r['confidence'] >= min_confidence_notify]

if actionable_signals:
    for r in actionable_signals:
        if r['action'] == 'BUY':
            card_color = "#1a472a"
            border_color = "#00ff00"
        else:
            card_color = "#471a1a"
            border_color = "#ff4444"
        
        if r['stop_loss'] is not None:
            if r['type'] == 'Forex':
                sl_display = f"{r['stop_loss']:.5f}"
                tp_display = f"{r['take_profit']:.5f}" if r['take_profit'] else "N/A"
            else:
                sl_display = f"{r['stop_loss']:.2f}"
                tp_display = f"{r['take_profit']:.2f}" if r['take_profit'] else "N/A"
        else:
            sl_display = "N/A"
            tp_display = "N/A"
        
        rr_display = f"1:{r['risk_reward']}" if r['risk_reward'] else "N/A"
        
        st.markdown(f"""
        <div style="background: {card_color}; border-left: 5px solid {border_color}; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <h2>{r['signal']} {r['name']}</h2>
            <table style="width: 100%;">
                <tr>
                    <td><b>💰 Price:</b> {r['price_str']}</td>
                    <td><b>🎯 Confidence:</b> {r['confidence']}%</td>
                    <td><b>📊 RSI:</b> {r['rsi']:.1f}</td>
                </tr>
                <tr>
                    <td><b>🛑 Stop Loss:</b> {sl_display}</td>
                    <td><b>🎯 Take Profit:</b> {tp_display}</td>
                    <td><b>📈 Risk/Reward:</b> {rr_display}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    st.success(f"📱 **Telegram Notification**: A consolidated message with all {len(actionable_signals)} signals has been sent to your Telegram bot.")
else:
    st.info(f"⚖️ No strong trade signals above {min_confidence_notify}% confidence at this time.")

# ============================================
# GOLD SCALPING STATUS CARD
# ============================================
st.markdown("## ⚡ GOLD SCALPING STATUS")

col1, col2, col3 = st.columns(3)

with col1:
    status_color = "🟢" if st.session_state.scalp_mode_enabled else "⚪"
    st.metric("Scalp Mode", f"{status_color} {'ACTIVE' if st.session_state.scalp_mode_enabled else 'INACTIVE'}")

with col2:
    st.metric("Signals Today", st.session_state.scalp_signal_count)

with col3:
    if st.session_state.scalp_mode_enabled:
        st.metric("Frequency", scalp_frequency)
    else:
        st.metric("Status", "Click toggle to enable")

if st.session_state.scalp_mode_enabled:
    st.info("⚡ **Gold Scalping Mode ACTIVE** - You will receive frequent scalp signals on Telegram. Turn OFF in sidebar to stop.")

# ============================================
# MARKET OVERVIEW
# ============================================
st.markdown("## 📊 MARKET OVERVIEW")

overview_df = pd.DataFrame([
    {
        'Instrument': r['name'],
        'Type': r['type'],
        'Price': r['price_str'],
        'Change %': f"{r['price_change']:+.2f}%",
        'Signal': r['signal'],
        'Confidence': f"{r['confidence']}%" if r['confidence'] > 0 else '-',
        'RSI': f"{r['rsi']:.1f}"
    }
    for r in results
])

st.dataframe(overview_df, use_container_width=True, hide_index=True)

# ============================================
# SUMMARY STATISTICS
# ============================================
st.markdown("## 📊 SUMMARY STATISTICS")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    buy_signals = len([r for r in results if r['action'] == 'BUY' and r['confidence'] >= min_confidence_notify])
    st.metric("🟢 BUY Signals", buy_signals)

with col2:
    sell_signals = len([r for r in results if r['action'] == 'SELL' and r['confidence'] >= min_confidence_notify])
    st.metric("🔴 SELL Signals", sell_signals)

with col3:
    neutral = len([r for r in results if r['action'] == 'NEUTRAL'])
    st.metric("⚖️ Neutral", neutral)

with col4:
    strong_signals = [r for r in results if r['confidence'] > 0]
    avg_confidence = sum(r['confidence'] for r in strong_signals) / len(strong_signals) if strong_signals else 0
    st.metric("Avg Confidence", f"{avg_confidence:.0f}%")

with col5:
    st.metric("🥇 Scalp Signals", st.session_state.scalp_signal_count)

# ============================================
# AUTO-REFRESH LOGIC
# ============================================
if st.session_state.auto_refresh:
    st.markdown("---")
    st.info("🔄 Auto-refresh enabled - Page will reload in 60 seconds...")
    time.sleep(60)
    st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚠️ <b>Educational purposes only</b> - Not financial advice</p>
    <p>📊 Main Bot: Daily consolidated signals | ⚡ Gold Bot: Scalping signals (toggle on/off)</p>
    <p>🥇 <b>Gold Scalping Mode:</b> Toggle ON in sidebar for frequent scalp signals (1-5 minute intervals)</p>
    <p>🔄 Enable auto-refresh for continuous monitoring</p>
</div>
""", unsafe_allow_html=True)

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
# DEFINE ALL INSTRUMENTS FIRST (BEFORE USING THEM)
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
# Your Telegram credentials
TELEGRAM_TOKEN = "8773664334:AAE4fd4Wpyd2ZQkWBsjlPby7qSGKp00jGng"
TELEGRAM_CHAT_ID = "2057396237"

# Gold-Only Bot (Optional - separate bot for gold)
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
    
    # Filter strong signals
    strong_signals = [r for r in results if r['action'] != 'NEUTRAL' and r['confidence'] >= min_confidence]
    
    if not strong_signals:
        return False
    
    # Get market session
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
    
    # Build consolidated message
    message = f"""
<b>📊 DAILY FOREX SIGNAL REPORT</b>
{session_emoji} {session} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
{'='*40}

<b>🎯 STRONG TRADE SIGNALS FOUND: {len(strong_signals)}</b>

"""
    
    # Add each signal
    for i, r in enumerate(strong_signals, 1):
        if r['action'] == 'BUY':
            emoji = "🟢"
            action = "BUY"
        else:
            emoji = "🔴"
            action = "SELL"
        
        # Format price and trade levels safely
        price_display = r['price_str']
        
        # Safely format stop loss and take profit
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
        
        # Safely format risk/reward
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
    
    # Add trading tips
    message += f"""
{'='*40}
<b>📝 QUICK TRADING TIPS:</b>
• Risk 1-2% per trade
• Wait for confirmation candle
• Use proper position sizing
• Set alerts at key levels

<i>⚠️ Educational purposes only - Manage risk!</i>
"""
    
    # Send to main bot
    success1 = send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
    
    # Also send gold signals to gold bot if any
    gold_signals = [r for r in strong_signals if 'Gold' in r['name']]
    if gold_signals and GOLD_BOT_TOKEN:
        gold_message = f"""
<b>🥇 GOLD DAILY SIGNAL REPORT</b>
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
{'='*30}

<b>🎯 GOLD SIGNALS: {len(gold_signals)}</b>
"""
        for i, r in enumerate(gold_signals, 1):
            if r['action'] == 'BUY':
                emoji = "🟢"
            else:
                emoji = "🔴"
            
            sl_display = f"{r['stop_loss']:.2f}" if r['stop_loss'] else "N/A"
            tp_display = f"{r['take_profit']:.2f}" if r['take_profit'] else "N/A"
            
            gold_message += f"""
{emoji} <b>#{i} {r['action']} {r['name']}</b>
   └─ 💰 Price: {r['price_str']}
   └─ 🎯 Confidence: {r['confidence']}%
   └─ 📊 RSI: {r['rsi']:.1f}
   └─ 🛑 Stop: {sl_display}
   └─ 🎯 Target: {tp_display}
"""
        
        gold_message += "\n<i>⚠️ Educational purposes only</i>"
        send_telegram_message(GOLD_BOT_TOKEN, GOLD_BOT_CHAT_ID, gold_message)
    
    return success1

def send_daily_summary(results):
    """Send daily summary at end of day"""
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
• ⚖️ Neutral: {len(results) - total_signals}

<b>🎯 Best Signal:</b>
"""
    
    # Find best signal
    strong_signals = [r for r in results if r['action'] != 'NEUTRAL' and r['confidence'] > 0]
    best = max(strong_signals, key=lambda x: x['confidence']) if strong_signals else None
    
    if best:
        summary += f"""
• Instrument: {best['name']}
• Action: {best['action']}
• Confidence: {best['confidence']}%
• Risk/Reward: 1:{best['risk_reward'] if best['risk_reward'] else 'N/A'}
"""
    else:
        summary += "• No strong signals today\n"
    
    summary += "\n<i>⚠️ Educational purposes only</i>"
    
    return summary

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
.neutral-notification {
    background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
    border-left: 5px solid #ffaa00;
    color: white;
}
.notification-close {
    float: right;
    cursor: pointer;
    margin-left: 15px;
    color: #888;
}
.notification-close:hover {
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Forex & Indices Market Analyzer")
st.write("Daily consolidated trading signals with Telegram notifications (Educational Only)")

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

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh (every 60 seconds)", 
                                                 value=st.session_state.auto_refresh)
    
    # Telegram settings
    st.subheader("📱 Telegram Notifications")
    st.info(f"Main Bot: @{TELEGRAM_TOKEN.split(':')[0]}")
    
    # Test Telegram button
    if st.button("📨 Send Test Consolidated Message", use_container_width=True):
        test_msg = f"""
<b>✅ Forex Bot is Online!</b>

📊 <b>System Status:</b>
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Monitoring: {len(pairs)} instruments
• Mode: Consolidated Daily Signals

<i>You will receive ONE daily message with all strong signals</i>
        """
        if send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, test_msg):
            st.success("✅ Test message sent! Check your Telegram!")
        else:
            st.error("❌ Failed to send. Check your token and chat ID.")
    
    st.markdown("---")
    
    # Notification settings
    st.subheader("🔔 Signal Settings")
    min_confidence_notify = st.slider("Minimum confidence for signals", 50, 90, 65)
    send_consolidated = st.checkbox("📦 Send ONE consolidated signal message", value=True)
    send_end_of_day = st.checkbox("📅 Send End-of-Day Summary", value=True)
    
    # Signal frequency
    st.subheader("⏰ Signal Frequency")
    signal_mode = st.radio("When to send signals:", 
                          ["Daily (Once per day)", "Every 4 hours", "On every signal change"])
    
    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.info("📊 Signals are consolidated into one daily message for day trading")

# Display current time
current_time = datetime.now()
st.write(f"⏰ Last update: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
if st.session_state.auto_refresh:
    st.info("🔄 Auto-refresh enabled - Page updates every 60 seconds")

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

        # Calculate indicators
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
        
        # ATR for volatility
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        atr_percent = (atr / current) * 100
        
        # Determine signal with scoring
        buy_score = 0
        sell_score = 0
        
        # Price vs SMA20
        if current > sma20:
            buy_score += 1
        else:
            sell_score += 1
        
        # SMA20 vs SMA50 (trend)
        if sma20 > sma50:
            buy_score += 1
        else:
            sell_score += 1
        
        # RSI signals
        if rsi < 30:
            buy_score += 2
        elif rsi > 70:
            sell_score += 2
        elif rsi < 45:
            buy_score += 1
        elif rsi > 55:
            sell_score += 1
        
        # MACD signals
        if macd_histogram > 0:
            buy_score += 1
        else:
            sell_score += 1
        
        # Determine final signal
        if buy_score > sell_score and buy_score >= 2:
            signal = "🟢 BUY"
            action = "BUY"
            confidence = min(90, 50 + (buy_score * 10))
            signal_strength = "Strong" if buy_score >= 4 else "Moderate"
        elif sell_score > buy_score and sell_score >= 2:
            signal = "🔴 SELL"
            action = "SELL"
            confidence = min(90, 50 + (sell_score * 10))
            signal_strength = "Strong" if sell_score >= 4 else "Moderate"
        else:
            signal = "⚖️ NEUTRAL"
            action = "NEUTRAL"
            confidence = 0
            signal_strength = "None"
        
        # Calculate trade levels for signals
        stop_loss = None
        take_profit = None
        risk_reward = None
        
        if action != "NEUTRAL":
            if action == "BUY":
                stop_loss = current - (atr * 1.5)
                take_profit = current + (atr * 2.5)
            else:
                stop_loss = current + (atr * 1.5)
                take_profit = current - (atr * 2.5)
            
            risk = abs(current - stop_loss)
            reward = abs(take_profit - current)
            risk_reward = round(reward / risk, 2) if risk > 0 else 0
        
        # Price change
        price_change = ((current - prev_close) / prev_close) * 100
        
        # Format price based on instrument
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
            'sma20': sma20,
            'sma50': sma50,
            'macd_histogram': macd_histogram,
            'atr': atr,
            'atr_percent': atr_percent,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
            'buy_score': buy_score,
            'sell_score': sell_score
        }
        
    except Exception as e:
        st.error(f"{name}: Error - {str(e)}")
        return None

# Analyze all instruments
with st.spinner("Analyzing markets..."):
    results = []
    for symbol, info in pairs.items():
        result = analyze_instrument(symbol, info)
        if result:
            results.append(result)

# Check for signal changes and send consolidated messages
current_hour = datetime.now().hour
current_day = datetime.now().strftime('%Y-%m-%d')

# Determine if we should send signals based on frequency
should_send = False

if signal_mode == "Daily (Once per day)":
    # Send once per day at 8:00 AM and 2:00 PM (key trading times)
    if current_hour in [8, 14] and st.session_state.last_signal_sent != current_day + str(current_hour):
        should_send = True
        st.session_state.last_signal_sent = current_day + str(current_hour)
        
elif signal_mode == "Every 4 hours":
    # Send at 0, 4, 8, 12, 16, 20 hours
    if current_hour % 4 == 0 and st.session_state.last_signal_sent != current_day + str(current_hour):
        should_send = True
        st.session_state.last_signal_sent = current_day + str(current_hour)
        
else:  # On every signal change
    # Check if any signal changed
    for r in results:
        prev = st.session_state.previous_signals.get(r['symbol'], {})
        if prev.get('action') != r['action'] and r['action'] != 'NEUTRAL':
            should_send = True
            break

# Send consolidated message if needed
if should_send and send_consolidated:
    send_consolidated_signal(results, min_confidence_notify)
    st.success("📱 Consolidated signal report sent to Telegram!")

# Send end-of-day summary
if send_end_of_day and current_hour == 21 and st.session_state.last_daily_summary != current_day:
    summary = send_daily_summary(results)
    send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, summary)
    st.session_state.last_daily_summary = current_day
    st.info("📅 End-of-day summary sent to Telegram!")

# Update previous signals
for r in results:
    st.session_state.previous_signals[r['symbol']] = {
        'action': r['action'],
        'confidence': r['confidence']
    }

# Clean old sent signals
if len(st.session_state.previous_signals) > 200:
    st.session_state.previous_signals = dict(list(st.session_state.previous_signals.items())[-200:])

# Check for signal changes and create on-screen notifications
new_notifications = []

for r in results:
    symbol_key = r['symbol']
    current_signal = r['action']
    current_confidence = r['confidence']
    
    if symbol_key in st.session_state.previous_signals:
        prev_signal = st.session_state.previous_signals[symbol_key]['action']
        prev_confidence = st.session_state.previous_signals[symbol_key]['confidence']
        
        # Check if signal changed
        if prev_signal != current_signal and current_signal != 'NEUTRAL':
            if current_signal == 'BUY':
                notification = {
                    'type': 'buy',
                    'message': f"🟢 BUY SIGNAL for {r['name']}! Confidence: {current_confidence}%",
                    'instrument': r['name'],
                    'price': r['price_str'],
                    'stop_loss': r['stop_loss'],
                    'take_profit': r['take_profit']
                }
                new_notifications.append(notification)
            elif current_signal == 'SELL':
                notification = {
                    'type': 'sell',
                    'message': f"🔴 SELL SIGNAL for {r['name']}! Confidence: {current_confidence}%",
                    'instrument': r['name'],
                    'price': r['price_str'],
                    'stop_loss': r['stop_loss'],
                    'take_profit': r['take_profit']
                }
                new_notifications.append(notification)

# Add new notifications to session state
if new_notifications:
    st.session_state.notifications = new_notifications + st.session_state.notifications
    st.session_state.notifications = st.session_state.notifications[:20]

# Display notifications using HTML/JS
if st.session_state.notifications:
    notification_html = ""
    for i, notif in enumerate(st.session_state.notifications[:5]):
        if notif['type'] == 'buy':
            notif_class = "buy-notification"
        elif notif['type'] == 'sell':
            notif_class = "sell-notification"
        else:
            notif_class = "neutral-notification"
        
        notification_html += f"""
        <div class="notification {notif_class}" id="notif_{i}">
            <strong>{notif['message']}</strong><br>
            <small>Price: {notif.get('price', 'N/A')}</small>
            <span class="notification-close" onclick="document.getElementById('notif_{i}').remove()">✕</span>
        </div>
        """
    
    st.markdown(f"""
    <div id="notification-container">
        {notification_html}
    </div>
    <script>
        setTimeout(function() {{
            var notifications = document.querySelectorAll('.notification');
            notifications.forEach(function(notif) {{
                notif.remove();
            }});
        }}, 10000);
    </script>
    """, unsafe_allow_html=True)

# ============================================
# DISPLAY TRADE SIGNALS TABLE
# ============================================
st.markdown("## 🎯 STRONG TRADE SIGNALS")
st.markdown("### What to Buy / Sell Today")

# Filter actionable signals
actionable_signals = [r for r in results if r['action'] != 'NEUTRAL' and r['confidence'] >= min_confidence_notify]

if actionable_signals:
    # Display as cards for better visibility
    for r in actionable_signals:
        if r['action'] == 'BUY':
            card_color = "#1a472a"
            border_color = "#00ff00"
        else:
            card_color = "#471a1a"
            border_color = "#ff4444"
        
        # Safely format stop loss and take profit
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
    
    # Show consolidated message preview
    st.success(f"📱 **Telegram Notification**: A consolidated message with all {len(actionable_signals)} signals has been sent to your Telegram bot.")
    
else:
    st.info(f"⚖️ No strong trade signals above {min_confidence_notify}% confidence at this time.")

# ============================================
# MARKET OVERVIEW TABLE
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
    st.metric("📱 Next Report", signal_mode.replace("Every ", "").replace("On ", ""))

# Signal mode info
st.info(f"📱 **Signal Mode:** {signal_mode} - You will receive ONE consolidated message with all strong signals")

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
    <p>📊 Signals based on: RSI, MACD, Moving Averages, and Volatility (ATR)</p>
    <p>📱 <b>One consolidated Telegram message</b> sent daily with all strong signals</p>
    <p>🔄 Enable auto-refresh in sidebar for live updates</p>
</div>
""", unsafe_allow_html=True)

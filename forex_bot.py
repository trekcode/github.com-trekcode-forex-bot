import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import time
import json
import requests

st.set_page_config(page_title="Forex Analyzer", layout="wide")

# ============================================
# TELEGRAM NOTIFICATION CONFIGURATION
# ============================================
# Your Telegram credentials
TELEGRAM_TOKEN = "8773664334:AAE4fd4Wpyd2ZQkWBsjlPby7qSGKp00jGng"
TELEGRAM_CHAT_ID = "2057396237"

def send_telegram_message(message, parse_mode='HTML'):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Telegram error: {e}")
        return False

def send_telegram_signal(instrument, signal, price, confidence, stop_loss, take_profit, rsi):
    """Send formatted trade signal to Telegram"""
    
    # Choose emoji based on signal
    if signal == "BUY":
        emoji = "🟢"
        action = "BUY"
        border = "🟢"
    elif signal == "SELL":
        emoji = "🔴"
        action = "SELL"
        border = "🔴"
    else:
        return
    
    # Format the message with HTML
    message = f"""
<b>{emoji} {action} SIGNAL!</b>

<b>📊 Instrument:</b> {instrument}
<b>💰 Price:</b> {price}
<b>🎯 Confidence:</b> {confidence}%
<b>📈 RSI:</b> {rsi:.1f}

<b>📋 Trade Plan:</b>
• <b>Entry:</b> {price}
• <b>Stop Loss:</b> {stop_loss}
• <b>Take Profit:</b> {take_profit}

<b>⏰ Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>⚠️ Educational purposes only</i>
    """.strip()
    
    # Send the message
    success = send_telegram_message(message)
    
    if success:
        st.success(f"📱 Telegram notification sent for {instrument} {signal} signal!")
    else:
        st.error(f"❌ Failed to send Telegram notification")
    
    return success

# ============================================
# TEST BUTTON IN SIDEBAR
# ============================================

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
st.write("Real-time trading signals with Telegram notifications (Educational Only)")

# Initialize session state for notifications
if 'previous_signals' not in st.session_state:
    st.session_state.previous_signals = {}
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'telegram_sent' not in st.session_state:
    st.session_state.telegram_sent = set()  # Track sent signals to avoid duplicates

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh (every 60 seconds)", 
                                                 value=st.session_state.auto_refresh)
    
    # Telegram settings
    st.subheader("📱 Telegram Notifications")
    st.info(f"Bot: @{TELEGRAM_TOKEN.split(':')[0]}")
    st.caption(f"Chat ID: {TELEGRAM_CHAT_ID}")
    
    # Test Telegram button
    if st.button("📨 Send Test Telegram Message", use_container_width=True):
        test_msg = f"✅ <b>Forex Bot is Online!</b>\n\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n📊 Monitoring {len(pairs)} instruments\n🎯 Min Confidence: {min_confidence_notify}%\n\n🔔 You will receive signals here when they appear!"
        if send_telegram_message(test_msg):
            st.success("✅ Test message sent! Check your Telegram!")
        else:
            st.error("❌ Failed to send. Check your token and chat ID.")
    
    st.markdown("---")
    
    # Notification settings
    st.subheader("🔔 Signal Settings")
    notify_buy = st.checkbox("🔔 Notify on BUY signals", value=True)
    notify_sell = st.checkbox("🔔 Notify on SELL signals", value=True)
    notify_signal_change = st.checkbox("🔔 Notify on SIGNAL CHANGES", value=True)
    
    min_confidence_notify = st.slider("Minimum confidence for notifications", 50, 90, 65)
    
    # Sound alerts
    sound_alerts = st.checkbox("🔊 Play sound on new signals", value=False)
    
    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.info("📊 Signals update every minute when auto-refresh is enabled")

# Display current time
current_time = datetime.now()
st.write(f"⏰ Last update: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
if st.session_state.auto_refresh:
    st.info("🔄 Auto-refresh enabled - Page updates every 60 seconds")

# Define all instruments
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

# Check for signal changes and send Telegram notifications
for r in results:
    if r['action'] != 'NEUTRAL' and r['confidence'] >= min_confidence_notify:
        # Create a unique key for this signal
        signal_key = f"{r['symbol']}_{r['action']}_{r['confidence']}"
        
        # Check if this signal was already sent
        if signal_key not in st.session_state.telegram_sent:
            # Check if signal changed from previous
            prev = st.session_state.previous_signals.get(r['symbol'], {})
            
            if prev.get('action') != r['action']:
                # Send Telegram notification
                if r['action'] == 'BUY' and notify_buy:
                    send_telegram_signal(
                        r['name'],
                        r['action'],
                        r['price_str'],
                        r['confidence'],
                        f"{r['stop_loss']:.5f}",
                        f"{r['take_profit']:.5f}",
                        r['rsi']
                    )
                    st.session_state.telegram_sent.add(signal_key)
                    
                elif r['action'] == 'SELL' and notify_sell:
                    send_telegram_signal(
                        r['name'],
                        r['action'],
                        r['price_str'],
                        r['confidence'],
                        f"{r['stop_loss']:.5f}",
                        f"{r['take_profit']:.5f}",
                        r['rsi']
                    )
                    st.session_state.telegram_sent.add(signal_key)
    
    # Update previous signals
    st.session_state.previous_signals[r['symbol']] = {
        'action': r['action'],
        'confidence': r['confidence']
    }

# Clean old sent signals (keep last 100)
if len(st.session_state.telegram_sent) > 100:
    st.session_state.telegram_sent = set(list(st.session_state.telegram_sent)[-100:])

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
        if prev_signal != current_signal:
            if current_signal == 'BUY' and notify_buy:
                notification = {
                    'type': 'buy',
                    'message': f"🟢 BUY SIGNAL for {r['name']}! Confidence: {current_confidence}%",
                    'instrument': r['name'],
                    'price': r['price_str'],
                    'stop_loss': r['stop_loss'],
                    'take_profit': r['take_profit']
                }
                new_notifications.append(notification)
            elif current_signal == 'SELL' and notify_sell:
                notification = {
                    'type': 'sell',
                    'message': f"🔴 SELL SIGNAL for {r['name']}! Confidence: {current_confidence}%",
                    'instrument': r['name'],
                    'price': r['price_str'],
                    'stop_loss': r['stop_loss'],
                    'take_profit': r['take_profit']
                }
                new_notifications.append(notification)
            elif notify_signal_change:
                notification = {
                    'type': 'neutral',
                    'message': f"⚖️ Signal changed to NEUTRAL for {r['name']}",
                    'instrument': r['name'],
                    'price': r['price_str']
                }
                new_notifications.append(notification)
        
        # Check for confidence increase
        elif current_signal != 'NEUTRAL' and current_confidence > prev_confidence + 10:
            notification = {
                'type': 'buy' if current_signal == 'BUY' else 'sell',
                'message': f"📈 SIGNAL STRENGTHENED for {r['name']}! Confidence: {prev_confidence}% → {current_confidence}%",
                'instrument': r['name'],
                'price': r['price_str']
            }
            new_notifications.append(notification)
    
    # Store current signal for next comparison
    st.session_state.previous_signals[symbol_key] = {
        'action': current_signal,
        'confidence': current_confidence
    }

# Add new notifications to session state
if new_notifications:
    st.session_state.notifications = new_notifications + st.session_state.notifications
    # Keep only last 20 notifications
    st.session_state.notifications = st.session_state.notifications[:20]

# Display notifications using HTML/JS
if st.session_state.notifications:
    notification_html = ""
    for i, notif in enumerate(st.session_state.notifications[:5]):  # Show only last 5
        if notif['type'] == 'buy':
            notif_class = "buy-notification"
            sound = "🔔" if sound_alerts else ""
        elif notif['type'] == 'sell':
            notif_class = "sell-notification"
            sound = "🔔" if sound_alerts else ""
        else:
            notif_class = "neutral-notification"
            sound = ""
        
        notification_html += f"""
        <div class="notification {notif_class}" id="notif_{i}">
            {sound} <strong>{notif['message']}</strong><br>
            <small>Price: {notif.get('price', 'N/A')}</small>
            <span class="notification-close" onclick="document.getElementById('notif_{i}').remove()">✕</span>
        </div>
        """
    
    # JavaScript to auto-remove notifications after 10 seconds
    st.markdown(f"""
    <div id="notification-container">
        {notification_html}
    </div>
    <script>
        // Auto-remove notifications after 10 seconds
        setTimeout(function() {{
            var notifications = document.querySelectorAll('.notification');
            notifications.forEach(function(notif) {{
                notif.remove();
            }});
        }}, 10000);
        
        // Play sound for new signals
        {"new Audio('https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3').play();" if sound_alerts and new_notifications else ""}
    </script>
    """, unsafe_allow_html=True)

# ============================================
# DISPLAY TRADE SIGNALS TABLE
# ============================================
st.markdown("## 🎯 TRADE SIGNALS")
st.markdown("### What to Buy / Sell Now")

# Filter actionable signals
actionable_signals = [r for r in results if r['action'] != 'NEUTRAL' and r['confidence'] >= min_confidence_notify]

if actionable_signals:
    # Create trade signals dataframe
    trade_df = pd.DataFrame([
        {
            'Signal': r['signal'],
            'Instrument': r['name'],
            'Type': r['type'],
            'Price': r['price_str'],
            'Confidence': f"{r['confidence']}%",
            'Strength': r['signal_strength'],
            'RSI': f"{r['rsi']:.1f}",
            'Entry': r['price_str'],
            'Stop Loss': f"{r['stop_loss']:.5f}" if r['stop_loss'] else '-',
            'Take Profit': f"{r['take_profit']:.5f}" if r['take_profit'] else '-',
            'R:R': f"1:{r['risk_reward']}" if r['risk_reward'] else '-'
        }
        for r in actionable_signals
    ])
    
    # Display signals table with highlighting
    st.dataframe(
        trade_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Signal": st.column_config.TextColumn(width="small"),
            "Instrument": st.column_config.TextColumn(width="medium"),
            "Type": st.column_config.TextColumn(width="small"),
            "Price": st.column_config.TextColumn(width="small"),
            "Confidence": st.column_config.TextColumn(width="small"),
            "Strength": st.column_config.TextColumn(width="small"),
            "RSI": st.column_config.TextColumn(width="small"),
            "Entry": st.column_config.TextColumn(width="small"),
            "Stop Loss": st.column_config.TextColumn(width="medium"),
            "Take Profit": st.column_config.TextColumn(width="medium"),
            "R:R": st.column_config.TextColumn(width="small"),
        }
    )
else:
    st.info(f"⚖️ No trade signals above {min_confidence_notify}% confidence at this time.")

# ============================================
# MARKET OVERVIEW TABLE
# ============================================
st.markdown("## 📊 MARKET OVERVIEW")
st.markdown("### All Instruments Analysis")

# Create overview dataframe
overview_df = pd.DataFrame([
    {
        'Instrument': r['name'],
        'Type': r['type'],
        'Price': r['price_str'],
        'Change %': f"{r['price_change']:+.2f}%",
        'Signal': r['signal'],
        'Confidence': f"{r['confidence']}%" if r['confidence'] > 0 else '-',
        'RSI': f"{r['rsi']:.1f}",
        'SMA20': f"{r['sma20']:.5f}" if r['type'] == 'Forex' else f"{r['sma20']:.2f}",
        'SMA50': f"{r['sma50']:.5f}" if r['type'] == 'Forex' else f"{r['sma50']:.2f}",
        'MACD': f"{r['macd_histogram']:.4f}",
        'Volatility': f"{r['atr_percent']:.2f}%"
    }
    for r in results
])

st.dataframe(
    overview_df,
    use_container_width=True,
    hide_index=True
)

# ============================================
# DETAILED ANALYSIS
# ============================================
st.markdown("## 📈 DETAILED ANALYSIS")

# Create tabs for different instrument types
tab1, tab2, tab3 = st.tabs(["💰 Forex Pairs", "📊 Indices", "🥇 Commodities"])

# Filter by type
forex = [r for r in results if r['type'] == 'Forex']
indices = [r for r in results if r['type'] == 'Index']
commodities = [r for r in results if r['type'] == 'Commodity']

with tab1:
    if forex:
        for r in forex:
            with st.expander(f"{r['signal']} {r['name']} - {r['signal']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", r['price_str'], f"{r['price_change']:+.2f}%")
                    st.metric("RSI", f"{r['rsi']:.1f}", 
                             delta="Oversold" if r['rsi'] < 30 else ("Overbought" if r['rsi'] > 70 else "Neutral"))
                    st.metric("ATR Volatility", f"{r['atr_percent']:.2f}%")
                
                with col2:
                    st.metric("SMA 20", f"{r['sma20']:.5f}")
                    st.metric("SMA 50", f"{r['sma50']:.5f}")
                    st.metric("MACD Histogram", f"{r['macd_histogram']:.4f}")
                
                with col3:
                    if r['action'] != 'NEUTRAL':
                        st.metric("Signal Strength", r['signal_strength'])
                        st.metric("Confidence", f"{r['confidence']}%")
                        st.metric("Risk/Reward", f"1:{r['risk_reward']}" if r['risk_reward'] else '-')
                
                if r['action'] != 'NEUTRAL':
                    st.markdown("---")
                    st.markdown("**🎯 Trade Plan:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"🚀 **Entry:** {r['price_str']}")
                    with col_b:
                        st.warning(f"🛑 **Stop Loss:** {r['stop_loss']:.5f}")
                    with col_c:
                        st.success(f"🎯 **Take Profit:** {r['take_profit']:.5f}")
    else:
        st.info("No forex data available")

with tab2:
    if indices:
        for r in indices:
            with st.expander(f"{r['signal']} {r['name']} - {r['signal']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", r['price_str'], f"{r['price_change']:+.2f}%")
                    st.metric("RSI", f"{r['rsi']:.1f}",
                             delta="Oversold" if r['rsi'] < 30 else ("Overbought" if r['rsi'] > 70 else "Neutral"))
                    st.metric("ATR Volatility", f"{r['atr_percent']:.2f}%")
                
                with col2:
                    st.metric("SMA 20", f"{r['sma20']:.2f}")
                    st.metric("SMA 50", f"{r['sma50']:.2f}")
                    st.metric("MACD Histogram", f"{r['macd_histogram']:.4f}")
                
                with col3:
                    if r['action'] != 'NEUTRAL':
                        st.metric("Signal Strength", r['signal_strength'])
                        st.metric("Confidence", f"{r['confidence']}%")
                        st.metric("Risk/Reward", f"1:{r['risk_reward']}" if r['risk_reward'] else '-')
                
                if r['action'] != 'NEUTRAL':
                    st.markdown("---")
                    st.markdown("**🎯 Trade Plan:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"🚀 **Entry:** {r['price_str']}")
                    with col_b:
                        st.warning(f"🛑 **Stop Loss:** {r['stop_loss']:.2f}")
                    with col_c:
                        st.success(f"🎯 **Take Profit:** {r['take_profit']:.2f}")
    else:
        st.info("No index data available")

with tab3:
    if commodities:
        for r in commodities:
            with st.expander(f"{r['signal']} {r['name']} - {r['signal']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", r['price_str'], f"{r['price_change']:+.2f}%")
                    st.metric("RSI", f"{r['rsi']:.1f}",
                             delta="Oversold" if r['rsi'] < 30 else ("Overbought" if r['rsi'] > 70 else "Neutral"))
                    st.metric("ATR Volatility", f"{r['atr_percent']:.2f}%")
                
                with col2:
                    st.metric("SMA 20", f"{r['sma20']:.2f}")
                    st.metric("SMA 50", f"{r['sma50']:.2f}")
                    st.metric("MACD Histogram", f"{r['macd_histogram']:.4f}")
                
                with col3:
                    if r['action'] != 'NEUTRAL':
                        st.metric("Signal Strength", r['signal_strength'])
                        st.metric("Confidence", f"{r['confidence']}%")
                        st.metric("Risk/Reward", f"1:{r['risk_reward']}" if r['risk_reward'] else '-')
                
                if r['action'] != 'NEUTRAL':
                    st.markdown("---")
                    st.markdown("**🎯 Trade Plan:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"🚀 **Entry:** {r['price_str']}")
                    with col_b:
                        st.warning(f"🛑 **Stop Loss:** {r['stop_loss']:.2f}")
                    with col_c:
                        st.success(f"🎯 **Take Profit:** {r['take_profit']:.2f}")
    else:
        st.info("No commodity data available")

# ============================================
# SUMMARY STATISTICS
# ============================================
st.markdown("## 📊 SUMMARY STATISTICS")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    buy_signals = len([r for r in results if r['action'] == 'BUY'])
    st.metric("🟢 BUY Signals", buy_signals)

with col2:
    sell_signals = len([r for r in results if r['action'] == 'SELL'])
    st.metric("🔴 SELL Signals", sell_signals)

with col3:
    neutral = len([r for r in results if r['action'] == 'NEUTRAL'])
    st.metric("⚖️ Neutral", neutral)

with col4:
    avg_confidence = sum(r['confidence'] for r in results if r['confidence'] > 0) / len([r for r in results if r['confidence'] > 0]) if [r for r in results if r['confidence'] > 0] else 0
    st.metric("Avg Confidence", f"{avg_confidence:.0f}%")

with col5:
    if st.session_state.auto_refresh:
        st.metric("Auto-Refresh", "ON", delta="60s")
    else:
        st.metric("Auto-Refresh", "OFF")

# Recent notifications log
if st.session_state.notifications:
    with st.expander("📋 Recent Notifications Log"):
        for notif in st.session_state.notifications[:10]:
            st.write(f"• {notif['message']}")

# Telegram status
with st.expander("📱 Telegram Status"):
    st.write(f"**Bot Token:** {TELEGRAM_TOKEN[:20]}...")
    st.write(f"**Chat ID:** {TELEGRAM_CHAT_ID}")
    st.write(f"**Signals Sent:** {len(st.session_state.telegram_sent)}")
    st.write("**Last 5 Signals Sent:**")
    for sig in list(st.session_state.telegram_sent)[-5:]:
        st.write(f"• {sig}")

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
    <p>📱 Telegram notifications sent to your phone when signals appear</p>
    <p>🔄 Enable auto-refresh in sidebar for live updates</p>
</div>
""", unsafe_allow_html=True)

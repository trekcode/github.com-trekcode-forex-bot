import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import MetaTrader5 as mt5
import time
import threading

st.set_page_config(page_title="Forex Auto Trader", layout="wide")

st.title("🤖 Automated Forex Trading Bot")
st.write("Real-time signals with MetaTrader integration (Educational Only)")

# ============================================
# CONFIGURATION
# ============================================
st.sidebar.header("⚙️ Trading Configuration")

# Trading parameters
AUTO_TRADE = st.sidebar.checkbox("🤖 Enable Auto-Trading", value=False)
RISK_PERCENT = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 2.0, 0.5)
MAX_POSITIONS = st.sidebar.slider("Max Concurrent Positions", 1, 10, 3)
USE_TRAILING_STOP = st.sidebar.checkbox("Use Trailing Stop", value=False)

# MetaTrader connection status
mt5_connected = False

if AUTO_TRADE:
    st.sidebar.warning("⚠️ Auto-Trading is ENABLED - Bot will place real trades!")
    
    # Initialize MetaTrader
    if not mt5.initialize():
        st.sidebar.error("MetaTrader5 initialization failed!")
        st.sidebar.info("Please ensure MetaTrader 5 is installed and running")
    else:
        mt5_connected = True
        st.sidebar.success("✅ Connected to MetaTrader 5")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            st.sidebar.metric("Account Balance", f"${account_info.balance:.2f}")
            st.sidebar.metric("Equity", f"${account_info.equity:.2f}")
            st.sidebar.metric("Free Margin", f"${account_info.margin_free:.2f}")
else:
    st.sidebar.info("⚙️ Auto-Trading is DISABLED - Demo mode only")

# ============================================
# INSTRUMENTS CONFIGURATION
# ============================================
pairs = {
    # Forex Pairs
    'EURUSD=X': {'name': 'EUR/USD', 'type': 'Forex', 'decimals': 5, 'mt5_symbol': 'EURUSD'},
    'GBPUSD=X': {'name': 'GBP/USD', 'type': 'Forex', 'decimals': 5, 'mt5_symbol': 'GBPUSD'},
    'USDJPY=X': {'name': 'USD/JPY', 'type': 'Forex', 'decimals': 3, 'mt5_symbol': 'USDJPY'},
    'AUDUSD=X': {'name': 'AUD/USD', 'type': 'Forex', 'decimals': 5, 'mt5_symbol': 'AUDUSD'},
    'USDCAD=X': {'name': 'USD/CAD', 'type': 'Forex', 'decimals': 5, 'mt5_symbol': 'USDCAD'},
    'USDCHF=X': {'name': 'USD/CHF', 'type': 'Forex', 'decimals': 5, 'mt5_symbol': 'USDCHF'},
    'NZDUSD=X': {'name': 'NZD/USD', 'type': 'Forex', 'decimals': 5, 'mt5_symbol': 'NZDUSD'},
    
    # Indices
    '^DJI': {'name': '🇺🇸 US30', 'type': 'Index', 'decimals': 2, 'mt5_symbol': 'US30'},
    '^NDX': {'name': '🇺🇸 US100', 'type': 'Index', 'decimals': 2, 'mt5_symbol': 'NAS100'},
    
    # Commodities
    'GC=F': {'name': '🥇 Gold', 'type': 'Commodity', 'decimals': 2, 'mt5_symbol': 'XAUUSD'},
}

# ============================================
# TRADE EXECUTION FUNCTIONS
# ============================================
def calculate_lot_size(account_balance, risk_percent, stop_loss_pips, symbol_info):
    """Calculate position size based on risk"""
    risk_amount = account_balance * (risk_percent / 100)
    
    # Get tick value for the symbol
    tick_value = symbol_info.trade_tick_value
    tick_size = symbol_info.trade_tick_size
    
    # Calculate lot size
    lot_size = risk_amount / (stop_loss_pips * tick_value * 10)
    
    # Round to allowed step size
    lot_step = symbol_info.volume_step
    lot_size = round(lot_size / lot_step) * lot_step
    
    # Apply min/max limits
    lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
    
    return lot_size

def place_mt5_order(symbol, action, volume, price, sl, tp, comment="Forex Bot"):
    """Place order in MetaTrader 5"""
    try:
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return False, "Symbol not found"
        
        # Ensure symbol is visible
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                return False, "Cannot select symbol"
        
        # Prepare order request
        if action == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        
        # Create order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return False, f"Order failed: {result.comment}"
        
        return True, result.order
        
    except Exception as e:
        return False, str(e)

def close_position(position):
    """Close an open position"""
    try:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,
            "position": position.ticket,
            "price": mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask,
            "deviation": 10,
            "magic": 123456,
            "comment": "Close by bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
        
    except Exception as e:
        return False

def get_open_positions():
    """Get all open positions"""
    positions = mt5.positions_get()
    return positions if positions else []

def update_trailing_stops():
    """Update trailing stops for open positions"""
    if not USE_TRAILING_STOP:
        return
    
    positions = get_open_positions()
    for pos in positions:
        current_price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask
        
        if pos.type == 0:  # BUY position
            trailing_distance = 50  # 50 pips
            new_sl = current_price - (trailing_distance * 0.0001)
            if new_sl > pos.sl:
                modify_order(pos.ticket, new_sl, pos.tp)
        else:  # SELL position
            trailing_distance = 50
            new_sl = current_price + (trailing_distance * 0.0001)
            if new_sl < pos.sl:
                modify_order(pos.ticket, new_sl, pos.tp)

def modify_order(position_ticket, new_sl, new_tp):
    """Modify existing order"""
    try:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position_ticket,
            "sl": new_sl,
            "tp": new_tp,
        }
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    except:
        return False

# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def analyze_instrument(symbol, instrument_info):
    """Analyze instrument and generate signal"""
    try:
        name = instrument_info['name']
        instrument_type = instrument_info['type']
        
        # Fetch data
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
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD
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
        atr_percent = (atr / current) * 100
        
        # Generate signal
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
        
        # Determine signal
        if buy_score > sell_score and buy_score >= 2:
            signal = "BUY"
            signal_emoji = "🟢"
            confidence = min(90, 50 + (buy_score * 10))
        elif sell_score > buy_score and sell_score >= 2:
            signal = "SELL"
            signal_emoji = "🔴"
            confidence = min(90, 50 + (sell_score * 10))
        else:
            signal = "NEUTRAL"
            signal_emoji = "⚖️"
            confidence = 0
        
        # Calculate trade levels
        stop_loss = None
        take_profit = None
        
        if signal != "NEUTRAL":
            if signal == "BUY":
                stop_loss = current - (atr * 1.5)
                take_profit = current + (atr * 2.5)
            else:
                stop_loss = current + (atr * 1.5)
                take_profit = current - (atr * 2.5)
        
        # Check if position exists
        has_position = False
        if mt5_connected and AUTO_TRADE:
            positions = get_open_positions()
            for pos in positions:
                if pos.symbol == instrument_info['mt5_symbol']:
                    has_position = True
                    break
        
        return {
            'symbol': symbol,
            'name': name,
            'type': instrument_type,
            'price': current,
            'price_str': f"{current:.5f}" if instrument_type == 'Forex' else f"{current:.2f}",
            'signal': signal,
            'signal_emoji': signal_emoji,
            'confidence': confidence,
            'rsi': rsi,
            'sma20': sma20,
            'sma50': sma50,
            'macd_histogram': macd_histogram,
            'atr_percent': atr_percent,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'has_position': has_position,
            'mt5_symbol': instrument_info['mt5_symbol']
        }
        
    except Exception as e:
        return None

# ============================================
# TRADE MANAGEMENT
# ============================================
def execute_trades(results):
    """Execute trades based on signals"""
    if not AUTO_TRADE or not mt5_connected:
        return
    
    current_positions = get_open_positions()
    positions_count = len(current_positions) if current_positions else 0
    
    # Don't exceed max positions
    if positions_count >= MAX_POSITIONS:
        return
    
    # Get account info
    account_info = mt5.account_info()
    if not account_info:
        return
    
    for r in results:
        if r['signal'] == 'NEUTRAL' or r['has_position']:
            continue
        
        # Check if we should trade this symbol
        if positions_count >= MAX_POSITIONS:
            break
        
        # Get symbol info
        symbol_info = mt5.symbol_info(r['mt5_symbol'])
        if not symbol_info:
            continue
        
        # Calculate pips for stop loss
        if r['signal'] == 'BUY':
            stop_loss_pips = abs(r['price'] - r['stop_loss']) * 10000
        else:
            stop_loss_pips = abs(r['price'] - r['stop_loss']) * 10000
        
        # Calculate position size
        lot_size = calculate_lot_size(account_info.balance, RISK_PERCENT, stop_loss_pips, symbol_info)
        
        if lot_size <= 0:
            continue
        
        # Place order
        success, result = place_mt5_order(
            r['mt5_symbol'],
            r['signal'],
            lot_size,
            r['price'],
            r['stop_loss'],
            r['take_profit'],
            f"Forex Bot - {r['signal']}"
        )
        
        if success:
            positions_count += 1
            st.success(f"✅ {r['signal']} order placed for {r['name']}")
        else:
            st.error(f"❌ Failed to place order for {r['name']}: {result}")

# ============================================
# MAIN APP
# ============================================
st.markdown("---")

# Auto-refresh toggle
auto_refresh = st.checkbox("🔄 Auto-refresh every 5 minutes", value=False)

# Analyze markets
with st.spinner("Analyzing markets..."):
    results = []
    for symbol, info in pairs.items():
        result = analyze_instrument(symbol, info)
        if result:
            results.append(result)

# Update trailing stops
if AUTO_TRADE and mt5_connected and USE_TRAILING_STOP:
    update_trailing_stops()

# Execute trades based on signals
if AUTO_TRADE and mt5_connected:
    execute_trades(results)
    
    # Show open positions
    st.subheader("📊 Open Positions")
    positions = get_open_positions()
    if positions:
        pos_data = []
        for pos in positions:
            pos_data.append({
                'Symbol': pos.symbol,
                'Type': 'BUY' if pos.type == 0 else 'SELL',
                'Volume': pos.volume,
                'Open Price': pos.price_open,
                'Current Price': pos.price_current,
                'Profit': f"${pos.profit:.2f}",
                'Stop Loss': pos.sl,
                'Take Profit': pos.tp
            })
        st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
    else:
        st.info("No open positions")

# ============================================
# DISPLAY TRADE SIGNALS TABLE
# ============================================
st.markdown("## 🎯 TRADE SIGNALS")

actionable_signals = [r for r in results if r['signal'] != 'NEUTRAL']

if actionable_signals:
    trade_df = pd.DataFrame([
        {
            'Signal': f"{r['signal_emoji']} {r['signal']}",
            'Instrument': r['name'],
            'Type': r['type'],
            'Price': r['price_str'],
            'Confidence': f"{r['confidence']}%",
            'RSI': f"{r['rsi']:.1f}",
            'Stop Loss': f"{r['stop_loss']:.5f}" if r['stop_loss'] else '-',
            'Take Profit': f"{r['take_profit']:.5f}" if r['take_profit'] else '-',
            'Position': "✅ Open" if r['has_position'] else "❌ None"
        }
        for r in actionable_signals
    ])
    
    st.dataframe(trade_df, use_container_width=True, hide_index=True)
else:
    st.info("⚖️ No trade signals at this time")

# ============================================
# DETAILED ANALYSIS
# ============================================
st.markdown("## 📈 DETAILED ANALYSIS")

for r in results:
    with st.expander(f"{r['signal_emoji']} {r['name']} - {r['signal'] if r['signal'] != 'NEUTRAL' else 'Monitoring'}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Price", r['price_str'])
            st.metric("RSI", f"{r['rsi']:.1f}")
            st.metric("Signal", r['signal'])
        
        with col2:
            st.metric("SMA 20", f"{r['sma20']:.5f}" if r['type'] == 'Forex' else f"{r['sma20']:.2f}")
            st.metric("SMA 50", f"{r['sma50']:.5f}" if r['type'] == 'Forex' else f"{r['sma50']:.2f}")
            st.metric("MACD", f"{r['macd_histogram']:.4f}")
        
        with col3:
            st.metric("Volatility", f"{r['atr_percent']:.2f}%")
            if r['confidence'] > 0:
                st.metric("Confidence", f"{r['confidence']}%")
            if r['stop_loss'] and r['take_profit']:
                st.metric("Risk/Reward", f"1:{abs(r['take_profit'] - r['price']) / abs(r['stop_loss'] - r['price']):.1f}")

# ============================================
# AUTO-REFRESH LOGIC
# ============================================
if auto_refresh:
    st.markdown("---")
    st.info("🔄 Auto-refresh enabled - Page will reload every 5 minutes...")
    time.sleep(300)
    st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚠️ <b>Educational purposes only</b> - Test on demo account first!</p>
    <p>🤖 Auto-trading can be enabled in the sidebar</p>
    <p>📊 Signals based on: RSI, MACD, Moving Averages, and Volatility</p>
</div>
""", unsafe_allow_html=True)

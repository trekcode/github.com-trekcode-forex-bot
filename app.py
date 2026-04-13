"""
Gold & Forex Scalping Bot v2
Beautiful dark UI · Auto-send signals · Multi-factor engine
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
import logging
import time
from dataclasses import dataclass
from typing import Optional
from enum import Enum

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ScalpBot Pro",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS  — dark theme, cards, badges
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e1a; color: #e8eaf6; }

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #1e2d40;
}
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] .stSlider > div > div > div { background: #1e2d40; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
[data-testid="stMetricValue"]  { color: #e8eaf6 !important; font-size: 1.4rem !important; }
[data-testid="stMetricLabel"]  { color: #8b949e !important; }
[data-testid="stMetricDelta"]  { font-size: .8rem !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    border: none;
    transition: all .2s;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white;
}
.stButton > button:hover { transform: translateY(-1px); opacity: .92; }

/* ── Tab bar ── */
[data-baseweb="tab-list"] { background: #0d1117; border-radius: 10px; padding: 4px; gap: 4px; }
[data-baseweb="tab"] { border-radius: 8px; color: #8b949e !important; background: transparent; }
[aria-selected="true"][data-baseweb="tab"] { background: #1e2d40 !important; color: #e8eaf6 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #1e2d40; border-radius: 10px; overflow: hidden; }

/* ── Divider ── */
hr { border-color: #1e2d40; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #238636 !important; }

/* ── Text inputs ── */
input, textarea, select {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #e8eaf6 !important;
    border-radius: 6px !important;
}

/* ── Number input ── */
[data-testid="stNumberInput"] input { background: #0d1117 !important; color: #e8eaf6 !important; }

/* ── Custom components ── */
.hero {
    background: linear-gradient(135deg, #0d1f3c 0%, #0a2a1a 50%, #1a0d3c 100%);
    border: 1px solid #1e2d40;
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(35,134,54,.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero h1 { margin: 0; font-size: 1.9rem; font-weight: 700; color: #e8eaf6; }
.hero p  { margin: .4rem 0 0; color: #8b949e; font-size: .9rem; }

.signal-card {
    border-radius: 14px;
    padding: 1.6rem;
    margin: .5rem 0 1rem;
    position: relative;
    overflow: hidden;
}
.signal-buy  { background: linear-gradient(135deg,#051f0f,#0d3320); border: 1px solid #238636; }
.signal-sell { background: linear-gradient(135deg,#1f0505,#330d0d); border: 1px solid #da3633; }
.signal-hold { background: linear-gradient(135deg,#0d1117,#161b22); border: 1px solid #30363d; }

.signal-card .glow-buy  { position:absolute;top:-40px;right:-40px;width:160px;height:160px;background:radial-gradient(circle,rgba(35,134,54,.2) 0%,transparent 70%);border-radius:50%; }
.signal-card .glow-sell { position:absolute;top:-40px;right:-40px;width:160px;height:160px;background:radial-gradient(circle,rgba(218,54,51,.2) 0%,transparent 70%);border-radius:50%; }

.sig-title  { font-size: 1.7rem; font-weight: 700; margin: 0 0 .2rem; }
.sig-sub    { color: #8b949e; font-size: .85rem; margin: 0 0 1.2rem; }
.sig-grid   { display: grid; grid-template-columns: repeat(3,1fr); gap: .8rem; }
.sig-item   { background: rgba(255,255,255,.04); border-radius: 8px; padding: .6rem .8rem; }
.sig-item .label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing:.04em; }
.sig-item .value { font-size: 1rem; font-weight: 600; color: #e8eaf6; margin-top: 2px; }

.ind-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #1e2d40; font-size:13.5px; }
.ind-row:last-child { border-bottom: none; }
.ind-label { color: #8b949e; }

.badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-green  { background:#0d2618; color:#3fb950; border:1px solid #238636; }
.badge-red    { background:#26070a; color:#f85149; border:1px solid #da3633; }
.badge-gray   { background:#161b22; color:#8b949e; border:1px solid #30363d; }
.badge-yellow { background:#261d05; color:#d29922; border:1px solid #9e6a03; }
.badge-purple { background:#1a0d2e; color:#bc8cff; border:1px solid #6e40c9; }

.score-bar-wrap { margin-bottom: .8rem; }
.score-bar-row  { display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:4px; }
.score-bar-bg   { background:#1e2d40; border-radius:4px; height:7px; }
.score-bar-fill { height:7px; border-radius:4px; transition:width .5s ease; }

.auto-panel {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.auto-panel.active { border-color: #238636; box-shadow: 0 0 12px rgba(35,134,54,.15); }
.countdown { font-size: 2rem; font-weight: 700; color: #3fb950; }

.hist-row-buy  { border-left: 3px solid #238636; background: rgba(35,134,54,.06); }
.hist-row-sell { border-left: 3px solid #da3633; background: rgba(218,54,51,.06); }
.hist-row      { padding: .55rem .8rem; border-radius: 6px; margin-bottom: 4px; display:grid; grid-template-columns:70px 1fr 70px 80px 1fr 1fr 60px; gap:8px; font-size:12.5px; align-items:center; }
.hist-header   { padding: .4rem .8rem; border-radius:6px; display:grid; grid-template-columns:70px 1fr 70px 80px 1fr 1fr 60px; gap:8px; font-size:11px; color:#8b949e; text-transform:uppercase; letter-spacing:.04em; margin-bottom:4px; }

.stat-card { background:#0d1117; border:1px solid #1e2d40; border-radius:10px; padding:1rem; text-align:center; }
.stat-card .sv { font-size:1.5rem; font-weight:700; }
.stat-card .sl { font-size:12px; color:#8b949e; margin-top:2px; }

.toast-success { background:#0d2618; border:1px solid #238636; color:#3fb950; border-radius:8px; padding:.6rem 1rem; font-size:13px; }
.toast-fail    { background:#26070a; border:1px solid #da3633; color:#f85149; border-radius:8px; padding:.6rem 1rem; font-size:13px; }

.section-title { font-size:.8rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:#8b949e; margin:.5rem 0 .8rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# ENUMS / DATACLASSES
# ─────────────────────────────────────────────
class SignalType(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TradeSignal:
    signal: SignalType
    pair: str; symbol: str
    entry: float; stop_loss: float; take_profit: float
    confidence: int; risk_reward: float; lot_size: float
    session: str; timestamp: datetime; expiry: datetime
    rsi: float; macd_hist: float; stoch_k: float
    volume_ratio: float; trend: str; htf_bias: str; atr: float
    bb_pct: float
    trend_score: float; momentum_score: float
    volume_score: float; mtf_score: float

# ─────────────────────────────────────────────
# INSTRUMENTS
# ─────────────────────────────────────────────
INSTRUMENTS = {
    "GC=F":     {"name": "XAU/USD · Gold",     "emoji": "🥇", "dec": 2,  "pip": 0.10},
    "EURUSD=X": {"name": "EUR/USD",            "emoji": "🇪🇺", "dec": 5,  "pip": 10.0},
    "GBPUSD=X": {"name": "GBP/USD",            "emoji": "🇬🇧", "dec": 5,  "pip": 10.0},
    "USDJPY=X": {"name": "USD/JPY",            "emoji": "🇯🇵", "dec": 3,  "pip": 9.0},
    "^DJI":     {"name": "US30 · Dow Jones",   "emoji": "🇺🇸", "dec": 2,  "pip": 1.0},
    "^NDX":     {"name": "US100 · Nasdaq",     "emoji": "💻", "dec": 2,  "pip": 0.5},
    "SI=F":     {"name": "XAG/USD · Silver",   "emoji": "🥈", "dec": 3,  "pip": 50.0},
}

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(signal: TradeSignal, token: str, chat_id: str) -> bool:
    if not token or not chat_id:
        return False
    dec  = INSTRUMENTS[signal.symbol]["dec"]
    icon = "🟢⚡" if signal.signal == SignalType.BUY else "🔴⚡"
    strength = "🔥 STRONG" if signal.confidence >= 80 else "⚡ GOOD" if signal.confidence >= 70 else "📊 MODERATE"
    msg = f"""{icon} <b>{signal.signal.value} — {signal.pair}</b>

<b>{strength} • {signal.confidence}% confidence</b>

💰 <b>Trade Levels</b>
• Entry:        <code>{signal.entry:.{dec}f}</code>
• Stop Loss:    <code>{signal.stop_loss:.{dec}f}</code>
• Take Profit:  <code>{signal.take_profit:.{dec}f}</code>
• Risk / Reward: 1:{signal.risk_reward:.1f}

📊 <b>Technicals</b>
• RSI:     {signal.rsi:.1f}  |  MACD: {signal.macd_hist:+.4f}
• Stoch:   {signal.stoch_k:.1f}  |  Vol: {signal.volume_ratio:.1f}x
• Trend:   {signal.trend.upper()}  |  4H Bias: {signal.htf_bias.upper()}

📋 <b>Position</b>
• Lot Size: {signal.lot_size:.2f}  |  Session: {signal.session}
• Expires:  {signal.expiry.strftime('%H:%M UTC')}

<i>⚠️ Educational only — manage risk carefully</i>"""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram: {e}")
        return False

# ─────────────────────────────────────────────
# DATA & INDICATORS
# ─────────────────────────────────────────────
@st.cache_data(ttl=55, show_spinner=False)
def fetch_data(symbol: str, period: str, interval: str):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        return df if len(df) >= 55 else None
    except Exception as e:
        logger.error(f"Fetch {symbol}: {e}")
        return None

def compute_indicators(df: pd.DataFrame) -> Optional[dict]:
    try:
        c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
        ema20 = c.ewm(span=20, adjust=False).mean()
        ema50 = c.ewm(span=50, adjust=False).mean()
        delta = c.diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi   = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
        macd  = c.ewm(span=12,adjust=False).mean() - c.ewm(span=26,adjust=False).mean()
        macd_hist = macd - macd.ewm(span=9,adjust=False).mean()
        tr    = pd.concat([h-l, abs(h-c.shift()), abs(l-c.shift())], axis=1).max(axis=1)
        atr   = tr.rolling(14).mean()
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_pct = (c - (sma20 - 2*std20)) / (4*std20).replace(0, np.nan)
        low14  = l.rolling(14).min(); high14 = h.rolling(14).max()
        stoch_k = 100*(c-low14)/(high14-low14).replace(0,np.nan)
        vol_r = v / v.rolling(20).mean().replace(0,np.nan)
        price = float(c.iloc[-1])
        trend = ("bullish" if price > ema20.iloc[-1] > ema50.iloc[-1]
                 else "bearish" if price < ema20.iloc[-1] < ema50.iloc[-1]
                 else "mixed")
        return dict(
            price=price, ema20=float(ema20.iloc[-1]), ema50=float(ema50.iloc[-1]),
            rsi=float(rsi.iloc[-1]), macd_hist=float(macd_hist.iloc[-1]),
            atr=float(atr.iloc[-1]), bb_pct=float(bb_pct.iloc[-1]),
            stoch_k=float(stoch_k.iloc[-1]), volume_ratio=float(vol_r.iloc[-1]),
            trend=trend,
        )
    except Exception as e:
        logger.error(f"Indicators: {e}")
        return None

@st.cache_data(ttl=240, show_spinner=False)
def get_htf_bias(symbol: str) -> str:
    try:
        df = yf.Ticker(symbol).history(period="10d", interval="4h")
        if len(df) < 20: return "unknown"
        c = df["Close"]
        e20 = c.ewm(span=20,adjust=False).mean(); e50 = c.ewm(span=50,adjust=False).mean()
        p = c.iloc[-1]
        if p > e20.iloc[-1] > e50.iloc[-1]: return "bullish"
        if p < e20.iloc[-1] < e50.iloc[-1]: return "bearish"
        return "mixed"
    except: return "unknown"

# ─────────────────────────────────────────────
# SIGNAL ENGINE
# ─────────────────────────────────────────────
def generate_signal(symbol, ind, htf, balance, risk_pct, min_conf, min_rr,
                    atr_sl, atr_tp, hold_mins, w_trend, w_mom, w_vol, w_mtf) -> Optional[TradeSignal]:
    buy = sell = 0.0
    t_sc = m_sc = v_sc = mtf_sc = 0.0
    price, atr = ind["price"], ind["atr"]

    # Trend
    if ind["trend"] == "bullish":   buy  += 3; t_sc = w_trend
    elif ind["trend"] == "bearish": sell += 3; t_sc = w_trend
    else: t_sc = w_trend * 0.3

    # RSI
    rsi = ind["rsi"]
    if   rsi < 30: buy  += 4; m_sc += w_mom*.45
    elif rsi < 45: buy  += 1.5; m_sc += w_mom*.20
    elif rsi > 70: sell += 4; m_sc += w_mom*.45
    elif rsi > 55: sell += 1.5; m_sc += w_mom*.20

    # MACD
    if ind["macd_hist"] > 0: buy  += 2; m_sc += w_mom*.30
    else:                    sell += 2; m_sc += w_mom*.30

    # Stoch
    sk = ind["stoch_k"]
    if   sk < 20: buy  += 2; m_sc += w_mom*.25
    elif sk < 40: buy  += .5
    elif sk > 80: sell += 2; m_sc += w_mom*.25
    elif sk > 60: sell += .5

    # Bollinger
    bp = ind["bb_pct"]
    if   bp < .15: buy  += 1.5
    elif bp > .85: sell += 1.5

    # Volume
    vr = ind["volume_ratio"]
    if   vr > 2.0: v_sc = w_vol;      buy += 2 if buy>sell else 0; sell += 2 if sell>buy else 0
    elif vr > 1.5: v_sc = w_vol*.7;   buy += 1 if buy>sell else 0; sell += 1 if sell>buy else 0
    elif vr > 1.2: v_sc = w_vol*.4
    else:          v_sc = w_vol*.1

    # HTF
    if   htf == "bullish" and buy  > sell: buy  += 3; mtf_sc = w_mtf
    elif htf == "bearish" and sell > buy:  sell += 3; mtf_sc = w_mtf
    elif htf == "mixed":  mtf_sc = w_mtf*.3
    else:                 mtf_sc = w_mtf*.1

    total = buy + sell
    if total == 0: return None
    if buy > sell and buy >= 5:
        direction = SignalType.BUY
        conf = min(93, int((buy/total)*100))
    elif sell > buy and sell >= 5:
        direction = SignalType.SELL
        conf = min(93, int((sell/total)*100))
    else:
        return None

    if conf < min_conf: return None

    sl = price - atr*atr_sl if direction==SignalType.BUY else price + atr*atr_sl
    tp = price + atr*atr_tp if direction==SignalType.BUY else price - atr*atr_tp
    risk = abs(price-sl); reward = abs(tp-price)
    rr   = reward/risk if risk > 0 else 0
    if rr < min_rr: return None

    pip_val = INSTRUMENTS[symbol]["pip"] / 100
    lot     = round(min(10, max(0.01, (balance*(risk_pct/100)) / (risk*100*pip_val))), 2)

    h = datetime.utcnow().hour
    session = "London 🇬🇧" if 8<=h<16 else "New York 🇺🇸" if 13<=h<21 else "Asian 🌏"

    return TradeSignal(
        signal=direction, pair=INSTRUMENTS[symbol]["name"], symbol=symbol,
        entry=price, stop_loss=sl, take_profit=tp, confidence=conf,
        risk_reward=round(rr,2), lot_size=lot, session=session,
        timestamp=datetime.now(), expiry=datetime.now()+timedelta(minutes=hold_mins),
        rsi=rsi, macd_hist=ind["macd_hist"], stoch_k=sk,
        volume_ratio=ind["volume_ratio"], trend=ind["trend"],
        htf_bias=htf, atr=atr, bb_pct=bp,
        trend_score=t_sc, momentum_score=m_sc, volume_score=v_sc, mtf_score=mtf_sc,
    )

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def badge(text, color="gray"):
    cls = {"green":"badge-green","red":"badge-red","gray":"badge-gray",
           "yellow":"badge-yellow","purple":"badge-purple"}.get(color,"badge-gray")
    return f'<span class="badge {cls}">{text}</span>'

def score_bar(label, score, max_w, clr, sub=""):
    pct = min(100, int(score/max(max_w,1)*100))
    return f"""
<div class="score-bar-wrap">
  <div class="score-bar-row">
    <span style="color:#c9d1d9;">{label}</span>
    <span style="color:#8b949e;">{int(score)} / {int(max_w)}</span>
  </div>
  <div class="score-bar-bg">
    <div class="score-bar-fill" style="width:{pct}%;background:{clr};"></div>
  </div>
</div>"""

def full_analysis(symbol, timeframe, period_map,
                  balance, risk_pct, min_conf, min_rr, atr_sl, atr_tp, hold_mins,
                  w_trend, w_mom, w_vol, w_mtf):
    df  = fetch_data(symbol, period_map[timeframe], timeframe)
    if df is None or len(df) < 55:
        return None, None, None, "Not enough data for this timeframe. Try 1h."
    ind = compute_indicators(df)
    if ind is None:
        return None, None, None, "Indicator calculation failed."
    htf = get_htf_bias(symbol)
    sig = generate_signal(symbol, ind, htf, balance, risk_pct, min_conf, min_rr,
                          atr_sl, atr_tp, hold_mins, w_trend, w_mom, w_vol, w_mtf)
    return sig, ind, htf, None

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [
    ("history", []), ("last_result", None),
    ("auto_on", False), ("auto_interval", 120),
    ("next_run", None), ("total_sent", 0),
    ("last_tg_status", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-title">Instrument</p>', unsafe_allow_html=True)
    symbol    = st.selectbox("", list(INSTRUMENTS.keys()),
                             format_func=lambda x: f"{INSTRUMENTS[x]['emoji']}  {INSTRUMENTS[x]['name']}")
    timeframe = st.selectbox("Timeframe", ["1h","30m","15m","5m"])
    period_map = {"1h":"5d","30m":"3d","15m":"2d","5m":"1d"}

    st.markdown("---")
    st.markdown('<p class="section-title">Risk Management</p>', unsafe_allow_html=True)
    balance   = st.number_input("Account Balance ($)", 10.0, 100000.0, 100.0, 10.0)
    risk_pct  = st.slider("Risk per Trade (%)", 0.1, 5.0, 0.5, 0.1)
    min_conf  = st.slider("Min Confidence (%)", 50, 90, 65, 5)
    min_rr    = st.slider("Min Risk / Reward", 1.0, 3.0, 1.5, 0.1)
    atr_sl    = st.slider("ATR Stop-Loss ×", 0.5, 3.0, 1.0, 0.1)
    atr_tp    = st.slider("ATR Take-Profit ×", 0.5, 5.0, 1.5, 0.1)
    hold_mins = st.slider("Signal Expiry (min)", 5, 120, 30, 5)

    st.markdown("---")
    st.markdown('<p class="section-title">Signal Weights</p>', unsafe_allow_html=True)
    w_trend = st.slider("Trend",     0, 40, 25, 5)
    w_mom   = st.slider("Momentum", 0, 40, 25, 5)
    w_vol   = st.slider("Volume",   0, 40, 25, 5)
    w_mtf   = st.slider("MTF",      0, 40, 25, 5)

    st.markdown("---")
    st.markdown('<p class="section-title">Telegram Alerts</p>', unsafe_allow_html=True)
    tg_token   = st.text_input("Bot Token",  type="password", placeholder="123456:ABC-xxx")
    tg_chat_id = st.text_input("Chat ID",    placeholder="Your chat ID")
    if st.button("🔔 Test Connection", use_container_width=True):
        if tg_token and tg_chat_id:
            try:
                r = requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    json={"chat_id":tg_chat_id,"text":"✅ ScalpBot Pro connected!"},timeout=10)
                st.success("✅ Connected!") if r.ok else st.error("❌ " + r.json().get("description","Failed"))
            except: st.error("❌ Network error")
        else: st.warning("Enter token & chat ID first")

    st.markdown("---")
    st.markdown('<p class="section-title">Auto-Send Interval</p>', unsafe_allow_html=True)
    auto_interval = st.select_slider("", options=[60,120,300,600,900],
                                     value=st.session_state.auto_interval,
                                     format_func=lambda x: f"{x//60} min" if x>=60 else f"{x}s")
    st.session_state.auto_interval = auto_interval

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
pair_info = INSTRUMENTS[symbol]
h_now = datetime.utcnow().hour
session_now = "London 🇬🇧" if 8<=h_now<16 else "New York 🇺🇸" if 13<=h_now<21 else "Asian 🌏"

st.markdown(f"""
<div class="hero">
  <h1>🥇 ScalpBot Pro</h1>
  <p>Multi-factor signal engine &nbsp;·&nbsp; {pair_info['emoji']} {pair_info['name']} &nbsp;·&nbsp;
     {timeframe.upper()} chart &nbsp;·&nbsp; {session_now} &nbsp;·&nbsp;
     {datetime.utcnow().strftime('%H:%M UTC')}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTO-SEND PANEL
# ─────────────────────────────────────────────
auto_col1, auto_col2 = st.columns([3, 1])
with auto_col1:
    auto_label = "🟢 AUTO-SEND ON" if st.session_state.auto_on else "⚫ AUTO-SEND OFF"
    panel_cls  = "auto-panel active" if st.session_state.auto_on else "auto-panel"
    countdown_html = ""
    if st.session_state.auto_on and st.session_state.next_run:
        secs_left = max(0, int((st.session_state.next_run - datetime.now()).total_seconds()))
        mins_left, s_left = divmod(secs_left, 60)
        countdown_html = f'<span class="countdown">{mins_left:02d}:{s_left:02d}</span> <span style="color:#8b949e;font-size:.85rem;">until next signal</span>'
    else:
        countdown_html = '<span style="color:#8b949e;font-size:.9rem;">Toggle to start sending signals automatically</span>'

    st.markdown(f"""
    <div class="{panel_cls}">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-weight:700;font-size:1rem;color:{'#3fb950' if st.session_state.auto_on else '#8b949e'};">{auto_label}</div>
          <div style="margin-top:.35rem;">{countdown_html}</div>
        </div>
        <div style="text-align:right;font-size:12px;color:#8b949e;">
          Interval: {auto_interval//60}m &nbsp;|&nbsp; Sent today: {st.session_state.total_sent}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with auto_col2:
    st.write("")
    toggle_label = "⏹ Stop Auto" if st.session_state.auto_on else "▶ Start Auto"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.auto_on = not st.session_state.auto_on
        if st.session_state.auto_on:
            st.session_state.next_run = datetime.now()
        else:
            st.session_state.next_run = None
        st.rerun()

# ─────────────────────────────────────────────
# MANUAL ANALYZE BUTTON
# ─────────────────────────────────────────────
b1, b2, b3 = st.columns([2, 1, 2])
with b1:
    manual_run = st.button("🚀 Analyze & Generate Signal", use_container_width=True, type="primary")
with b2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_result = None
        st.session_state.total_sent = 0
        st.rerun()

# ─────────────────────────────────────────────
# DECIDE WHETHER TO RUN
# ─────────────────────────────────────────────
should_run = manual_run
if (st.session_state.auto_on and st.session_state.next_run
        and datetime.now() >= st.session_state.next_run):
    should_run = True
    st.session_state.next_run = datetime.now() + timedelta(seconds=st.session_state.auto_interval)

# ─────────────────────────────────────────────
# RUN ANALYSIS
# ─────────────────────────────────────────────
if should_run:
    with st.spinner("Fetching data & computing indicators..."):
        fetch_data.clear()
        sig, ind, htf, err = full_analysis(
            symbol, timeframe, period_map,
            balance, risk_pct, min_conf, min_rr, atr_sl, atr_tp, hold_mins,
            w_trend, w_mom, w_vol, w_mtf,
        )
    if err:
        st.error(f"⚠️ {err}")
    else:
        st.session_state.last_result = (sig, ind, htf)
        if sig:
            st.session_state.history.insert(0, sig)
            if len(st.session_state.history) > 30:
                st.session_state.history = st.session_state.history[:30]
            # Telegram
            tg_ok = send_telegram(sig, tg_token, tg_chat_id)
            st.session_state.last_tg_status = ("✅ Signal sent to Telegram!" if tg_ok
                                                else ("⚠️ No Telegram configured" if not tg_token
                                                      else "❌ Telegram send failed"))
            st.session_state.total_sent += 1
        else:
            st.session_state.last_tg_status = None

# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────
if st.session_state.last_result:
    sig, ind, htf = st.session_state.last_result
    dec = INSTRUMENTS[symbol]["dec"]

    # Telegram status toast
    if st.session_state.last_tg_status:
        cls = "toast-success" if "✅" in st.session_state.last_tg_status else "toast-fail"
        st.markdown(f'<div class="{cls}">{st.session_state.last_tg_status}</div>', unsafe_allow_html=True)

    # ── Snapshot metrics
    st.markdown('<p class="section-title" style="margin-top:1.2rem;">Live Snapshot</p>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("Price",     f"{ind['price']:.{dec}f}")
    m2.metric("RSI (14)",  f"{ind['rsi']:.1f}",
              delta="Oversold" if ind['rsi']<30 else "Overbought" if ind['rsi']>70 else None)
    m3.metric("MACD Hist", f"{ind['macd_hist']:+.4f}",
              delta="Bullish" if ind['macd_hist']>0 else "Bearish")
    m4.metric("Stoch %K",  f"{ind['stoch_k']:.1f}")
    m5.metric("Trend",     ind['trend'].title())
    m6.metric("Vol Ratio", f"{ind['volume_ratio']:.2f}x",
              delta="Spike!" if ind['volume_ratio']>1.5 else None)

    st.markdown("")

    # ── SIGNAL CARD
    if sig:
        is_buy  = sig.signal == SignalType.BUY
        clr_val = "#3fb950" if is_buy else "#f85149"
        glow    = "glow-buy" if is_buy else "glow-sell"
        css     = "signal-buy" if is_buy else "signal-sell"
        icon    = "🟢 BUY" if is_buy else "🔴 SELL"
        conf_c  = "#3fb950" if sig.confidence>=75 else "#d29922" if sig.confidence>=60 else "#f85149"
        strength= "🔥 Strong Signal" if sig.confidence>=80 else "⚡ Good Signal" if sig.confidence>=70 else "📊 Moderate Signal"

        st.markdown(f"""
        <div class="signal-card {css}">
          <div class="{glow}"></div>
          <div class="sig-title" style="color:{clr_val};">{icon}</div>
          <div class="sig-sub">{pair_info['emoji']} {pair_info['name']} &nbsp;·&nbsp; {timeframe.upper()} &nbsp;·&nbsp;
               <span style="color:{conf_c};font-weight:600;">{sig.confidence}% confidence</span> &nbsp;·&nbsp; {strength} &nbsp;·&nbsp; {sig.session}</div>
          <div class="sig-grid">
            <div class="sig-item"><div class="label">Entry</div><div class="value">{sig.entry:.{dec}f}</div></div>
            <div class="sig-item"><div class="label">Stop Loss</div><div class="value" style="color:#f85149;">{sig.stop_loss:.{dec}f}</div></div>
            <div class="sig-item"><div class="label">Take Profit</div><div class="value" style="color:#3fb950;">{sig.take_profit:.{dec}f}</div></div>
            <div class="sig-item"><div class="label">Risk / Reward</div><div class="value">1 : {sig.risk_reward}</div></div>
            <div class="sig-item"><div class="label">Lot Size</div><div class="value">{sig.lot_size}</div></div>
            <div class="sig-item"><div class="label">Expires</div><div class="value">{sig.expiry.strftime('%H:%M UTC')}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="signal-card signal-hold">
          <div class="sig-title" style="color:#8b949e;">⚖️ HOLD — No Signal</div>
          <div class="sig-sub">Market lacks directional edge right now. Filters: min confidence or R/R not met. Wait for a cleaner setup.</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Two-column: indicators + score
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="section-title">All Indicators</p>', unsafe_allow_html=True)
        rsi_c  = "green" if ind['rsi']<40 else "red" if ind['rsi']>60 else "gray"
        mcd_c  = "green" if ind['macd_hist']>0 else "red"
        sk_c   = "green" if ind['stoch_k']<30 else "red" if ind['stoch_k']>70 else "gray"
        tr_c   = "green" if ind['trend']=="bullish" else "red" if ind['trend']=="bearish" else "gray"
        ht_c   = "green" if htf=="bullish" else "red" if htf=="bearish" else "gray"
        vl_c   = "green" if ind['volume_ratio']>1.5 else "gray"
        bb_c   = "green" if ind['bb_pct']<.2 else "red" if ind['bb_pct']>.8 else "gray"

        rows = [
            ("RSI (14)",         f"{ind['rsi']:.1f}",           rsi_c),
            ("MACD Histogram",   f"{ind['macd_hist']:+.5f}",    mcd_c),
            ("Stochastic %K",    f"{ind['stoch_k']:.1f}",       sk_c),
            ("Bollinger %B",     f"{ind['bb_pct']*100:.1f}%",   bb_c),
            ("ATR (14)",         f"{ind['atr']:.{dec}f}",       "gray"),
            ("EMA 20",           f"{ind['ema20']:.{dec}f}",     "gray"),
            ("EMA 50",           f"{ind['ema50']:.{dec}f}",     "gray"),
            ("Volume Ratio",     f"{ind['volume_ratio']:.2f}x", vl_c),
            ("1H Trend",         ind['trend'].title(),          tr_c),
            ("4H Bias (HTF)",    htf.title(),                   ht_c),
        ]
        rows_html = ""
        for name_, val_, c_ in rows:
            rows_html += f'<div class="ind-row"><span class="ind-label">{name_}</span>{badge(val_, c_)}</div>'
        st.markdown(rows_html, unsafe_allow_html=True)

    with col_b:
        st.markdown('<p class="section-title">Score Breakdown</p>', unsafe_allow_html=True)
        if sig:
            bars = [
                ("Trend alignment",             sig.trend_score,    w_trend,      "#3fb950"),
                ("Momentum (RSI+MACD+Stoch)", sig.momentum_score, w_mom*1.3,    "#58a6ff"),
                ("Volume confirmation",          sig.volume_score,   w_vol,        "#d29922"),
                ("Multi-TF confluence",          sig.mtf_score,      w_mtf,        "#bc8cff"),
            ]
            bars_html = ""
            for lbl, sc, mx, clr in bars:
                bars_html += score_bar(lbl, sc, mx, clr)

            conf = sig.confidence
            conf_clr = "#3fb950" if conf>=75 else "#d29922" if conf>=60 else "#f85149"
            bars_html += f"""
            <div style="background:#0d1117;border:1px solid #1e2d40;border-radius:10px;padding:1rem;margin-top:1rem;">
              <div style="display:flex;justify-content:space-between;font-weight:600;margin-bottom:8px;font-size:.9rem;">
                <span>Overall confidence</span>
                <span style="color:{conf_clr};">{conf}%</span>
              </div>
              <div style="background:#1e2d40;border-radius:6px;height:10px;">
                <div style="width:{conf}%;background:{conf_clr};height:10px;border-radius:6px;"></div>
              </div>
            </div>"""
            st.markdown(bars_html, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#8b949e;font-size:.9rem;">Run an analysis to see the score breakdown.</p>', unsafe_allow_html=True)

    # ── Price chart
    st.markdown("---")
    st.markdown('<p class="section-title">Price Action (last 60 candles)</p>', unsafe_allow_html=True)
    chart_df = fetch_data(symbol, period_map[timeframe], timeframe)
    if chart_df is not None:
        cc = chart_df["Close"].tail(60)
        e20 = cc.ewm(span=20,adjust=False).mean()
        e50 = cc.ewm(span=50,adjust=False).mean()
        st.line_chart(pd.DataFrame({"Price":cc,"EMA 20":e20,"EMA 50":e50}))

# ─────────────────────────────────────────────
# SIGNAL HISTORY
# ─────────────────────────────────────────────
if st.session_state.history:
    st.markdown("---")
    st.markdown('<p class="section-title">Signal History — This Session</p>', unsafe_allow_html=True)

    # Stat cards
    buys  = sum(1 for s in st.session_state.history if s.signal==SignalType.BUY)
    sells = sum(1 for s in st.session_state.history if s.signal==SignalType.SELL)
    avg_c = int(np.mean([s.confidence for s in st.session_state.history]))
    avg_r = round(np.mean([s.risk_reward for s in st.session_state.history]), 2)

    sc1,sc2,sc3,sc4 = st.columns(4)
    def stat_card(col, val, label, color="#e8eaf6"):
        col.markdown(f'<div class="stat-card"><div class="sv" style="color:{color};">{val}</div><div class="sl">{label}</div></div>', unsafe_allow_html=True)
    stat_card(sc1, len(st.session_state.history), "Total signals")
    stat_card(sc2, buys,  "Buy signals",  "#3fb950")
    stat_card(sc3, sells, "Sell signals", "#f85149")
    stat_card(sc4, f"{avg_c}% / 1:{avg_r}", "Avg conf / R:R")

    st.markdown("")
    # Table header
    st.markdown('<div class="hist-header"><span>Time</span><span>Pair</span><span>Signal</span><span>Conf</span><span>Entry</span><span>TP</span><span>R/R</span></div>', unsafe_allow_html=True)
    rows_html = ""
    for s in st.session_state.history[:15]:
        is_b = s.signal == SignalType.BUY
        row_cls = "hist-row hist-row-buy" if is_b else "hist-row hist-row-sell"
        dec_ = INSTRUMENTS.get(s.symbol, {}).get("dec", 5)
        sig_badge = badge("BUY","green") if is_b else badge("SELL","red")
        conf_badge = badge(f"{s.confidence}%", "green" if s.confidence>=75 else "yellow" if s.confidence>=65 else "red")
        rows_html += f"""
        <div class="{row_cls}">
          <span style="color:#8b949e;">{s.timestamp.strftime('%H:%M:%S')}</span>
          <span style="font-weight:600;">{pair_info['emoji']} {s.pair.split('·')[0].strip()}</span>
          <span>{sig_badge}</span>
          <span>{conf_badge}</span>
          <span>{s.entry:.{dec_}f}</span>
          <span style="color:#3fb950;">{s.take_profit:.{dec_}f}</span>
          <span>1:{s.risk_reward}</span>
        </div>"""
    st.markdown(rows_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8b949e;font-size:12px;padding:.5rem 0 1rem;">
  ⚠️ <b>For educational purposes only.</b> &nbsp;Not financial advice. &nbsp;Always use proper risk management.<br>
  Powered by: RSI · MACD · Stochastic · Bollinger Bands · ATR · Volume · Multi-Timeframe Confluence
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTO-REFRESH LOOP
# ─────────────────────────────────────────────
if st.session_state.auto_on:
    if st.session_state.next_run and datetime.now() < st.session_state.next_run:
        secs = max(1, int((st.session_state.next_run - datetime.now()).total_seconds()))
        wait = min(secs, 10)
        time.sleep(wait)
        st.rerun()

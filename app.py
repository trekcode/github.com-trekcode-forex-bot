# === SCALPBOT PRO v3 — FULL SMC/ICT TOP-DOWN EDITION ===
"""
ScalpBot Pro v3
• Permanent sidebar (never collapses)
• Full ICT/SMC top-down engine: Daily → 4H → 1H → Entry TF
• Detects: Order Blocks, FVGs, BOS/CHOCH, Liquidity Sweeps, Supply/Demand
• Plotly candlestick chart with drawn OBs, FVGs, liquidity lines
• SMC Strength Meter + SMC Analysis tab
• Auto-send toggle with countdown • Telegram with SMC levels
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be FIRST Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ScalpBot Pro v3",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS — dark theme + permanent sidebar
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── App background ── */
.stApp { background: #0a0e1a; color: #e8eaf6; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }

/* ════════════════════════════════════════════
   PERMANENT SIDEBAR — hide the collapse arrow
   ════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #1e2d40;
    min-width: 290px !important;
    max-width: 290px !important;
}
/* Kill the collapse/expand toggle button */
[data-testid="stSidebarCollapseButton"],
button[aria-label="Close sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Open sidebar"],
[data-testid="collapsedControl"] { display: none !important; }

[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
[data-testid="stSidebar"] .stSlider > div > div > div { background: #1e2d40; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e8eaf6 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
[data-testid="stMetricValue"]  { color: #e8eaf6 !important; font-size: 1.35rem !important; }
[data-testid="stMetricLabel"]  { color: #8b949e !important; }
[data-testid="stMetricDelta"]  { font-size: .78rem !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    border: none;
    transition: all .2s;
    color: #e8eaf6 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: white !important;
}
.stButton > button:hover { transform: translateY(-1px); opacity: .92; }

/* ── Tabs ── */
[data-baseweb="tab-list"] { background: #0d1117; border-radius: 10px; padding: 4px; gap: 4px; border: 1px solid #1e2d40; }
[data-baseweb="tab"] { border-radius: 8px; color: #8b949e !important; background: transparent; font-size: .85rem; }
[aria-selected="true"][data-baseweb="tab"] { background: #1e2d40 !important; color: #e8eaf6 !important; font-weight: 600; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #1e2d40; border-radius: 10px; overflow: hidden; }

/* ── Divider ── */
hr { border-color: #1e2d40; margin: 1rem 0; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #238636 !important; }

/* ── Text / number inputs ── */
input, textarea, select {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #e8eaf6 !important;
    border-radius: 6px !important;
}
[data-testid="stNumberInput"] input { background: #0d1117 !important; color: #e8eaf6 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #0d1117;
    border: 1px solid #1e2d40 !important;
    border-radius: 10px;
}
[data-testid="stExpander"] summary { color: #c9d1d9 !important; font-weight: 600; }

/* ════════ CUSTOM COMPONENTS ════════ */

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #0d1f3c 0%, #0a2a1a 50%, #1a0d3c 100%);
    border: 1px solid #1e2d40;
    border-radius: 16px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
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
.hero h1 { margin: 0; font-size: 1.8rem; font-weight: 700; color: #e8eaf6; }
.hero p  { margin: .35rem 0 0; color: #8b949e; font-size: .88rem; }

/* Signal cards */
.signal-card {
    border-radius: 14px;
    padding: 1.5rem;
    margin: .4rem 0 .8rem;
    position: relative;
    overflow: hidden;
}
.signal-buy  { background: linear-gradient(135deg,#051f0f,#0d3320); border: 1px solid #238636; }
.signal-sell { background: linear-gradient(135deg,#1f0505,#330d0d); border: 1px solid #da3633; }
.signal-hold { background: linear-gradient(135deg,#0d1117,#161b22); border: 1px solid #30363d; }

.glow-buy  { position:absolute;top:-40px;right:-40px;width:160px;height:160px;background:radial-gradient(circle,rgba(35,134,54,.22) 0%,transparent 70%);border-radius:50%; }
.glow-sell { position:absolute;top:-40px;right:-40px;width:160px;height:160px;background:radial-gradient(circle,rgba(218,54,51,.22) 0%,transparent 70%);border-radius:50%; }

.sig-title { font-size: 1.65rem; font-weight: 700; margin: 0 0 .15rem; }
.sig-sub   { color: #8b949e; font-size: .83rem; margin: 0 0 1rem; }
.sig-grid  { display: grid; grid-template-columns: repeat(3,1fr); gap: .7rem; }
.sig-item  { background: rgba(255,255,255,.045); border-radius: 8px; padding: .55rem .75rem; }
.sig-item .label { font-size: 10.5px; color: #8b949e; text-transform: uppercase; letter-spacing:.04em; }
.sig-item .value { font-size: .95rem; font-weight: 600; color: #e8eaf6; margin-top: 2px; }
.sig-item .value.green { color: #3fb950; }
.sig-item .value.red   { color: #f85149; }

/* Indicator rows */
.ind-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #1e2d40; font-size:13px; }
.ind-row:last-child { border-bottom: none; }
.ind-label { color: #8b949e; }

/* Badges */
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:11.5px; font-weight:600; }
.badge-green  { background:#0d2618; color:#3fb950; border:1px solid #238636; }
.badge-red    { background:#26070a; color:#f85149; border:1px solid #da3633; }
.badge-gray   { background:#161b22; color:#8b949e; border:1px solid #30363d; }
.badge-yellow { background:#261d05; color:#d29922; border:1px solid #9e6a03; }
.badge-purple { background:#1a0d2e; color:#bc8cff; border:1px solid #6e40c9; }
.badge-blue   { background:#051929; color:#58a6ff; border:1px solid #1f6feb; }
.badge-orange { background:#271700; color:#f0883e; border:1px solid #bd561d; }

/* Score bars */
.score-bar-wrap { margin-bottom: .75rem; }
.score-bar-row  { display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px; color:#c9d1d9; }
.score-bar-bg   { background:#1e2d40; border-radius:4px; height:7px; }
.score-bar-fill { height:7px; border-radius:4px; transition:width .5s ease; }

/* SMC Strength Meter */
.smc-meter { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:.6rem 0; }
.smc-bar-wrap { text-align:center; }
.smc-bar-label { font-size:10px; color:#8b949e; margin-bottom:4px; text-transform:uppercase; letter-spacing:.04em; }
.smc-bar-outer { background:#1e2d40; border-radius:6px; height:60px; display:flex; flex-direction:column-reverse; overflow:hidden; }
.smc-bar-inner { border-radius:6px; transition:height .5s ease; }

/* SMC level cards */
.smc-level-card {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 10px;
    padding: .85rem 1rem;
    margin-bottom: .5rem;
    font-size: 13px;
}
.smc-level-card.ob-bull { border-left: 3px solid #238636; }
.smc-level-card.ob-bear { border-left: 3px solid #da3633; }
.smc-level-card.fvg-bull { border-left: 3px solid #58a6ff; }
.smc-level-card.fvg-bear { border-left: 3px solid #bc8cff; }
.smc-level-card.liq      { border-left: 3px solid #d29922; }
.smc-level-card.sd-bull  { border-left: 3px solid #3fb950; }
.smc-level-card.sd-bear  { border-left: 3px solid #f85149; }

/* Bias row */
.bias-row { display:flex; gap:10px; margin:.5rem 0 1rem; flex-wrap:wrap; }
.bias-pill {
    padding: .4rem .9rem;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid transparent;
}
.bias-bull { background:#0d2618; color:#3fb950; border-color:#238636; }
.bias-bear { background:#26070a; color:#f85149; border-color:#da3633; }
.bias-neut { background:#161b22; color:#8b949e; border-color:#30363d; }

/* Auto-send panel */
.auto-panel {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: .8rem;
}
.auto-panel.active { border-color: #238636; box-shadow: 0 0 14px rgba(35,134,54,.18); }
.countdown { font-size: 1.9rem; font-weight: 700; color: #3fb950; }

/* History */
.hist-row-buy  { border-left: 3px solid #238636; background: rgba(35,134,54,.06); }
.hist-row-sell { border-left: 3px solid #da3633; background: rgba(218,54,51,.06); }
.hist-row      { padding:.5rem .75rem; border-radius:6px; margin-bottom:3px; display:grid; grid-template-columns:70px 1fr 60px 75px 1fr 1fr 55px 1fr; gap:7px; font-size:12px; align-items:center; }
.hist-header   { padding:.35rem .75rem; border-radius:6px; display:grid; grid-template-columns:70px 1fr 60px 75px 1fr 1fr 55px 1fr; gap:7px; font-size:10.5px; color:#8b949e; text-transform:uppercase; letter-spacing:.04em; margin-bottom:4px; }

/* Stat cards */
.stat-card { background:#0d1117; border:1px solid #1e2d40; border-radius:10px; padding:.9rem; text-align:center; }
.stat-card .sv { font-size:1.45rem; font-weight:700; }
.stat-card .sl { font-size:11.5px; color:#8b949e; margin-top:2px; }

/* Toast */
.toast-success { background:#0d2618; border:1px solid #238636; color:#3fb950; border-radius:8px; padding:.55rem 1rem; font-size:13px; margin:.4rem 0; }
.toast-fail    { background:#26070a; border:1px solid #da3633; color:#f85149; border-radius:8px; padding:.55rem 1rem; font-size:13px; margin:.4rem 0; }

/* Section title */
.section-title { font-size:.75rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:#8b949e; margin:.5rem 0 .65rem; }

/* Confluence table */
.conf-table { width:100%; border-collapse:collapse; font-size:12.5px; }
.conf-table th { color:#8b949e; font-weight:600; text-transform:uppercase; font-size:11px; padding:6px 8px; border-bottom:1px solid #1e2d40; text-align:left; }
.conf-table td { padding:6px 8px; border-bottom:1px solid #0d1117; color:#c9d1d9; }
.conf-table tr:last-child td { border-bottom:none; }
.conf-table tr:hover td { background:rgba(255,255,255,.02); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────
class SignalType(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

# ─────────────────────────────────────────────
# SMC STRUCTURE DATACLASSES
# ─────────────────────────────────────────────
@dataclass
class OrderBlock:
    """A bullish or bearish order block zone"""
    ob_type: str          # "bullish" or "bearish"
    top: float
    bottom: float
    mid: float
    index: int            # candle index in df
    strength: float       # 0-1, based on move size after OB
    mitigated: bool = False

@dataclass
class FairValueGap:
    """3-candle imbalance gap"""
    fvg_type: str         # "bullish" or "bearish"
    top: float
    bottom: float
    mid: float
    index: int
    filled: bool = False

@dataclass
class LiquidityLevel:
    """Equal highs/lows or swing liquidity pool"""
    liq_type: str         # "buy_side" (above highs) or "sell_side" (below lows)
    price: float
    swept: bool = False
    strength: float = 0.5

@dataclass
class SupplyDemandZone:
    """Supply or demand zone based on strong reaction"""
    zone_type: str        # "demand" or "supply"
    top: float
    bottom: float
    mid: float
    strength: float = 0.5

@dataclass
class SMCAnalysis:
    """Full SMC top-down analysis result"""
    # Bias per timeframe
    daily_bias: str       # bullish / bearish / mixed
    h4_bias: str
    h1_bias: str
    entry_bias: str
    # Structure
    bos_detected: bool
    choch_detected: bool
    bos_direction: str    # bullish / bearish
    # SMC Levels
    order_blocks: List[OrderBlock] = field(default_factory=list)
    fvgs: List[FairValueGap] = field(default_factory=list)
    liquidity_levels: List[LiquidityLevel] = field(default_factory=list)
    supply_demand: List[SupplyDemandZone] = field(default_factory=list)
    # Scores (0-100 each)
    structure_score: float = 0.0
    ob_score: float = 0.0
    fvg_score: float = 0.0
    liquidity_score: float = 0.0
    confluence_score: float = 0.0
    # Key level description
    key_level_type: str = "None"
    # Raw DFs for chart
    df_entry: Optional[pd.DataFrame] = None

@dataclass
class TradeSignal:
    """Complete trade signal with SMC enrichment"""
    signal: SignalType
    pair: str
    symbol: str
    entry: float
    stop_loss: float
    take_profit: float
    confidence: int
    risk_reward: float
    lot_size: float
    session: str
    timestamp: datetime
    expiry: datetime
    # Classic indicators
    rsi: float
    macd_hist: float
    stoch_k: float
    volume_ratio: float
    trend: str
    htf_bias: str
    atr: float
    bb_pct: float
    # Score components
    trend_score: float
    momentum_score: float
    volume_score: float
    mtf_score: float
    smc_score: float
    # SMC enrichment
    smc_confluence_score: float
    key_level_type: str
    daily_bias: str
    h4_bias: str

# ─────────────────────────────────────────────
# INSTRUMENTS
# ─────────────────────────────────────────────
INSTRUMENTS = {
    "GC=F":     {"name": "XAU/USD · Gold",    "emoji": "🥇", "dec": 2, "pip": 0.10},
    "EURUSD=X": {"name": "EUR/USD",           "emoji": "🇪🇺", "dec": 5, "pip": 10.0},
    "GBPUSD=X": {"name": "GBP/USD",           "emoji": "🇬🇧", "dec": 5, "pip": 10.0},
    "USDJPY=X": {"name": "USD/JPY",           "emoji": "🇯🇵", "dec": 3, "pip": 9.0},
    "^DJI":     {"name": "US30 · Dow Jones",  "emoji": "🇺🇸", "dec": 2, "pip": 1.0},
    "^NDX":     {"name": "US100 · Nasdaq",    "emoji": "💻",  "dec": 2, "pip": 0.5},
    "SI=F":     {"name": "XAG/USD · Silver",  "emoji": "🥈", "dec": 3, "pip": 50.0},
}

# ─────────────────────────────────────────────
# DATA FETCHING (cached)
# ─────────────────────────────────────────────
@st.cache_data(ttl=55, show_spinner=False)
def fetch_data(symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        return df if len(df) >= 30 else None
    except Exception as e:
        logger.error(f"Fetch {symbol} {interval}: {e}")
        return None

# ─────────────────────────────────────────────
# CLASSIC INDICATORS
# ─────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> Optional[dict]:
    """Compute RSI, MACD, Stoch, BB, ATR, EMA, Volume"""
    try:
        c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
        ema20 = c.ewm(span=20, adjust=False).mean()
        ema50 = c.ewm(span=50, adjust=False).mean()
        delta = c.diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi   = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
        macd  = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        macd_hist = macd - macd.ewm(span=9, adjust=False).mean()
        tr    = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr   = tr.rolling(14).mean()
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_pct = (c - (sma20 - 2 * std20)) / (4 * std20).replace(0, np.nan)
        low14  = l.rolling(14).min()
        high14 = h.rolling(14).max()
        stoch_k = 100 * (c - low14) / (high14 - low14).replace(0, np.nan)
        vol_r = v / v.rolling(20).mean().replace(0, np.nan)
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

# ─────────────────────────────────────────────
# SMC ENGINE — SWING DETECTION
# ─────────────────────────────────────────────
def detect_swings(df: pd.DataFrame, left: int = 3, right: int = 3):
    """
    Detect swing highs and lows.
    Returns two boolean Series: swing_highs, swing_lows
    """
    highs = df["High"]
    lows  = df["Low"]
    n = len(df)
    swing_highs = pd.Series(False, index=df.index)
    swing_lows  = pd.Series(False, index=df.index)
    for i in range(left, n - right):
        window_h = highs.iloc[i - left: i + right + 1]
        window_l = lows.iloc[i  - left: i + right + 1]
        if highs.iloc[i] == window_h.max():
            swing_highs.iloc[i] = True
        if lows.iloc[i] == window_l.min():
            swing_lows.iloc[i] = True
    return swing_highs, swing_lows

# ─────────────────────────────────────────────
# SMC ENGINE — BOS / CHOCH DETECTION
# ─────────────────────────────────────────────
def detect_bos_choch(df: pd.DataFrame, swing_highs: pd.Series, swing_lows: pd.Series) -> dict:
    """
    Break of Structure (BOS): price continues in trend direction, breaking last swing H/L
    Change of Character (CHOCH): price breaks AGAINST the trend, signalling potential reversal
    """
    result = {"bos": False, "choch": False, "bos_direction": "none", "last_hh": None, "last_ll": None}
    if len(df) < 10:
        return result
    close = df["Close"]
    price = float(close.iloc[-1])

    sh_prices = df["High"][swing_highs].values
    sl_prices = df["Low"][swing_lows].values

    if len(sh_prices) >= 2:
        last_sh  = sh_prices[-1]
        prev_sh  = sh_prices[-2]
        result["last_hh"] = float(last_sh)
        # BOS bullish: current close breaks above last swing high
        if price > last_sh:
            if last_sh > prev_sh:   # Higher High → BOS bullish continuation
                result["bos"] = True
                result["bos_direction"] = "bullish"
            else:                   # Lower High broken → CHOCH bullish
                result["choch"] = True
                result["bos_direction"] = "bullish"

    if len(sl_prices) >= 2:
        last_sl  = sl_prices[-1]
        prev_sl  = sl_prices[-2]
        result["last_ll"] = float(last_sl)
        if price < last_sl:
            if last_sl < prev_sl:   # Lower Low → BOS bearish continuation
                result["bos"] = True
                result["bos_direction"] = "bearish"
            else:                   # Higher Low broken → CHOCH bearish
                result["choch"] = True
                result["bos_direction"] = "bearish"

    return result

# ─────────────────────────────────────────────
# SMC ENGINE — ORDER BLOCKS
# ─────────────────────────────────────────────
def detect_order_blocks(df: pd.DataFrame, lookback: int = 50) -> List[OrderBlock]:
    """
    Bullish OB: last BEARISH candle before a strong bullish impulse move
    Bearish OB: last BULLISH candle before a strong bearish impulse move
    Strength is proportional to how far price moved after the OB.
    """
    obs: List[OrderBlock] = []
    df_tail = df.tail(lookback).reset_index(drop=True)
    close = df_tail["Close"].values
    open_ = df_tail["Open"].values
    high  = df_tail["High"].values
    low   = df_tail["Low"].values
    n = len(df_tail)
    atr_val = float(pd.Series(high - low).rolling(5).mean().iloc[-1]) if n > 5 else (high[-1] - low[-1])

    for i in range(2, n - 2):
        # Check for impulse move AFTER candle i
        future_close = close[min(i + 3, n - 1)]
        move = future_close - close[i]
        move_abs = abs(move)

        # Bullish OB: bearish candle (close < open) before upward impulse
        if close[i] < open_[i] and move > atr_val * 1.0:
            strength = min(1.0, move_abs / (atr_val * 3))
            # Check if OB is mitigated (price returned into it)
            ob_top = open_[i]
            ob_bot = low[i]
            mitigated = any(low[j] < ob_top and close[j] < ob_bot for j in range(i + 1, n))
            obs.append(OrderBlock(
                ob_type="bullish", top=float(ob_top), bottom=float(ob_bot),
                mid=float((ob_top + ob_bot) / 2), index=i,
                strength=strength, mitigated=mitigated,
            ))

        # Bearish OB: bullish candle (close > open) before downward impulse
        elif close[i] > open_[i] and move < -atr_val * 1.0:
            strength = min(1.0, move_abs / (atr_val * 3))
            ob_top = high[i]
            ob_bot = open_[i]
            mitigated = any(high[j] > ob_bot and close[j] > ob_top for j in range(i + 1, n))
            obs.append(OrderBlock(
                ob_type="bearish", top=float(ob_top), bottom=float(ob_bot),
                mid=float((ob_top + ob_bot) / 2), index=i,
                strength=strength, mitigated=mitigated,
            ))

    # Return the 4 most recent, strongest, un-mitigated ones
    fresh = [o for o in obs if not o.mitigated]
    fresh.sort(key=lambda x: (x.strength, x.index), reverse=True)
    return fresh[:4]

# ─────────────────────────────────────────────
# SMC ENGINE — FAIR VALUE GAPS (FVG)
# ─────────────────────────────────────────────
def detect_fvgs(df: pd.DataFrame, lookback: int = 40) -> List[FairValueGap]:
    """
    Bullish FVG: candle[i-1].high < candle[i+1].low  → gap between them
    Bearish FVG: candle[i-1].low  > candle[i+1].high → gap between them
    """
    fvgs: List[FairValueGap] = []
    df_tail = df.tail(lookback).reset_index(drop=True)
    high  = df_tail["High"].values
    low   = df_tail["Low"].values
    close = df_tail["Close"].values
    n = len(df_tail)
    price = close[-1]

    for i in range(1, n - 1):
        # Bullish FVG
        if high[i - 1] < low[i + 1]:
            gap_top = low[i + 1]
            gap_bot = high[i - 1]
            if gap_top > gap_bot:
                # Check if filled
                filled = any(low[j] <= gap_bot for j in range(i + 1, n))
                fvgs.append(FairValueGap(
                    fvg_type="bullish", top=float(gap_top), bottom=float(gap_bot),
                    mid=float((gap_top + gap_bot) / 2), index=i, filled=filled,
                ))

        # Bearish FVG
        elif low[i - 1] > high[i + 1]:
            gap_top = low[i - 1]
            gap_bot = high[i + 1]
            if gap_top > gap_bot:
                filled = any(high[j] >= gap_top for j in range(i + 1, n))
                fvgs.append(FairValueGap(
                    fvg_type="bearish", top=float(gap_top), bottom=float(gap_bot),
                    mid=float((gap_top + gap_bot) / 2), index=i, filled=filled,
                ))

    # Return 4 most recent unfilled FVGs closest to current price
    fresh = [f for f in fvgs if not f.filled]
    fresh.sort(key=lambda x: abs(x.mid - price))
    return fresh[:4]

# ─────────────────────────────────────────────
# SMC ENGINE — LIQUIDITY LEVELS
# ─────────────────────────────────────────────
def detect_liquidity(df: pd.DataFrame, lookback: int = 40, tolerance_pct: float = 0.0015) -> List[LiquidityLevel]:
    """
    Equal highs (buy-side liquidity above) and equal lows (sell-side liquidity below).
    Also detects liquidity sweeps: price wicks beyond a level then returns.
    Double liquidity: two consecutive equal highs/lows (stronger pool).
    """
    levels: List[LiquidityLevel] = []
    df_tail = df.tail(lookback).reset_index(drop=True)
    high  = df_tail["High"].values
    low   = df_tail["Low"].values
    close = df_tail["Close"].values
    n = len(df_tail)
    price = close[-1]

    # Detect equal highs (buy-side liquidity)
    for i in range(n - 1):
        for j in range(i + 1, min(i + 10, n)):
            tol = high[i] * tolerance_pct
            if abs(high[i] - high[j]) < tol:
                level_price = float((high[i] + high[j]) / 2)
                # Check if swept (price wicked above but closed below)
                swept = any(high[k] > level_price and close[k] < level_price for k in range(j + 1, n))
                strength = 0.8 if swept else 0.5
                levels.append(LiquidityLevel(
                    liq_type="buy_side", price=level_price, swept=swept, strength=strength
                ))

    # Detect equal lows (sell-side liquidity)
    for i in range(n - 1):
        for j in range(i + 1, min(i + 10, n)):
            tol = low[i] * tolerance_pct
            if abs(low[i] - low[j]) < tol:
                level_price = float((low[i] + low[j]) / 2)
                swept = any(low[k] < level_price and close[k] > level_price for k in range(j + 1, n))
                strength = 0.8 if swept else 0.5
                levels.append(LiquidityLevel(
                    liq_type="sell_side", price=level_price, swept=swept, strength=strength
                ))

    # Deduplicate close levels and return top 5 by strength, sorted by price proximity
    seen = []
    unique = []
    for lv in sorted(levels, key=lambda x: x.strength, reverse=True):
        if not any(abs(lv.price - s) < lv.price * 0.002 for s in seen):
            seen.append(lv.price)
            unique.append(lv)
        if len(unique) >= 5:
            break
    return unique

# ─────────────────────────────────────────────
# SMC ENGINE — SUPPLY & DEMAND ZONES
# ─────────────────────────────────────────────
def detect_supply_demand(df: pd.DataFrame, lookback: int = 60) -> List[SupplyDemandZone]:
    """
    Demand zone: consolidation followed by strong bullish impulse
    Supply zone: consolidation followed by strong bearish impulse
    """
    zones: List[SupplyDemandZone] = []
    df_tail = df.tail(lookback).reset_index(drop=True)
    high  = df_tail["High"].values
    low   = df_tail["Low"].values
    close = df_tail["Close"].values
    open_ = df_tail["Open"].values
    n = len(df_tail)
    if n < 5:
        return zones
    avg_range = float(np.mean(high - low))

    for i in range(2, n - 2):
        move_after = abs(close[min(i + 3, n - 1)] - close[i])
        # Demand: strong bullish candle after base
        if (close[i] > open_[i] and  # bullish candle
                move_after > avg_range * 1.5):
            base_low  = float(min(low[max(0, i - 2): i + 1]))
            base_high = float(close[i])
            strength  = min(1.0, move_after / (avg_range * 4))
            zones.append(SupplyDemandZone(
                zone_type="demand", top=base_high, bottom=base_low,
                mid=(base_high + base_low) / 2, strength=strength,
            ))

        # Supply: strong bearish candle after base
        elif (close[i] < open_[i] and
              move_after > avg_range * 1.5):
            base_low  = float(close[i])
            base_high = float(max(high[max(0, i - 2): i + 1]))
            strength  = min(1.0, move_after / (avg_range * 4))
            zones.append(SupplyDemandZone(
                zone_type="supply", top=base_high, bottom=base_low,
                mid=(base_high + base_low) / 2, strength=strength,
            ))

    # Return top 3 strongest zones
    zones.sort(key=lambda x: x.strength, reverse=True)
    return zones[:3]

# ─────────────────────────────────────────────
# SMC ENGINE — BIAS PER TIMEFRAME
# ─────────────────────────────────────────────
def get_tf_bias(symbol: str, period: str, interval: str) -> str:
    """EMA 20/50 trend bias for any timeframe"""
    try:
        df = fetch_data(symbol, period, interval)
        if df is None or len(df) < 20:
            return "unknown"
        c  = df["Close"]
        e20 = c.ewm(span=20, adjust=False).mean()
        e50 = c.ewm(span=50, adjust=False).mean()
        p = float(c.iloc[-1])
        if p > e20.iloc[-1] > e50.iloc[-1]: return "bullish"
        if p < e20.iloc[-1] < e50.iloc[-1]: return "bearish"
        return "mixed"
    except:
        return "unknown"

# ─────────────────────────────────────────────
# SMC ENGINE — FULL TOP-DOWN ANALYSIS
# ─────────────────────────────────────────────
def run_smc_analysis(symbol: str, entry_tf: str, period_map: dict) -> SMCAnalysis:
    """
    Top-down: Daily → 4H → 1H → Entry TF
    Detect all SMC structures and compute scores.
    """
    # ── Bias per timeframe
    daily_bias = get_tf_bias(symbol, "60d",  "1d")
    h4_bias    = get_tf_bias(symbol, "30d",  "4h" if entry_tf not in ["4h"] else "1d")
    h1_bias    = get_tf_bias(symbol, "10d",  "1h")
    entry_bias = get_tf_bias(symbol, period_map.get(entry_tf, "5d"), entry_tf)

    # ── Fetch entry TF data for SMC detection
    df_entry = fetch_data(symbol, period_map.get(entry_tf, "5d"), entry_tf)
    if df_entry is None or len(df_entry) < 20:
        return SMCAnalysis(
            daily_bias=daily_bias, h4_bias=h4_bias, h1_bias=h1_bias, entry_bias=entry_bias,
            bos_detected=False, choch_detected=False, bos_direction="none",
            df_entry=df_entry,
        )

    # ── Detect swings
    swing_h, swing_l = detect_swings(df_entry)

    # ── BOS / CHOCH
    struct = detect_bos_choch(df_entry, swing_h, swing_l)

    # ── SMC levels
    obs  = detect_order_blocks(df_entry)
    fvgs = detect_fvgs(df_entry)
    liqs = detect_liquidity(df_entry)
    sd   = detect_supply_demand(df_entry)

    # ── Score structure (0-100)
    structure_score = 0.0
    biases = [daily_bias, h4_bias, h1_bias, entry_bias]
    bull_count = biases.count("bullish")
    bear_count = biases.count("bearish")
    alignment  = max(bull_count, bear_count)
    structure_score = (alignment / 4) * 60
    if struct["bos"] or struct["choch"]:
        structure_score += 40
    structure_score = min(100, structure_score)

    # ── Score OBs
    bull_obs = [o for o in obs if o.ob_type == "bullish"]
    bear_obs = [o for o in obs if o.ob_type == "bearish"]
    ob_score = 0.0
    if obs:
        ob_score = min(100, sum(o.strength * 40 for o in obs[:2]))

    # ── Score FVGs
    fvg_score = 0.0
    if fvgs:
        fvg_score = min(100, len(fvgs) * 25.0)

    # ── Score Liquidity
    liq_score = 0.0
    swept_count = sum(1 for l in liqs if l.swept)
    liq_score = min(100, len(liqs) * 15 + swept_count * 20)

    # ── Confluence score: is price near an OB + FVG at the same time?
    price = float(df_entry["Close"].iloc[-1])
    confluence_score = 0.0
    conf_hits = []

    for ob in obs[:2]:
        if ob.bottom <= price <= ob.top * 1.003:
            conf_hits.append(f"{'🟢' if ob.ob_type == 'bullish' else '🔴'} {'Bullish' if ob.ob_type == 'bullish' else 'Bearish'} OB @ {ob.mid:.4f}")
            confluence_score += 30

    for fvg in fvgs[:2]:
        if fvg.bottom <= price <= fvg.top:
            conf_hits.append(f"{'🔵' if fvg.fvg_type == 'bullish' else '🟣'} {'Bullish' if fvg.fvg_type == 'bullish' else 'Bearish'} FVG @ {fvg.mid:.4f}")
            confluence_score += 25

    for lv in liqs:
        dist_pct = abs(price - lv.price) / price
        if dist_pct < 0.003:
            conf_hits.append(f"⚡ Liq @ {lv.price:.4f} ({'swept' if lv.swept else 'unswept'})")
            confluence_score += 20

    for zone in sd:
        if zone.bottom <= price <= zone.top:
            conf_hits.append(f"{'📗' if zone.zone_type == 'demand' else '📕'} {'Demand' if zone.zone_type == 'demand' else 'Supply'} zone @ {zone.mid:.4f}")
            confluence_score += 15

    confluence_score = min(100, confluence_score)
    key_level = " + ".join(conf_hits[:2]) if conf_hits else "No direct confluence"

    return SMCAnalysis(
        daily_bias=daily_bias, h4_bias=h4_bias, h1_bias=h1_bias, entry_bias=entry_bias,
        bos_detected=struct["bos"], choch_detected=struct["choch"],
        bos_direction=struct["bos_direction"],
        order_blocks=obs, fvgs=fvgs, liquidity_levels=liqs, supply_demand=sd,
        structure_score=structure_score, ob_score=ob_score,
        fvg_score=fvg_score, liquidity_score=liq_score,
        confluence_score=confluence_score,
        key_level_type=key_level,
        df_entry=df_entry,
    )

# ─────────────────────────────────────────────
# MAIN SIGNAL ENGINE (SMC + Classic)
# ─────────────────────────────────────────────
def generate_signal(
    symbol, ind, smc: SMCAnalysis,
    balance, risk_pct, min_conf, min_rr,
    atr_sl, atr_tp, hold_mins,
    w_trend, w_mom, w_vol, w_mtf, w_smc,
) -> Optional[TradeSignal]:
    """
    SMC-first signal generation.
    HTF bias must agree. SMC confluence gates the signal.
    Classic indicators act as confirmation.
    """
    buy = sell = 0.0
    t_sc = m_sc = v_sc = mtf_sc = smc_sc = 0.0
    price, atr = ind["price"], ind["atr"]

    # ── 1. HTF BIAS GATE (Daily + 4H must agree for high-quality signal)
    htf_bull = smc.daily_bias == "bullish" and smc.h4_bias in ("bullish", "mixed")
    htf_bear = smc.daily_bias == "bearish" and smc.h4_bias in ("bearish", "mixed")

    if htf_bull:   buy  += 4; mtf_sc = w_mtf
    elif htf_bear: sell += 4; mtf_sc = w_mtf
    elif smc.h4_bias == "bullish": buy  += 2; mtf_sc = w_mtf * 0.5
    elif smc.h4_bias == "bearish": sell += 2; mtf_sc = w_mtf * 0.5
    else: mtf_sc = w_mtf * 0.2

    # ── 2. STRUCTURE (BOS / CHOCH)
    if smc.bos_detected or smc.choch_detected:
        if smc.bos_direction == "bullish":   buy  += 3; t_sc += w_trend * 0.6
        elif smc.bos_direction == "bearish": sell += 3; t_sc += w_trend * 0.6

    # Classic trend EMA
    if ind["trend"] == "bullish":   buy  += 2; t_sc += w_trend * 0.4
    elif ind["trend"] == "bearish": sell += 2; t_sc += w_trend * 0.4

    # ── 3. SMC CONFLUENCE SCORE
    smc_points = smc.confluence_score / 100 * 5   # up to 5 extra points
    # Detect direction from OBs
    bull_obs = [o for o in smc.order_blocks if o.ob_type == "bullish"]
    bear_obs = [o for o in smc.order_blocks if o.ob_type == "bearish"]
    # Price near bullish OB or FVG → buy bias
    for ob in bull_obs:
        if ob.bottom <= price <= ob.top * 1.003:
            buy  += smc_points * 0.5; smc_sc += w_smc * 0.3
    for ob in bear_obs:
        if ob.bottom * 0.997 <= price <= ob.top:
            sell += smc_points * 0.5; smc_sc += w_smc * 0.3
    # FVGs
    for fvg in smc.fvgs:
        if fvg.bottom <= price <= fvg.top:
            if fvg.fvg_type == "bullish": buy  += 1; smc_sc += w_smc * 0.2
            else:                         sell += 1; smc_sc += w_smc * 0.2
    # Liquidity sweep confirmation
    for lv in smc.liquidity_levels:
        if lv.swept:
            dist_pct = abs(price - lv.price) / price
            if dist_pct < 0.004:
                # Sweep below → expecting reversal up
                if lv.liq_type == "sell_side": buy  += 1.5; smc_sc += w_smc * 0.15
                else:                          sell += 1.5; smc_sc += w_smc * 0.15
    # Supply / Demand
    for zone in smc.supply_demand:
        if zone.bottom <= price <= zone.top:
            if zone.zone_type == "demand": buy  += 1; smc_sc += w_smc * 0.1
            else:                          sell += 1; smc_sc += w_smc * 0.1
    smc_sc = min(w_smc, smc_sc)

    # ── 4. CLASSIC MOMENTUM CONFIRMATION
    rsi = ind["rsi"]
    if   rsi < 30:  buy  += 3; m_sc += w_mom * .40
    elif rsi < 45:  buy  += 1.5; m_sc += w_mom * .20
    elif rsi > 70:  sell += 3; m_sc += w_mom * .40
    elif rsi > 55:  sell += 1.5; m_sc += w_mom * .20

    if ind["macd_hist"] > 0: buy  += 1.5; m_sc += w_mom * .25
    else:                    sell += 1.5; m_sc += w_mom * .25

    sk = ind["stoch_k"]
    if   sk < 20: buy  += 1.5; m_sc += w_mom * .20
    elif sk < 40: buy  += .5
    elif sk > 80: sell += 1.5; m_sc += w_mom * .20
    elif sk > 60: sell += .5

    bp = ind["bb_pct"]
    if bp < .15: buy  += 1
    elif bp > .85: sell += 1

    # ── 5. VOLUME
    vr = ind["volume_ratio"]
    if   vr > 2.0: v_sc = w_vol;    buy += 1.5 if buy > sell else 0; sell += 1.5 if sell > buy else 0
    elif vr > 1.5: v_sc = w_vol*.7; buy += 1   if buy > sell else 0; sell += 1   if sell > buy else 0
    elif vr > 1.2: v_sc = w_vol*.4
    else:          v_sc = w_vol*.1

    # ── DIRECTION DECISION
    total = buy + sell
    if total == 0:
        return None
    if buy > sell and buy >= 6:
        direction = SignalType.BUY
        conf = min(93, int((buy / total) * 100))
    elif sell > buy and sell >= 6:
        direction = SignalType.SELL
        conf = min(93, int((sell / total) * 100))
    else:
        return None

    # ── SMC confluence bonus on confidence
    conf = min(96, conf + int(smc.confluence_score * 0.08))

    if conf < min_conf:
        return None

    # ── TRADE LEVELS (ATR-based, biased toward SMC levels)
    if direction == SignalType.BUY:
        # Try to use nearest bullish OB bottom as SL if available
        ob_sl = None
        for ob in bull_obs:
            if ob.bottom < price:
                ob_sl = ob.bottom * 0.9995
                break
        sl = ob_sl if ob_sl and abs(price - ob_sl) < atr * atr_sl * 2 else price - atr * atr_sl
        tp = price + atr * atr_tp
    else:
        ob_sl = None
        for ob in bear_obs:
            if ob.top > price:
                ob_sl = ob.top * 1.0005
                break
        sl = ob_sl if ob_sl and abs(price - ob_sl) < atr * atr_sl * 2 else price + atr * atr_sl
        tp = price - atr * atr_tp

    risk   = abs(price - sl)
    reward = abs(tp - price)
    rr     = reward / risk if risk > 0 else 0
    if rr < min_rr:
        return None

    pip_val = INSTRUMENTS[symbol]["pip"] / 100
    lot     = round(min(10, max(0.01, (balance * (risk_pct / 100)) / (risk * 100 * pip_val))), 2)

    h_now = datetime.utcnow().hour
    session = "London 🇬🇧" if 8 <= h_now < 16 else "New York 🇺🇸" if 13 <= h_now < 21 else "Asian 🌏"

    return TradeSignal(
        signal=direction, pair=INSTRUMENTS[symbol]["name"], symbol=symbol,
        entry=price, stop_loss=sl, take_profit=tp, confidence=conf,
        risk_reward=round(rr, 2), lot_size=lot, session=session,
        timestamp=datetime.now(), expiry=datetime.now() + timedelta(minutes=hold_mins),
        rsi=rsi, macd_hist=ind["macd_hist"], stoch_k=sk,
        volume_ratio=ind["volume_ratio"], trend=ind["trend"],
        htf_bias=smc.h4_bias, atr=atr, bb_pct=bp,
        trend_score=t_sc, momentum_score=m_sc, volume_score=v_sc,
        mtf_score=mtf_sc, smc_score=smc_sc,
        smc_confluence_score=smc.confluence_score,
        key_level_type=smc.key_level_type,
        daily_bias=smc.daily_bias, h4_bias=smc.h4_bias,
    )

# ─────────────────────────────────────────────
# PLOTLY CANDLESTICK CHART WITH SMC DRAWINGS
# ─────────────────────────────────────────────
def build_smc_chart(df: pd.DataFrame, smc: SMCAnalysis, signal: Optional[TradeSignal],
                    symbol: str, timeframe: str) -> go.Figure:
    """
    Plotly candlestick with:
    - Order Block rectangles (green/red shaded)
    - FVG rectangles (blue/purple shaded)
    - Liquidity horizontal lines (gold dashed)
    - Supply/Demand zone rectangles
    - Entry / SL / TP horizontal lines
    - EMA 20, EMA 50
    """
    df_tail = df.tail(80).copy().reset_index()
    # Plotly needs datetime index
    if "Datetime" in df_tail.columns:
        x_axis = df_tail["Datetime"]
    elif "Date" in df_tail.columns:
        x_axis = df_tail["Date"]
    else:
        x_axis = df_tail.index

    fig = go.Figure()

    # ── Candlesticks
    fig.add_trace(go.Candlestick(
        x=x_axis,
        open=df_tail["Open"], high=df_tail["High"],
        low=df_tail["Low"],   close=df_tail["Close"],
        name="Price",
        increasing_line_color="#3fb950", increasing_fillcolor="#1a3a20",
        decreasing_line_color="#f85149", decreasing_fillcolor="#3a1a1a",
        line_width=1,
    ))

    # ── EMA 20 & 50
    ema20 = df_tail["Close"].ewm(span=20, adjust=False).mean()
    ema50 = df_tail["Close"].ewm(span=50, adjust=False).mean()
    fig.add_trace(go.Scatter(x=x_axis, y=ema20, name="EMA 20",
                             line=dict(color="#58a6ff", width=1.2, dash="solid"), opacity=.7))
    fig.add_trace(go.Scatter(x=x_axis, y=ema50, name="EMA 50",
                             line=dict(color="#d29922", width=1.2, dash="solid"), opacity=.7))

    x0_chart = x_axis.iloc[0]
    x1_chart = x_axis.iloc[-1]

    # ── Order Blocks
    for ob in smc.order_blocks[:3]:
        clr = "rgba(63,185,80,0.12)" if ob.ob_type == "bullish" else "rgba(248,81,73,0.12)"
        border_clr = "#238636" if ob.ob_type == "bullish" else "#da3633"
        fig.add_hrect(y0=ob.bottom, y1=ob.top, x0=x0_chart, x1=x1_chart,
                      fillcolor=clr, line=dict(color=border_clr, width=1, dash="dot"),
                      annotation_text=f"{'Bull' if ob.ob_type=='bullish' else 'Bear'} OB",
                      annotation_position="top left",
                      annotation_font=dict(size=9, color=border_clr))

    # ── Fair Value Gaps
    for fvg in smc.fvgs[:3]:
        clr = "rgba(88,166,255,0.10)" if fvg.fvg_type == "bullish" else "rgba(188,140,255,0.10)"
        border_clr = "#58a6ff" if fvg.fvg_type == "bullish" else "#bc8cff"
        fig.add_hrect(y0=fvg.bottom, y1=fvg.top, x0=x0_chart, x1=x1_chart,
                      fillcolor=clr, line=dict(color=border_clr, width=0.8, dash="dot"),
                      annotation_text=f"{'Bull' if fvg.fvg_type=='bullish' else 'Bear'} FVG",
                      annotation_position="bottom right",
                      annotation_font=dict(size=9, color=border_clr))

    # ── Liquidity levels
    for lv in smc.liquidity_levels[:4]:
        clr  = "#d29922" if not lv.swept else "#8b949e"
        dash = "dash" if not lv.swept else "dot"
        label = f"{'Buy Liq' if lv.liq_type=='buy_side' else 'Sell Liq'}" + (" ✓swept" if lv.swept else "")
        fig.add_hline(y=lv.price, line=dict(color=clr, width=1, dash=dash),
                      annotation_text=label,
                      annotation_font=dict(size=9, color=clr),
                      annotation_position="top right")

    # ── Supply / Demand zones
    for zone in smc.supply_demand[:2]:
        clr = "rgba(63,185,80,0.08)" if zone.zone_type == "demand" else "rgba(248,81,73,0.08)"
        border = "#3fb950" if zone.zone_type == "demand" else "#f85149"
        fig.add_hrect(y0=zone.bottom, y1=zone.top, x0=x0_chart, x1=x1_chart,
                      fillcolor=clr, line=dict(color=border, width=0.8, dash="longdash"),
                      annotation_text=f"{'Demand' if zone.zone_type=='demand' else 'Supply'}",
                      annotation_font=dict(size=9, color=border),
                      annotation_position="bottom left")

    # ── Signal levels
    if signal:
        entry_clr = "#e8eaf6"
        sl_clr    = "#f85149"
        tp_clr    = "#3fb950"
        fig.add_hline(y=signal.entry, line=dict(color=entry_clr, width=1.5, dash="solid"),
                      annotation_text=f"Entry {signal.entry:.2f}",
                      annotation_font=dict(size=10, color=entry_clr),
                      annotation_position="right")
        fig.add_hline(y=signal.stop_loss, line=dict(color=sl_clr, width=1.5, dash="dash"),
                      annotation_text=f"SL {signal.stop_loss:.2f}",
                      annotation_font=dict(size=10, color=sl_clr),
                      annotation_position="right")
        fig.add_hline(y=signal.take_profit, line=dict(color=tp_clr, width=1.5, dash="dash"),
                      annotation_text=f"TP {signal.take_profit:.2f}",
                      annotation_font=dict(size=10, color=tp_clr),
                      annotation_position="right")

    # ── Chart layout
    fig.update_layout(
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1117",
        font=dict(family="Inter", color="#8b949e"),
        xaxis=dict(
            gridcolor="#1e2d40", showgrid=True,
            rangeslider=dict(visible=False),
            type="category" if len(df_tail) < 100 else "-",
        ),
        yaxis=dict(gridcolor="#1e2d40", showgrid=True, side="right"),
        legend=dict(bgcolor="#0d1117", bordercolor="#1e2d40", borderwidth=1,
                    font=dict(size=11), orientation="h", yanchor="bottom", y=1.01),
        margin=dict(l=10, r=60, t=30, b=10),
        height=480,
        title=dict(
            text=f"{INSTRUMENTS[symbol]['emoji']} {INSTRUMENTS[symbol]['name']} · {timeframe.upper()} · SMC Analysis",
            font=dict(size=13, color="#c9d1d9"),
            x=0,
        ),
    )
    return fig

# ─────────────────────────────────────────────
# TELEGRAM — enhanced with SMC levels
# ─────────────────────────────────────────────
def send_telegram(signal: TradeSignal, token: str, chat_id: str) -> bool:
    if not token or not chat_id:
        return False
    dec      = INSTRUMENTS[signal.symbol]["dec"]
    icon     = "🟢⚡" if signal.signal == SignalType.BUY else "🔴⚡"
    strength = "🔥 STRONG" if signal.confidence >= 82 else "⚡ GOOD" if signal.confidence >= 70 else "📊 MODERATE"
    msg = f"""{icon} <b>{signal.signal.value} — {signal.pair}</b>

<b>{strength} · {signal.confidence}% confidence</b>

💰 <b>Trade Levels</b>
• Entry:        <code>{signal.entry:.{dec}f}</code>
• Stop Loss:    <code>{signal.stop_loss:.{dec}f}</code>
• Take Profit:  <code>{signal.take_profit:.{dec}f}</code>
• Risk / Reward: 1:{signal.risk_reward:.1f}

🏛️ <b>SMC Analysis</b>
• Daily Bias:  {signal.daily_bias.upper()}
• 4H Bias:     {signal.h4_bias.upper()}
• SMC Score:   {signal.smc_confluence_score:.0f}/100
• Key Level:   {signal.key_level_type}

📊 <b>Classic Confluence</b>
• RSI: {signal.rsi:.1f}  |  MACD: {signal.macd_hist:+.4f}
• Stoch: {signal.stoch_k:.1f}  |  Vol: {signal.volume_ratio:.1f}x
• Trend: {signal.trend.upper()}

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
# UI HELPER FUNCTIONS
# ─────────────────────────────────────────────
def badge(text: str, color: str = "gray") -> str:
    cls = {"green":"badge-green","red":"badge-red","gray":"badge-gray",
           "yellow":"badge-yellow","purple":"badge-purple",
           "blue":"badge-blue","orange":"badge-orange"}.get(color, "badge-gray")
    return f'<span class="badge {cls}">{text}</span>'

def score_bar(label: str, score: float, max_w: float, clr: str) -> str:
    pct = min(100, int(score / max(max_w, 1) * 100))
    return f"""<div class="score-bar-wrap">
  <div class="score-bar-row"><span>{label}</span><span style="color:#8b949e;">{int(score)} / {int(max_w)}</span></div>
  <div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct}%;background:{clr};"></div></div>
</div>"""

def bias_pill(label: str, bias: str) -> str:
    cls = {"bullish":"bias-bull","bearish":"bias-bear"}.get(bias,"bias-neut")
    icon = "🟢" if bias=="bullish" else "🔴" if bias=="bearish" else "⚪"
    return f'<span class="bias-pill {cls}">{icon} {label}: {bias.upper()}</span>'

def smc_strength_meter(smc: SMCAnalysis) -> str:
    bars = [
        ("Structure", smc.structure_score,  "#3fb950"),
        ("OB",        smc.ob_score,          "#58a6ff"),
        ("FVG",       smc.fvg_score,         "#bc8cff"),
        ("Liquidity", smc.liquidity_score,   "#d29922"),
        ("Confluence",smc.confluence_score,  "#f0883e"),
    ]
    items = ""
    for label, score, clr in bars:
        h = max(4, int(score * 0.6))  # max 60px
        items += f"""<div class="smc-bar-wrap">
  <div class="smc-bar-label">{label}</div>
  <div class="smc-bar-outer" style="height:60px;">
    <div class="smc-bar-inner" style="height:{h}px;background:{clr};"></div>
  </div>
  <div style="font-size:10px;color:{clr};margin-top:3px;font-weight:600;">{int(score)}</div>
</div>"""
    return f'<div class="smc-meter">{items}</div>'

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [
    ("history", []), ("last_result", None), ("last_smc", None),
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
    st.markdown("## 🥇 ScalpBot Pro v3")
    st.markdown('<p style="color:#8b949e;font-size:.8rem;margin-top:-8px;">ICT/SMC Top-Down Edition</p>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:.4rem;">Instrument & Timeframe</p>', unsafe_allow_html=True)
    symbol = st.selectbox(
        "Instrument", list(INSTRUMENTS.keys()),
        format_func=lambda x: f"{INSTRUMENTS[x]['emoji']}  {INSTRUMENTS[x]['name']}"
    )
    timeframe = st.selectbox("Timeframe", ["1h", "30m", "15m", "5m"], index=0)
    period_map = {"1h": "5d", "30m": "3d", "15m": "2d", "5m": "1d"}

    st.markdown("---")
    st.markdown('<p style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:.4rem;">Risk Management</p>', unsafe_allow_html=True)
    balance  = st.number_input("Account Balance ($)", 10.0, 1_000_000.0, 100.0, 10.0)
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 0.5, 0.1)
    min_conf = st.slider("Min Confidence (%)", 50, 92, 65, 5)
    min_rr   = st.slider("Min Risk / Reward", 1.0, 4.0, 1.5, 0.1)
    atr_sl   = st.slider("ATR Stop-Loss ×", 0.5, 3.0, 1.0, 0.1)
    atr_tp   = st.slider("ATR Take-Profit ×", 0.5, 6.0, 2.0, 0.1)
    hold_mins= st.slider("Signal Expiry (min)", 5, 240, 60, 5)

    st.markdown("---")
    st.markdown('<p style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:.4rem;">Signal Weights</p>', unsafe_allow_html=True)
    w_trend = st.slider("Trend / Structure", 0, 30, 20, 5)
    w_mom   = st.slider("Momentum (RSI+MACD+Stoch)", 0, 30, 20, 5)
    w_vol   = st.slider("Volume", 0, 20, 15, 5)
    w_mtf   = st.slider("Multi-TF Bias", 0, 30, 20, 5)
    w_smc   = st.slider("SMC Confluence", 0, 40, 30, 5)

    st.markdown("---")
    st.markdown('<p style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:.4rem;">Telegram Alerts</p>', unsafe_allow_html=True)
    tg_token   = st.text_input("Bot Token",  type="password", placeholder="123456:ABC-xxx")
    tg_chat_id = st.text_input("Chat ID",    placeholder="Your chat ID")
    if st.button("🔔 Test Telegram", use_container_width=True):
        if tg_token and tg_chat_id:
            try:
                r = requests.post(
                    f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    json={"chat_id": tg_chat_id, "text": "✅ ScalpBot Pro v3 connected! SMC/ICT engine ready."},
                    timeout=10,
                )
                st.success("✅ Connected!") if r.ok else st.error("❌ " + r.json().get("description", "Failed"))
            except:
                st.error("❌ Network error")
        else:
            st.warning("Enter token & chat ID first")

    st.markdown("---")
    st.markdown('<p style="font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:.4rem;">Auto-Send Interval</p>', unsafe_allow_html=True)
    auto_interval = st.select_slider(
        "", options=[60, 120, 300, 600, 900],
        value=st.session_state.auto_interval,
        format_func=lambda x: f"{x // 60} min" if x >= 60 else f"{x}s",
    )
    st.session_state.auto_interval = auto_interval

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
pair_info = INSTRUMENTS[symbol]
h_now     = datetime.utcnow().hour
session_now = "London 🇬🇧" if 8 <= h_now < 16 else "New York 🇺🇸" if 13 <= h_now < 21 else "Asian 🌏"

st.markdown(f"""
<div class="hero">
  <h1>🥇 ScalpBot Pro <span style="color:#3fb950;">v3</span></h1>
  <p>ICT/SMC Top-Down Engine &nbsp;·&nbsp; {pair_info['emoji']} {pair_info['name']}
     &nbsp;·&nbsp; {timeframe.upper()} chart &nbsp;·&nbsp; {session_now}
     &nbsp;·&nbsp; {datetime.utcnow().strftime('%H:%M UTC')}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTO-SEND PANEL
# ─────────────────────────────────────────────
auto_col1, auto_col2 = st.columns([4, 1])
with auto_col1:
    panel_cls = "auto-panel active" if st.session_state.auto_on else "auto-panel"
    auto_label = "🟢 AUTO-SEND  ON" if st.session_state.auto_on else "⚫ AUTO-SEND  OFF"
    if st.session_state.auto_on and st.session_state.next_run:
        secs_left = max(0, int((st.session_state.next_run - datetime.now()).total_seconds()))
        m_, s_ = divmod(secs_left, 60)
        countdown_html = f'<span class="countdown">{m_:02d}:{s_:02d}</span> <span style="color:#8b949e;font-size:.82rem;">until next analysis</span>'
    else:
        countdown_html = '<span style="color:#8b949e;font-size:.88rem;">Toggle to start sending signals automatically</span>'
    st.markdown(f"""
    <div class="{panel_cls}">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-weight:700;font-size:.95rem;color:{'#3fb950' if st.session_state.auto_on else '#8b949e'};">{auto_label}</div>
          <div style="margin-top:.3rem;">{countdown_html}</div>
        </div>
        <div style="text-align:right;font-size:11.5px;color:#8b949e;">
          Interval: {auto_interval//60}m &nbsp;|&nbsp; Sent: {st.session_state.total_sent}
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

with auto_col2:
    st.write("")
    st.write("")
    toggle_label = "⏹ Stop" if st.session_state.auto_on else "▶ Start Auto"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.auto_on = not st.session_state.auto_on
        st.session_state.next_run = datetime.now() if st.session_state.auto_on else None
        st.rerun()

# ─────────────────────────────────────────────
# MANUAL BUTTON ROW
# ─────────────────────────────────────────────
b1, b2, b3 = st.columns([3, 1, 2])
with b1:
    manual_run = st.button("🚀 Run Full SMC Analysis & Generate Signal", use_container_width=True, type="primary")
with b2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_result = None
        st.session_state.last_smc = None
        st.session_state.total_sent = 0
        st.rerun()

# ─────────────────────────────────────────────
# TRIGGER LOGIC
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
    with st.spinner("Running SMC top-down analysis (Daily → 4H → 1H → Entry TF)..."):
        fetch_data.clear()
        smc_result = run_smc_analysis(symbol, timeframe, period_map)
        df_entry   = fetch_data(symbol, period_map[timeframe], timeframe)
        ind        = compute_indicators(df_entry) if df_entry is not None else None

    if ind is None or df_entry is None:
        st.error("⚠️ Could not fetch market data. Check instrument/timeframe.")
    else:
        with st.spinner("Generating signal..."):
            sig = generate_signal(
                symbol, ind, smc_result,
                balance, risk_pct, min_conf, min_rr, atr_sl, atr_tp, hold_mins,
                w_trend, w_mom, w_vol, w_mtf, w_smc,
            )
        st.session_state.last_result = (sig, ind, smc_result)
        st.session_state.last_smc    = smc_result

        if sig:
            st.session_state.history.insert(0, sig)
            if len(st.session_state.history) > 30:
                st.session_state.history = st.session_state.history[:30]
            tg_ok = send_telegram(sig, tg_token, tg_chat_id)
            st.session_state.last_tg_status = (
                "✅ Signal sent to Telegram!" if tg_ok
                else ("⚠️ No Telegram configured" if not tg_token else "❌ Telegram send failed")
            )
            st.session_state.total_sent += 1
        else:
            st.session_state.last_tg_status = None

# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────
if st.session_state.last_result:
    sig, ind, smc_result = st.session_state.last_result
    dec = INSTRUMENTS[symbol]["dec"]

    # Toast
    if st.session_state.last_tg_status:
        cls = "toast-success" if "✅" in st.session_state.last_tg_status else "toast-fail"
        st.markdown(f'<div class="{cls}">{st.session_state.last_tg_status}</div>', unsafe_allow_html=True)

    # ── TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Signal", "🏛️ SMC Analysis", "📈 Chart", "📋 History"])

    # ════════════════════════════════════════════
    # TAB 1 — SIGNAL
    # ════════════════════════════════════════════
    with tab1:
        # Snapshot metrics
        st.markdown('<p class="section-title" style="margin-top:.8rem;">Live Market Snapshot</p>', unsafe_allow_html=True)
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Price",      f"{ind['price']:.{dec}f}")
        m2.metric("RSI (14)",   f"{ind['rsi']:.1f}",
                  delta="Oversold" if ind['rsi'] < 30 else "Overbought" if ind['rsi'] > 70 else None)
        m3.metric("MACD",       f"{ind['macd_hist']:+.4f}",
                  delta="Bullish" if ind['macd_hist'] > 0 else "Bearish")
        m4.metric("Stoch %K",   f"{ind['stoch_k']:.1f}")
        m5.metric("1H Trend",   ind['trend'].title())
        m6.metric("Vol Ratio",  f"{ind['volume_ratio']:.2f}x",
                  delta="Spike!" if ind['volume_ratio'] > 1.5 else None)

        # Signal card
        if sig:
            is_buy  = sig.signal == SignalType.BUY
            clr_val = "#3fb950" if is_buy else "#f85149"
            css     = "signal-buy" if is_buy else "signal-sell"
            glow    = "glow-buy"  if is_buy else "glow-sell"
            icon    = "🟢 BUY"   if is_buy else "🔴 SELL"
            conf_c  = "#3fb950" if sig.confidence >= 75 else "#d29922" if sig.confidence >= 60 else "#f85149"
            strength = ("🔥 Strong SMC Signal" if sig.confidence >= 82
                        else "⚡ Good Signal" if sig.confidence >= 70 else "📊 Moderate Signal")
            st.markdown(f"""
<div class="signal-card {css}">
  <div class="{glow}"></div>
  <div class="sig-title" style="color:{clr_val};">{icon}</div>
  <div class="sig-sub">{pair_info['emoji']} {pair_info['name']} &nbsp;·&nbsp; {timeframe.upper()}
    &nbsp;·&nbsp; <span style="color:{conf_c};font-weight:600;">{sig.confidence}% confidence</span>
    &nbsp;·&nbsp; {strength} &nbsp;·&nbsp; {sig.session}</div>
  <div class="sig-grid">
    <div class="sig-item"><div class="label">Entry</div><div class="value">{sig.entry:.{dec}f}</div></div>
    <div class="sig-item"><div class="label">Stop Loss</div><div class="value red">{sig.stop_loss:.{dec}f}</div></div>
    <div class="sig-item"><div class="label">Take Profit</div><div class="value green">{sig.take_profit:.{dec}f}</div></div>
    <div class="sig-item"><div class="label">Risk / Reward</div><div class="value">1 : {sig.risk_reward}</div></div>
    <div class="sig-item"><div class="label">Lot Size</div><div class="value">{sig.lot_size}</div></div>
    <div class="sig-item"><div class="label">Expires</div><div class="value">{sig.expiry.strftime('%H:%M UTC')}</div></div>
    <div class="sig-item"><div class="label">Daily Bias</div><div class="value {'green' if sig.daily_bias=='bullish' else 'red' if sig.daily_bias=='bearish' else ''}">{sig.daily_bias.upper()}</div></div>
    <div class="sig-item"><div class="label">4H Bias</div><div class="value {'green' if sig.h4_bias=='bullish' else 'red' if sig.h4_bias=='bearish' else ''}">{sig.h4_bias.upper()}</div></div>
    <div class="sig-item"><div class="label">Key Level</div><div class="value" style="font-size:.78rem;color:#d29922;">{sig.key_level_type[:30] + '…' if len(sig.key_level_type) > 30 else sig.key_level_type}</div></div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
<div class="signal-card signal-hold">
  <div class="sig-title" style="color:#8b949e;">⚖️ HOLD — No Signal</div>
  <div class="sig-sub">SMC analysis complete but no high-probability confluence found at this price.
  Wait for price to reach a key Order Block, FVG, or Liquidity level before re-analyzing.</div>
</div>""", unsafe_allow_html=True)

        # Two columns: indicators + scores
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<p class="section-title">All Indicators</p>', unsafe_allow_html=True)
            rsi_c = "green" if ind['rsi'] < 40 else "red" if ind['rsi'] > 60 else "gray"
            mcd_c = "green" if ind['macd_hist'] > 0 else "red"
            sk_c  = "green" if ind['stoch_k'] < 30 else "red" if ind['stoch_k'] > 70 else "gray"
            tr_c  = "green" if ind['trend'] == "bullish" else "red" if ind['trend'] == "bearish" else "gray"
            ht_c  = "green" if smc_result.h4_bias == "bullish" else "red" if smc_result.h4_bias == "bearish" else "gray"
            vl_c  = "green" if ind['volume_ratio'] > 1.5 else "gray"
            bb_c  = "green" if ind['bb_pct'] < .2 else "red" if ind['bb_pct'] > .8 else "gray"
            dl_c  = "green" if smc_result.daily_bias == "bullish" else "red" if smc_result.daily_bias == "bearish" else "gray"

            ind_rows = [
                ("RSI (14)",       f"{ind['rsi']:.1f}",           rsi_c),
                ("MACD Histogram", f"{ind['macd_hist']:+.5f}",    mcd_c),
                ("Stochastic %K",  f"{ind['stoch_k']:.1f}",       sk_c),
                ("Bollinger %B",   f"{ind['bb_pct']*100:.1f}%",   bb_c),
                ("ATR (14)",       f"{ind['atr']:.{dec}f}",       "gray"),
                ("EMA 20",         f"{ind['ema20']:.{dec}f}",     "gray"),
                ("EMA 50",         f"{ind['ema50']:.{dec}f}",     "gray"),
                ("Volume Ratio",   f"{ind['volume_ratio']:.2f}x", vl_c),
                ("Daily Bias",     smc_result.daily_bias.title(), dl_c),
                ("4H Bias",        smc_result.h4_bias.title(),    ht_c),
                ("1H Bias",        smc_result.h1_bias.title(),
                 "green" if smc_result.h1_bias=="bullish" else "red" if smc_result.h1_bias=="bearish" else "gray"),
            ]
            html = ""
            for n_, v_, c_ in ind_rows:
                html += f'<div class="ind-row"><span class="ind-label">{n_}</span>{badge(v_, c_)}</div>'
            st.markdown(html, unsafe_allow_html=True)

        with col_b:
            st.markdown('<p class="section-title">Score Breakdown</p>', unsafe_allow_html=True)
            if sig:
                bars_html = ""
                bars_html += score_bar("Trend / Structure",          sig.trend_score,    w_trend,     "#3fb950")
                bars_html += score_bar("Momentum (RSI+MACD+Stoch)",  sig.momentum_score, w_mom * 1.3, "#58a6ff")
                bars_html += score_bar("Volume Confirmation",         sig.volume_score,   w_vol,       "#d29922")
                bars_html += score_bar("Multi-TF Bias",               sig.mtf_score,      w_mtf,       "#bc8cff")
                bars_html += score_bar("SMC Confluence",              sig.smc_score,      w_smc,       "#f0883e")

                conf     = sig.confidence
                conf_clr = "#3fb950" if conf >= 75 else "#d29922" if conf >= 60 else "#f85149"
                bars_html += f"""
<div style="background:#0d1117;border:1px solid #1e2d40;border-radius:10px;padding:1rem;margin-top:.8rem;">
  <div style="display:flex;justify-content:space-between;font-weight:600;margin-bottom:8px;font-size:.88rem;">
    <span>Overall Confidence</span>
    <span style="color:{conf_clr};">{conf}%</span>
  </div>
  <div style="background:#1e2d40;border-radius:6px;height:10px;">
    <div style="width:{conf}%;background:{conf_clr};height:10px;border-radius:6px;"></div>
  </div>
</div>"""
                st.markdown(bars_html, unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.88rem;margin-top:.5rem;">Run an analysis to see score breakdown.</p>', unsafe_allow_html=True)

            # SMC Strength Meter
            st.markdown('<p class="section-title" style="margin-top:1rem;">SMC Strength Meter</p>', unsafe_allow_html=True)
            st.markdown(smc_strength_meter(smc_result), unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 2 — SMC ANALYSIS
    # ════════════════════════════════════════════
    with tab2:
        st.markdown('<p class="section-title" style="margin-top:.6rem;">Top-Down Bias</p>', unsafe_allow_html=True)
        bias_html = '<div class="bias-row">'
        bias_html += bias_pill("Daily", smc_result.daily_bias)
        bias_html += bias_pill("4H",    smc_result.h4_bias)
        bias_html += bias_pill("1H",    smc_result.h1_bias)
        bias_html += bias_pill(f"{timeframe.upper()} Entry", smc_result.entry_bias)
        bias_html += '</div>'
        st.markdown(bias_html, unsafe_allow_html=True)

        # Structure events
        struct_col1, struct_col2 = st.columns(2)
        with struct_col1:
            st.markdown('<p class="section-title">Market Structure</p>', unsafe_allow_html=True)
            if smc_result.bos_detected:
                dir_c = "green" if smc_result.bos_direction == "bullish" else "red"
                st.markdown(f'{badge("BOS Detected", dir_c)} &nbsp; {badge(smc_result.bos_direction.upper(), dir_c)}', unsafe_allow_html=True)
            if smc_result.choch_detected:
                dir_c = "green" if smc_result.bos_direction == "bullish" else "red"
                st.markdown(f'{badge("CHOCH Detected", "orange")} &nbsp; {badge(smc_result.bos_direction.upper(), dir_c)}', unsafe_allow_html=True)
            if not smc_result.bos_detected and not smc_result.choch_detected:
                st.markdown(f'{badge("No BOS/CHOCH", "gray")}', unsafe_allow_html=True)

        with struct_col2:
            st.markdown('<p class="section-title">Key Confluence</p>', unsafe_allow_html=True)
            kl = smc_result.key_level_type
            if kl and kl != "None" and kl != "No direct confluence":
                for part in kl.split(" + "):
                    st.markdown(f'<div style="font-size:12.5px;color:#d29922;margin-bottom:3px;">{part}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.85rem;">Price not at a key SMC level right now.</p>', unsafe_allow_html=True)

        st.markdown("---")

        # SMC Levels — 4 sub-columns
        lc1, lc2 = st.columns(2)

        with lc1:
            st.markdown('<p class="section-title">Order Blocks</p>', unsafe_allow_html=True)
            if smc_result.order_blocks:
                for ob in smc_result.order_blocks[:4]:
                    css_  = "ob-bull" if ob.ob_type == "bullish" else "ob-bear"
                    icon_ = "🟢" if ob.ob_type == "bullish" else "🔴"
                    st.markdown(f"""
<div class="smc-level-card {css_}">
  <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
    <span style="font-weight:600;font-size:12.5px;">{icon_} {'Bullish' if ob.ob_type=='bullish' else 'Bearish'} OB</span>
    {badge(f"Str: {ob.strength:.0%}", 'green' if ob.strength > 0.6 else 'yellow')}
  </div>
  <div style="font-size:12px;color:#8b949e;">Top: {ob.top:.{dec}f} &nbsp;|&nbsp; Bot: {ob.bottom:.{dec}f} &nbsp;|&nbsp; Mid: {ob.mid:.{dec}f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.85rem;">No fresh order blocks detected.</p>', unsafe_allow_html=True)

            st.markdown('<p class="section-title" style="margin-top:.8rem;">Supply & Demand Zones</p>', unsafe_allow_html=True)
            if smc_result.supply_demand:
                for zone in smc_result.supply_demand[:3]:
                    css_  = "sd-bull" if zone.zone_type == "demand" else "sd-bear"
                    icon_ = "📗" if zone.zone_type == "demand" else "📕"
                    st.markdown(f"""
<div class="smc-level-card {css_}">
  <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
    <span style="font-weight:600;font-size:12.5px;">{icon_} {'Demand' if zone.zone_type=='demand' else 'Supply'} Zone</span>
    {badge(f"Str: {zone.strength:.0%}", 'green' if zone.strength > 0.6 else 'yellow')}
  </div>
  <div style="font-size:12px;color:#8b949e;">Top: {zone.top:.{dec}f} &nbsp;|&nbsp; Bot: {zone.bottom:.{dec}f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.85rem;">No zones detected.</p>', unsafe_allow_html=True)

        with lc2:
            st.markdown('<p class="section-title">Fair Value Gaps (FVG)</p>', unsafe_allow_html=True)
            if smc_result.fvgs:
                for fvg in smc_result.fvgs[:4]:
                    css_  = "fvg-bull" if fvg.fvg_type == "bullish" else "fvg-bear"
                    icon_ = "🔵" if fvg.fvg_type == "bullish" else "🟣"
                    st.markdown(f"""
<div class="smc-level-card {css_}">
  <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
    <span style="font-weight:600;font-size:12.5px;">{icon_} {'Bullish' if fvg.fvg_type=='bullish' else 'Bearish'} FVG</span>
    {badge('Unfilled', 'blue')}
  </div>
  <div style="font-size:12px;color:#8b949e;">Top: {fvg.top:.{dec}f} &nbsp;|&nbsp; Bot: {fvg.bottom:.{dec}f} &nbsp;|&nbsp; Mid: {fvg.mid:.{dec}f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.85rem;">No unfilled FVGs detected.</p>', unsafe_allow_html=True)

            st.markdown('<p class="section-title" style="margin-top:.8rem;">Liquidity Levels</p>', unsafe_allow_html=True)
            if smc_result.liquidity_levels:
                for lv in smc_result.liquidity_levels[:5]:
                    css_  = "liq"
                    icon_ = "⬆️" if lv.liq_type == "buy_side" else "⬇️"
                    swept_b = badge("Swept ✓", "orange") if lv.swept else badge("Unswept", "gray")
                    st.markdown(f"""
<div class="smc-level-card {css_}">
  <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
    <span style="font-weight:600;font-size:12.5px;">{icon_} {'Buy-Side Liq' if lv.liq_type=='buy_side' else 'Sell-Side Liq'}</span>
    {swept_b}
  </div>
  <div style="font-size:12px;color:#8b949e;">Price: {lv.price:.{dec}f} &nbsp;|&nbsp; Strength: {lv.strength:.0%}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.85rem;">No liquidity levels detected.</p>', unsafe_allow_html=True)

        # Confluence summary table
        st.markdown("---")
        st.markdown('<p class="section-title">SMC Confluence Summary</p>', unsafe_allow_html=True)
        table_rows = [
            ("Structure",  f"BOS: {'✅' if smc_result.bos_detected else '❌'} / CHOCH: {'✅' if smc_result.choch_detected else '❌'}",  f"{smc_result.structure_score:.0f}/100"),
            ("Order Blocks", f"{len(smc_result.order_blocks)} detected ({len([o for o in smc_result.order_blocks if o.ob_type=='bullish'])} bull / {len([o for o in smc_result.order_blocks if o.ob_type=='bearish'])} bear)", f"{smc_result.ob_score:.0f}/100"),
            ("Fair Value Gaps", f"{len(smc_result.fvgs)} unfilled",           f"{smc_result.fvg_score:.0f}/100"),
            ("Liquidity",  f"{len(smc_result.liquidity_levels)} levels ({sum(1 for l in smc_result.liquidity_levels if l.swept)} swept)", f"{smc_result.liquidity_score:.0f}/100"),
            ("Confluence", smc_result.key_level_type[:45] + ("…" if len(smc_result.key_level_type) > 45 else ""), f"{smc_result.confluence_score:.0f}/100"),
        ]
        table_html = '<table class="conf-table"><tr><th>Factor</th><th>Detail</th><th>Score</th></tr>'
        for factor, detail, score in table_rows:
            table_html += f"<tr><td>{factor}</td><td>{detail}</td><td><b>{score}</b></td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 3 — PLOTLY CHART
    # ════════════════════════════════════════════
    with tab3:
        df_chart = fetch_data(symbol, period_map[timeframe], timeframe)
        if df_chart is not None and len(df_chart) >= 10:
            fig = build_smc_chart(df_chart, smc_result, sig, symbol, timeframe)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        else:
            st.warning("Not enough data to draw the chart.")

        # Legend
        st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:14px;font-size:11.5px;color:#8b949e;margin-top:.5rem;">
  <span><span style="color:#238636;">■</span> Bullish OB</span>
  <span><span style="color:#da3633;">■</span> Bearish OB</span>
  <span><span style="color:#58a6ff;">■</span> Bullish FVG</span>
  <span><span style="color:#bc8cff;">■</span> Bearish FVG</span>
  <span><span style="color:#d29922;">—</span> Liquidity</span>
  <span><span style="color:#3fb950;">—</span> Demand Zone</span>
  <span><span style="color:#f85149;">—</span> Supply Zone</span>
  <span><span style="color:#e8eaf6;">—</span> Entry</span>
  <span><span style="color:#f85149;">- -</span> SL</span>
  <span><span style="color:#3fb950;">- -</span> TP</span>
</div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════
    # TAB 4 — HISTORY
    # ════════════════════════════════════════════
    with tab4:
        if st.session_state.history:
            buys  = sum(1 for s in st.session_state.history if s.signal == SignalType.BUY)
            sells = sum(1 for s in st.session_state.history if s.signal == SignalType.SELL)
            avg_c = int(np.mean([s.confidence for s in st.session_state.history]))
            avg_r = round(np.mean([s.risk_reward for s in st.session_state.history]), 2)
            avg_smc = round(np.mean([s.smc_confluence_score for s in st.session_state.history]), 1)

            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            def stat_card(col, val, label, color="#e8eaf6"):
                col.markdown(f'<div class="stat-card"><div class="sv" style="color:{color};">{val}</div><div class="sl">{label}</div></div>', unsafe_allow_html=True)
            stat_card(sc1, len(st.session_state.history), "Total Signals")
            stat_card(sc2, buys,   "Buy Signals",   "#3fb950")
            stat_card(sc3, sells,  "Sell Signals",  "#f85149")
            stat_card(sc4, f"{avg_c}%", "Avg Conf")
            stat_card(sc5, f"{avg_smc}", "Avg SMC Score")

            st.markdown("")
            st.markdown('<div class="hist-header"><span>Time</span><span>Pair</span><span>Signal</span><span>Conf</span><span>Entry</span><span>TP</span><span>R/R</span><span>SMC Level</span></div>', unsafe_allow_html=True)
            rows_html = ""
            for s in st.session_state.history[:20]:
                is_b = s.signal == SignalType.BUY
                dec_ = INSTRUMENTS.get(s.symbol, {}).get("dec", 5)
                rows_html += f"""
<div class="hist-row {'hist-row-buy' if is_b else 'hist-row-sell'}">
  <span style="color:#8b949e;">{s.timestamp.strftime('%H:%M:%S')}</span>
  <span style="font-weight:600;">{pair_info['emoji']} {s.pair.split('·')[0].strip()}</span>
  <span>{badge('BUY','green') if is_b else badge('SELL','red')}</span>
  <span>{badge(f"{s.confidence}%", 'green' if s.confidence>=75 else 'yellow' if s.confidence>=65 else 'red')}</span>
  <span>{s.entry:.{dec_}f}</span>
  <span style="color:#3fb950;">{s.take_profit:.{dec_}f}</span>
  <span>1:{s.risk_reward}</span>
  <span style="font-size:11px;color:#d29922;">{s.key_level_type[:25] + '…' if len(s.key_level_type) > 25 else s.key_level_type}</span>
</div>"""
            st.markdown(rows_html, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#8b949e;font-size:.9rem;margin-top:1rem;">No signals generated yet this session.</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8b949e;font-size:11.5px;padding:.4rem 0 .8rem;">
  ⚠️ <b>For educational purposes only.</b> &nbsp; Not financial advice. &nbsp; Always use proper risk management.<br>
  ScalpBot Pro v3 · ICT/SMC: Order Blocks · FVG · BOS/CHOCH · Liquidity · Supply/Demand · Top-Down Bias
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTO-REFRESH SLEEP LOOP
# ─────────────────────────────────────────────
if st.session_state.auto_on and st.session_state.next_run:
    remaining = (st.session_state.next_run - datetime.now()).total_seconds()
    if remaining > 0:
        time.sleep(min(remaining, 8))
        st.rerun()

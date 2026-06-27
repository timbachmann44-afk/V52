import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="V45 PRO AI FINAL", layout="wide")

st.title("🤖 V45 PRO AI TRADER – FINAL LEVEL")

API_KEY = st.secrets.get("TWELVE_DATA_API_KEY", None)

# =========================
# REFRESH
# =========================
if st.button("🔄 Refresh AI Engine"):
    st.cache_data.clear()
    st.rerun()

# =========================
# DARK MODE
# =========================
st.markdown("""
<style>

.stApp {
    background:#05070D;
    color:#EAEAEA;
}

h1,h2,h3 {
    color:#00E5FF;
}

.card {
    background:#0B1220;
    padding:14px;
    border-radius:14px;
    margin-bottom:12px;
    border:1px solid #1f2937;
}

.buy { border-left:5px solid #00FF88; }
.sell { border-left:5px solid #FF3B3B; }

</style>
""", unsafe_allow_html=True)

# =========================
# COINS
# =========================
coins = ["BTC/USD","ETH/USD","XRP/USD","SOL/USD","ADA/USD","DOGE/USD","BNB/USD"]

selected = st.sidebar.multiselect("Coins", coins, default=coins)

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data(symbol):

    if not API_KEY:
        return None

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "15min",
        "outputsize": 200,
        "apikey": API_KEY
    }

    r = requests.get(url, params=params).json()

    if "values" not in r:
        return None

    df = pd.DataFrame(r["values"])
    df = df.iloc[::-1]

    for c in ["open","high","low","close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df

# =========================
# STRUCTURE
# =========================
def structure(df):

    price = df["close"].iloc[-1]

    support = df["low"].rolling(20).min().iloc[-1]
    resistance = df["high"].rolling(20).max().iloc[-1]

    atr = (df["high"] - df["low"]).rolling(20).mean().iloc[-1]

    return price, support, resistance, atr

# =========================
# 🕯️ CANDLE AI (NEW)
# =========================
def candle_ai(df):

    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    bullish = last["close"] > last["open"]
    bearish = last["close"] < last["open"]

    # Engulfing
    engulfing = (
        last["close"] > prev["open"] and
        last["open"] < prev["close"]
    )

    # Pinbar
    pinbar = (body / range_) < 0.3

    return bullish, bearish, engulfing, pinbar

# =========================
# V45 AI ENGINE
# =========================
def engine(price, support, resistance, atr, candle):

    bullish, bearish, engulfing, pinbar = candle

    rng = resistance - support

    score = 50
    reasons = []

    # =========================
    # CANDLE SIGNAL BOOST
    # =========================
    if engulfing:
        score += 20
        reasons.append("Engulfing candle detected")

    if pinbar:
        score += 15
        reasons.append("Pinbar rejection")

    if bullish:
        score += 10
        reasons.append("Bullish candle bias")
    else:
        score -= 10
        reasons.append("Bearish candle bias")

    # =========================
    # STRUCTURE
    # =========================
    breakout = price > resistance * 0.999
    breakdown = price < support * 1.001

    near_support = price <= support * 1.002
    near_resistance = price >= resistance * 0.998

    # =========================
    # SMART MONEY LOGIC
    # =========================
    liquidity_sweep = (price > resistance and bearish) or (price < support and bullish)

    if liquidity_sweep:
        score += 25
        reasons.append("Liquidity sweep detected")

    # =========================
    # SIGNALS
    # =========================
    if breakout:
        signal = "BREAKOUT BUY"
        direction = "BUY"
        entry = resistance
        sl = support
        tp = resistance + rng
        score += 25
        reasons.append("Breakout confirmed")

    elif breakdown:
        signal = "BREAKDOWN SELL"
        direction = "SELL"
        entry = support
        sl = resistance
        tp = support - rng
        score += 25
        reasons.append("Breakdown confirmed")

    elif near_support:
        signal = "SUPPORT BUY"
        direction = "BUY"
        entry = support
        sl = support - atr
        tp = resistance
        score += 15
        reasons.append("Support zone reaction")

    elif near_resistance:
        signal = "RESISTANCE SELL"
        direction = "SELL"
        entry = resistance
        sl = resistance + atr
        tp = support
        score += 15
        reasons.append("Resistance rejection")

    else:
        signal = "NO EDGE"
        direction = "WAIT"
        entry = price
        sl = price - atr
        tp = price + atr
        score -= 10
        reasons.append("Market neutral")

    # =========================
    # RR FILTER
    # =========================
    risk = abs(entry - sl)
    reward = abs(tp - entry)

    rr = round(reward / risk, 2) if risk != 0 else 0

    if rr > 2:
        score += 15
    elif rr < 1.2:
        score -= 10

    score = max(0, min(100, score))

    return signal, direction, entry, sl, tp, rr, score, reasons

# =========================
# RUN SCAN
# =========================
results = []

for coin in selected:

    df = load_data(coin)

    if df is None or df.empty:
        continue

    price, support, resistance, atr = structure(df)
    candle = candle_ai(df)

    signal, direction, entry, sl, tp, rr, score, reasons = engine(
        price, support, resistance, atr, candle
    )

    results.append({
        "Coin": coin,
        "Signal": signal,
        "Direction": direction,
        "Price": price,
        "Entry": entry,
        "SL": sl,
        "TP": tp,
        "RR": rr,
        "Score": score,
        "Reasons": reasons
    })

df = pd.DataFrame(results).sort_values("Score", ascending=False)

# =========================
# KPI
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("🟢 BUY", len(df[df["Direction"] == "BUY"]))
c2.metric("🔴 SELL", len(df[df["Direction"] == "SELL"]))
c3.metric("🔥 TOP SCORE", df["Score"].max())

# =========================
# BEST TRADE
# =========================
best = df.iloc[0]

st.success(f"""
🏆 BEST TRADE OF THE DAY

Coin: {best['Coin']}
Signal: {best['Signal']}
Score: {best['Score']}
RR: {best['RR']}
""")

# =========================
# FINAL RANKING
# =========================
st.subheader("🤖 V45 AI MARKET RANKING")

for i, r in df.iterrows():

    cls = "buy" if r["Direction"] == "BUY" else "sell"

    st.markdown(f"""
    <div class="card {cls}">

    <h3>{r['Coin']} – {r['Direction']}</h3>

    <p>{r['Signal']}</p>

    <hr>

    💰 Price: {r['Price']}<br>
    🎯 Entry: {r['Entry']}<br>
    🛑 SL: {r['SL']}<br>
    📈 TP: {r['TP']}<br>

    <hr>

    📊 RR: {r['RR']}<br>
    🧠 Score: {r['Score']}

    <hr>

    🧠 AI REASONS:<br>
    {"<br>".join(["- " + x for x in r["Reasons"]])}

    </div>
    """, unsafe_allow_html=True)

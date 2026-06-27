import streamlit as st
import requests
import pandas as pd
import numpy as np

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="V49 ULTIMATE AI TRADER", layout="wide")

st.title("🚀 V49 ULTIMATE AI TRADING SYSTEM")

API_KEY = st.secrets.get("TWELVE_DATA_API_KEY", None)

# =========================
# REFRESH
# =========================
if st.button("🔄 Refresh AI Engine"):
    st.cache_data.clear()
    st.rerun()

# =========================
# DARK UI
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

    momentum = df["close"].diff(5).mean()

    return price, support, resistance, atr, momentum

# =========================
# ENTRY TIMING ZONE (NEW CORE)
# =========================
def entry_zone(price, support, resistance, atr):

    zone_size = atr * 0.6

    buy_zone_low = support
    buy_zone_high = support + zone_size

    sell_zone_low = resistance - zone_size
    sell_zone_high = resistance

    if buy_zone_low <= price <= buy_zone_high:
        return "BUY_ZONE"
    elif sell_zone_low <= price <= sell_zone_high:
        return "SELL_ZONE"
    else:
        return "NO_ZONE"

# =========================
# MINI BACKTEST (NEW)
# =========================
def mini_backtest(df):

    returns = df["close"].pct_change().fillna(0)

    wins = (returns > 0).sum()
    losses = (returns < 0).sum()

    if wins + losses == 0:
        return 50

    return wins / (wins + losses)

# =========================
# V49 AI ENGINE
# =========================
def engine(price, support, resistance, atr, momentum, zone, winrate):

    rng = resistance - support

    score = 50
    reasons = []

    # =========================
    # BACKTEST EDGE
    # =========================
    score += (winrate - 0.5) * 40

    if winrate > 0.55:
        reasons.append("Historical edge positive")
    else:
        reasons.append("Weak historical edge")

    # =========================
    # MOMENTUM
    # =========================
    if momentum > 0:
        score += 10
        reasons.append("Bullish momentum")
        direction = "BUY"
    else:
        score -= 10
        reasons.append("Bearish momentum")
        direction = "SELL"

    # =========================
    # ENTRY ZONE LOGIC
    # =========================
    if zone == "BUY_ZONE":
        signal = "TIMED BUY"
        entry_low = support
        entry_high = support + atr
        sl = support - atr
        tp = resistance
        score += 20
        reasons.append("Inside BUY timing zone")

    elif zone == "SELL_ZONE":
        signal = "TIMED SELL"
        entry_low = resistance - atr
        entry_high = resistance
        sl = resistance + atr
        tp = support
        score += 20
        reasons.append("Inside SELL timing zone")

    else:
        signal = "WAIT"
        entry_low = price - atr
        entry_high = price + atr
        sl = price - atr
        tp = price + atr
        score -= 10
        reasons.append("No entry zone")

    # =========================
    # RISK / REWARD
    # =========================
    risk = abs((entry_low + entry_high)/2 - sl)
    reward = abs(tp - (entry_low + entry_high)/2)

    rr = round(reward / risk, 2) if risk != 0 else 0

    if rr > 2:
        score += 10
    elif rr < 1.2:
        score -= 10

    score = max(0, min(100, score))

    return signal, direction, entry_low, entry_high, sl, tp, rr, score, reasons

# =========================
# RUN SCAN
# =========================
results = []

for coin in selected:

    df = load_data(coin)

    if df is None or df.empty:
        continue

    price, support, resistance, atr, momentum = structure(df)

    zone = entry_zone(price, support, resistance, atr)
    winrate = mini_backtest(df)

    signal, direction, e_low, e_high, sl, tp, rr, score, reasons = engine(
        price, support, resistance, atr, momentum, zone, winrate
    )

    # =========================
    # CONFIDENCE LEVEL
    # =========================
    if score > 75:
        confidence = "HIGH"
    elif score > 55:
        confidence = "MED"
    else:
        confidence = "LOW"

    results.append({
        "Coin": coin,
        "Signal": signal,
        "Zone": zone,
        "Confidence": confidence,
        "Score": score,
        "RR": rr,
        "Entry Zone": f"{round(e_low,2)} - {round(e_high,2)}",
        "SL": round(sl,2),
        "TP": round(tp,2),
        "Winrate": round(winrate,2),
        "Reasons": reasons
    })

df = pd.DataFrame(results).sort_values("Score", ascending=False)

# =========================
# KPI
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("🟢 HIGH CONF", len(df[df["Confidence"] == "HIGH"]))
c2.metric("🎯 ACTIVE ZONES", len(df[df["Zone"] != "NO_ZONE"]))
c3.metric("🔥 TOP SCORE", df["Score"].max())

# =========================
# TOP TRADE
# =========================
best = df.iloc[0]

st.success(f"""
🏆 TOP TIMED TRADE

Coin: {best['Coin']}
Signal: {best['Signal']}
Zone: {best['Zone']}
Confidence: {best['Confidence']}
Score: {best['Score']}
RR: {best['RR']}
Winrate: {best['Winrate']}
""")

# =========================
# RANKING
# =========================
st.subheader("🚀 V49 TIMED AI RANKING")

for i, r in df.iterrows():

    st.markdown(f"""
    <div class="card">

    <h3>{r['Coin']} – {r['Signal']}</h3>

    📍 Zone: {r['Zone']}<br>
    🧠 Confidence: {r['Confidence']}<br>

    <hr>

    🎯 Entry Zone: {r['Entry Zone']}<br>
    🛑 SL: {r['SL']}<br>
    📈 TP: {r['TP']}<br>

    <hr>

    📊 RR: {r['RR']}<br>
    📊 Winrate: {r['Winrate']}<br>
    🧠 Score: {r['Score']}

    <hr>

    🧠 AI:
    {"<br>".join(["- " + x for x in r["Reasons"]])}

    </div>
    """, unsafe_allow_html=True)

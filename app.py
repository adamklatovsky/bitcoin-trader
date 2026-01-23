import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===============================
# KONFIGURACE STRÁNKY
# ===============================
st.set_page_config(
    page_title="BTC Regime Trader",
    page_icon="₿",
    layout="wide"
)

st.title("₿ Bitcoin Regime Trader")
st.markdown("""
**Smysl aplikace:**  
- BUY → režim nákupu (DCA + re-entry)  
- SELL → režim ochrany kapitálu  
- HOLD → nedělá nic  

Neřeší timing. Řeší **kdy smíš kupovat**.
""")

# ===============================
# SESSION STATE (PORTFOLIO)
# ===============================
if "cash" not in st.session_state:
    st.session_state.cash = 0.0

if "btc" not in st.session_state:
    st.session_state.btc = 0.0

if "position" not in st.session_state:
    st.session_state.position = "OUT"  # IN / OUT

if "log" not in st.session_state:
    st.session_state.log = []

# ===============================
# TECHNICKÉ INDIKÁTORY
# ===============================
def calculate_technicals(df):
    data = df.copy()

    data["SMA_50"] = data["Close"].rolling(50).mean()
    data["SMA_200"] = data["Close"].rolling(200).mean()

    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = ema12 - ema26
    data["MACD_SIGNAL"] = data["MACD"].ewm(span=9, adjust=False).mean()

    return data

# ===============================
# SKÓROVÁNÍ TRHU
# ===============================
def get_signal(row):
    score = 0
    reasons = []

    if row["SMA_50"] > row["SMA_200"]:
        score += 1
        reasons.append("Trend: býčí (SMA50 > SMA200)")
    else:
        score -= 1
        reasons.append("Trend: medvědí (SMA50 < SMA200)")

    if row["RSI"] < 30:
        score += 1
        reasons.append("RSI: přeprodaný")
    elif row["RSI"] > 70:
        score -= 1
        reasons.append("RSI: překoupený")

    if row["MACD"] > row["MACD_SIGNAL"]:
        score += 1
        reasons.append("MACD: pozitivní momentum")
    else:
        score -= 1
        reasons.append("MACD: negativní momentum")

    if score >= 2:
        verdict = "BUY"
        color = "green"
    elif score == 1:
        verdict = "WEAK BUY"
        color = "lightgreen"
    elif score == 0:
        verdict = "HOLD"
        color = "gray"
    elif score == -1:
        verdict = "SELL"
        color = "orange"
    else:
        verdict = "STRONG SELL"
        color = "red"

    return score, verdict, color, reasons

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.header("⚙️ Nastavení")
    ticker = st.text_input("Ticker", "BTC-USD")
    period = st.selectbox("Historie", ["1y", "2y", "5y"], index=1)
    daily_dca = st.number_input("Denní nákup (Kč)", value=100, step=50)

if st.button("🔁 Reset portfolia"):
    st.session_state.cash = 0
    st.session_state.btc = 0
    st.session_state.position = "OUT"
    st.session_state.log = []
    st.rerun()

# ===============================
# DATA
# ===============================
@st.cache_data
def load_data(symbol, period):
    df = yf.download(symbol, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = load_data(ticker, period)

if df.empty:
    st.error("Nepodařilo se stáhnout data.")
    st.stop()

df = calculate_technicals(df)
last = df.iloc[-1]
price = last["Close"]

score, verdict, color, reasons = get_signal(last)

# ===============================
# ROZHODOVACÍ LOGIKA (STAVOVÝ AUTOMAT)
# ===============================
action = "Žádná akce"

# BUY režim
if verdict in ["BUY", "WEAK BUY"]:
    if st.session_state.position == "OUT" and st.session_state.cash > 0:
        st.session_state.btc += st.session_state.cash / price
        st.session_state.log.append(f"RE-ENTRY za {st.session_state.cash:.0f} Kč")
        st.session_state.cash = 0
        st.session_state.position = "IN"
        action = "RE-ENTRY – nákup za celý cash"

    elif st.session_state.position == "IN":
        st.session_state.cash += daily_dca
        st.session_state.btc += daily_dca / price
        st.session_state.log.append(f"DCA +{daily_dca} Kč")
        action = f"DCA nákup +{daily_dca} Kč"

# SELL režim
elif verdict in ["SELL", "STRONG SELL"]:
    if st.session_state.position == "IN":
        st.session_state.cash += st.session_state.btc * price
        st.session_state.log.append("EXIT – prodej všeho")
        st.session_state.btc = 0
        st.session_state.position = "OUT"
        action = "EXIT – prodáno vše"

# ===============================
# DASHBOARD
# ===============================
st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cena BTC", f"${price:,.0f}")
col2.metric("Skóre", f"{score}/3")
col3.markdown(f"<h2 style='color:{color}'>{verdict}</h2>", unsafe_allow_html=True)
col4.metric("Režim", st.session_state.position)

st.info(action)

# ===============================
# PORTFOLIO
# ===============================
st.subheader("💼 Portfolio")
total_value = st.session_state.cash + st.session_state.btc * price

c1, c2, c3 = st.columns(3)
c1.metric("Cash (Kč)", f"{st.session_state.cash:,.0f}")
c2.metric("BTC", f"{st.session_state.btc:.6f}")
c3.metric("Celkem (Kč)", f"{total_value:,.0f}")

# ===============================
# GRAF
# ===============================
fig = make_subplots(rows=3, cols=1, shared_xaxes=True)

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], name="SMA50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["SMA_200"], name="SMA200"), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI"), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MACD_SIGNAL"], name="Signal"), row=3, col=1)

fig.update_layout(height=800, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ===============================
# LOG
# ===============================
with st.expander("📜 Log akcí"):
    for l in st.session_state.log[-20:]:
        st.write(l)

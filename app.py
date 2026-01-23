import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ===============================
# KONFIGURACE STRÁNKY
# ===============================
st.set_page_config(
    page_title="BTC Market Signal",
    page_icon="₿",
    layout="wide"
)

st.title("₿ Bitcoin Market Signal")
st.markdown("""
**Co to je:**  
Jednoduchý indikátor režimu trhu.

- **BUY** → trh je vhodný pro nákupy  
- **HOLD** → nejasná situace  
- **SELL** → trh není vhodný pro držení / nákup  

Neřeší peníze.  
Neřeší strategii.  
Říká jen **v jakém režimu se trh nachází**.
""")

# ===============================
# TECHNICKÉ INDIKÁTORY
# ===============================
def calculate_technicals(df):
    data = df.copy()

    # SMA
    data["SMA_50"] = data["Close"].rolling(50).mean()
    data["SMA_200"] = data["Close"].rolling(200).mean()

    # RSI
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = ema12 - ema26
    data["MACD_SIGNAL"] = data["MACD"].ewm(span=9, adjust=False).mean()

    return data

# ===============================
# SIGNÁL
# ===============================
def get_signal(row):
    score = 0
    reasons = []

    # Trend
    if row["SMA_50"] > row["SMA_200"]:
        score += 1
        reasons.append("📈 Trend: býčí (SMA 50 > SMA 200)")
    else:
        score -= 1
        reasons.append("📉 Trend: medvědí (SMA 50 < SMA 200)")

    # RSI
    if row["RSI"] < 30:
        score += 1
        reasons.append("💎 RSI: přeprodaný (<30)")
    elif row["RSI"] > 70:
        score -= 1
        reasons.append("🔥 RSI: překoupený (>70)")
    else:
        reasons.append("⚖️ RSI: neutrální (30–70)")

    # MACD
    if row["MACD"] > row["MACD_SIGNAL"]:
        score += 1
        reasons.append("🚀 MACD: pozitivní momentum")
    else:
        score -= 1
        reasons.append("🐌 MACD: negativní momentum")

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
    st.caption("Zdroj dat: Yahoo Finance")

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
# HLAVNÍ SEMAFOR
# ===============================
st.divider()

col1, col2, col3 = st.columns(3)

col1.metric("Cena BTC", f"${price:,.0f}")
col2.metric("Skóre", f"{score}/3")
col3.markdown(
    f"<h1 style='color:{color}; text-align:center'>{verdict}</h1>",
    unsafe_allow_html=True
)

with st.expander("🔍 Proč tento signál"):
    for r in reasons:
        st.write(r)

# ===============================
# GRAFY
# ===============================
st.subheader("📊 Technická analýza")

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.5, 0.25, 0.25],
    subplot_titles=("Cena + SMA", "RSI (14)", "MACD")
)

# Cena
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"]
), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["SMA_200"], name="SMA 200"), row=1, col=1)

# RSI
fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI"), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", row=2, col=1)

# MACD
fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["MACD_SIGNAL"], name="Signal"), row=3, col=1)

fig.update_layout(height=850, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

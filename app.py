import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# --------------------------------------------
# FUTURISTIC CLEAN VERSION — PURE STREAMLIT UI
# --------------------------------------------

st.set_page_config(
    page_title="BTC FUTURE Trader",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# THEME (Streamlit native)
st.write("""
<style>
:root {
    --primary-color: #6d5dfc;
    --text-color: #1d1f23;
}
</style>
""", unsafe_allow_html=True)

# --------- HERO ---------
st.markdown("## 🚀 BTC FUTURE Trader")
st.markdown(
    "Futuristický dashboard pro prezentaci vývoje ceny. "
    "Marketingový přehled nahoře. Technická analýza schovaná níže."
)
st.markdown("---")


# --------- SIDEBAR ---------
with st.sidebar:
    st.header("Nastavení")
    ticker = st.text_input("Ticker", value="BTC-USD")
    period = st.selectbox("Rozsah dat", ["1y", "2y", "5y"], index=1)
    if st.button("🔄 Obnovit cache"):
        st.cache_data.clear()
    st.caption("Zdroj dat: Yahoo Finance")


# --------- DATA LOADING ---------
@st.cache_data
def load(symbol, period):
    df = yf.download(symbol, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


df = load(ticker, period)

if df.empty:
    st.error("Nepodařilo se stáhnout data.")
    st.stop()

# --------- TECHNICALS ---------
def add_technicals(df):
    d = df.copy()

    d['SMA_50'] = d['Close'].rolling(50).mean()
    d['SMA_200'] = d['Close'].rolling(200).mean()

    delta = d['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    d['RSI'] = 100 - (100 / (1 + rs))

    exp1 = d['Close'].ewm(12, adjust=False).mean()
    exp2 = d['Close'].ewm(26, adjust=False).mean()
    d['MACD'] = exp1 - exp2
    d['Signal'] = d['MACD'].ewm(9, adjust=False).mean()
    return d


df = add_technicals(df)


def get_signal(row):
    score = 0
    if row["SMA_50"] > row["SMA_200"]: score += 1
    if row["RSI"] < 30: score += 1
    if row["MACD"] > row["Signal"]: score += 1

    if score == 3: return "STRONG BUY"
    if score == 2: return "BUY"
    if score == 1: return "HOLD"
    if score == 0: return "SELL"
    return "STRONG SELL"


# --------- TOP METRICS ---------
last = df.iloc[-1]
prev = df.iloc[-2]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Aktuální cena",
        f"${last['Close']:,.2f}",
        f"{(last['Close']-prev['Close'])/prev['Close']*100:.2f}%"
    )

with col2:
    st.metric("Signál", get_signal(last))

with col3:
    st.download_button(
        "📥 Stáhnout CSV",
        df.to_csv().encode(),
        file_name=f"{ticker}.csv"
    )


# --------- CHARTS ---------
st.markdown("### Vizualizace")
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    row_heights=[0.55, 0.25, 0.25]
)

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name="Cena"
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=df["SMA_50"], name="SMA 50"
), row=1, col=1)
fig.add_trace(go.Scatter(
    x=df.index, y=df["SMA_200"], name="SMA 200"
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=df["RSI"], name="RSI"
), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", row=2, col=1)

fig.add_trace(go.Scatter(
    x=df.index, y=df["MACD"], name="MACD"
), row=3, col=1)
fig.add_trace(go.Scatter(
    x=df.index, y=df["Signal"], name="Signal"
), row=3, col=1)

fig.update_layout(template="plotly_white", height=780)
st.plotly_chart(fig, use_container_width=True)


# --------- TECHNICAL SECTION ---------
with st.expander("Technická analýza — detailní tabulky"):
    st.dataframe(df.tail(20))


# --------- FOOTER ---------
st.markdown("---")
st.caption("Futuristický marketingový dashboard. Technika, když ji potřebuješ — jinak neruší.")

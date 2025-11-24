import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# -----------------------------
# BTC FUTURE Trader — FUTURISTIC MARKETING UI
# -----------------------------

st.set_page_config(page_title="BTC FUTURE Trader", page_icon="🚀", layout="wide")

# ---------- GLOBAL STYLES ----------
st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.bft-hero {
    background: linear-gradient(112deg,
        rgba(105,65,198,0.12),
        rgba(59,130,246,0.10)
    );
    padding: 38px 28px;
    border-radius: 18px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
    backdrop-filter: blur(14px);
}

.bft-h1 {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
}

.bft-sub {
    color: #6d7683;
    margin-top: 6px;
    font-size: 15px;
}

.bft-card {
    background: rgba(255,255,255,0.65);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.45);
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 18px rgba(0,0,0,0.04);
}

.bft-small {
    color: #7b8794;
    font-size: 13px;
}

.bft-badge {
    display: inline-block;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 13px;
}

.bft-legend {
    color: #445;
    font-size: 12px;
    opacity: 0.7;
}

.sidebar .sidebar-content {
    background: white !important;
}

.stDownloadButton button {
    border-radius: 12px !important;
}

</style>
""", unsafe_allow_html=True)


# ---------- HERO SECTION ----------
col1, col2 = st.columns([3,1])

with col1:
    st.markdown("<div class='bft-hero'>", unsafe_allow_html=True)
    st.markdown("<div class='bft-h1'>BTC FUTURE Trader</div>", unsafe_allow_html=True)
    st.markdown("<div class='bft-sub'>Budoucnost ceny. Přehledně. Marketingově. Bez hluku.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='bft-card' style='text-align:center'>", unsafe_allow_html=True)
    st.markdown("<div class='bft-small'>Aktualizace</div>")
    st.markdown(
        f"<div style='font-weight:700; font-size:22px; margin-top:4px'>{datetime.date.today().isoformat()}</div>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Nastavení")
    ticker = st.text_input("Ticker", value="BTC-USD")
    period = st.selectbox("Rozsah dat", ["1y", "2y", "5y"], index=1)
    st.write("<div class='bft-small'>Zdroj dat: Yahoo Finance</div>", unsafe_allow_html=True)
    if st.button("🔄 Obnovit cache"):
        st.cache_data.clear()


# ---------- DATA ----------
@st.cache_data
def load_data(symbol, period):
    try:
        df = yf.download(symbol, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()


def calculate_technicals(df):
    if df.empty: return df
    d = df.copy()

    d['SMA_50'] = d['Close'].rolling(50).mean()
    d['SMA_200'] = d['Close'].rolling(200).mean()

    delta = d['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    d['RSI'] = 100 - (100 / (1 + rs))

    exp1 = d['Close'].ewm(12, adjust=False).mean()
    exp2 = d['Close'].ewm(26, adjust=False).mean()
    d['MACD'] = exp1 - exp2
    d['Signal_Line'] = d['MACD'].ewm(9, adjust=False).mean()
    return d


def trading_signal(row):
    score = 0
    notes = []

    # Trend
    if row['SMA_50'] > row['SMA_200']:
        score += 1; notes.append("Trend: býčí (SMA 50 > SMA 200)")
    else:
        score -= 1; notes.append("Trend: medvědí (SMA 50 < SMA 200)")

    # RSI
    if row['RSI'] < 30:
        score += 1; notes.append("RSI: podhodnoceno")
    elif row['RSI'] > 70:
        score -= 1; notes.append("RSI: přehřáto")
    else:
        notes.append("RSI: neutrální")

    # MACD
    if row['MACD'] > row['Signal_Line']:
        score += 1; notes.append("MACD: rostoucí momentum")
    else:
        score -= 1; notes.append("MACD: klesající momentum")

    if score >= 2: return score, "STRONG BUY", "#00b36b", notes
    if score == 1: return score, "BUY", "#33cc88", notes
    if score == 0: return score, "HOLD", "#888", notes
    if score == -1: return score, "SELL", "#f5b400", notes
    return score, "STRONG SELL", "#e02424", notes


def fmt(v):
    try: return f"${v:,.2f}"
    except: return "-"


df = load_data(ticker, period)

if df.empty:
    st.error("Nepodařilo se stáhnout data – zkontroluj ticker.")
    st.stop()

df = calculate_technicals(df)

last = df.iloc[-1]
price = last["Close"]
prev = df.iloc[-2]["Close"]
pct = (price - prev) / prev * 100

score, verdict, color, notes = trading_signal(last)


# ---------- TOP CARDS ----------
st.divider()
c1, c2, c3 = st.columns([2,1,1])

with c1:
    st.markdown("<div class='bft-card'>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='display:flex; justify-content:space-between; align-items:center'>
            <div>
                <div style='font-size:24px; font-weight:800'>{fmt(price)}</div>
                <div class='bft-small'>Změna: {pct:.2f}%</div>
            </div>
            <div style='text-align:right'>
                <span class='bft-badge' style='background:{color}; color:white;'>{verdict}</span>
                <div class='bft-small' style='margin-top:6px'>Skóre: {score}/3</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='bft-card' style='text-align:center'>", unsafe_allow_html=True)
    st.markdown("<div class='bft-small'>Export</div>")
    st.download_button("📥 CSV", df.to_csv().encode(), f"{ticker}.csv")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='bft-card'>", unsafe_allow_html=True)
    st.markdown("<div class='bft-small'>Detaily signálu</div>")
    for n in notes:
        st.markdown(f"- {n}")
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- CHART ----------
st.subheader("Vizualizace")

fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.55,0.22,0.23]
)

fig.add_trace(go.Candlestick(x=df.index,
                             open=df['Open'], high=df['High'],
                             low=df['Low'], close=df['Close'],
                             name="Cena"), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50'), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200'), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI'), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", row=2, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal'), row=3, col=1)

fig.update_layout(height=760, template="plotly_white", xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)


# ---------- TECHNICKÉ (UPRAVENÉ, SCHOVANÉ) ----------
with st.expander("Technické indikátory (detailní analytika)"):
    st.markdown("<div class='bft-legend'>Pro zájemce o technickou hloubku</div>", unsafe_allow_html=True)
    st.dataframe(df.tail(10).style.format('{:.2f}'))


# ---------- FOOTER ----------
st.divider()
f1, f2 = st.columns(2)

with f1:
    st.markdown("<div class='bft-card'><strong>Pro reporty & týmy</strong><div class='bft-small'>Rychlé vizuály pro prezentace, CSV export, moderní UX.</div></div>", unsafe_allow_html=True)

with f2:
    st.markdown("<div class='bft-card'><strong>Chcete prezentaci?</strong><div class='bft-small'>Možné doplnit PPTX s vysvětlením metrik.</div></div>", unsafe_allow_html=True)

st.markdown("<div class='bft-small'>Futuristický, čistý, marketing-first design.</div>", unsafe_allow_html=True)

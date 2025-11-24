import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# -----------------------------
# BTC FUTURE Trader — CLEAN FUTURISTIC
# Marketing-forward but stable and readable. Opravené chyby CSS a layoutu.
# -----------------------------

st.set_page_config(page_title="BTC FUTURE Trader", page_icon="🚀", layout="wide")

# --- STYLING: minimal, safe CSS (nezasahuje do Streamlit internals) ---
st.markdown("""
<style>
/* safe scope: only classes we add */
.bft-hero{ background: linear-gradient(90deg, rgba(124,58,237,0.06), rgba(59,130,246,0.02)); padding:18px; border-radius:12px;}
.bft-card{ background:#fff; border-radius:12px; padding:14px; box-shadow:0 6px 18px rgba(15,23,42,0.04); border:1px solid rgba(11,22,35,0.04);}
.bft-h1{ font-size:22px; font-weight:800; margin:0 }
.bft-sub{ color:#586069; margin-top:6px; font-size:13px }
.bft-badge{ display:inline-block; padding:8px 12px; border-radius:999px; font-weight:700 }
.bft-small{ color:#7b8794; font-size:13px }
/* ensure charts and tables behave */
.streamlit-expanderHeader{ font-weight:600 }
</style>
""", unsafe_allow_html=True)

# --- HERO ---
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("<div class='bft-hero'>", unsafe_allow_html=True)
    st.markdown("<div class='bft-h1'>BTC FUTURE Trader — Predict. Prepare. Present.</div>", unsafe_allow_html=True)
    st.markdown("<div class='bft-sub'>Marketing-first prezentace dat, přitom plná techniky pro ty, kdo chtějí jít do hloubky.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='bft-card' style='text-align:center'>", unsafe_allow_html=True)
    st.markdown("<div class='bft-small'>Verze</div>")
    st.markdown(f"<div style='font-weight:700; font-size:18px'>{datetime.date.today().isoformat()}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Nastavení")
    ticker = st.text_input("Ticker", value="BTC-USD")
    period = st.selectbox("Rozsah dat", options=["1y","2y","5y"], index=1)
    st.write("<div class='bft-small'>Zdroj dat: Yahoo Finance — nástroj pro analytické a prezentacní účely.</div>", unsafe_allow_html=True)
    if st.button("🔄 Obnovit cache"):
        st.cache_data.clear()

# --- DATA LOADING & INDICATORS ---
@st.cache_data
def load_data(symbol, period):
    try:
        df = yf.download(symbol, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


def calculate_technicals(df):
    data = df.copy()
    if data.empty:
        return data
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    delta = data['Close'].diff()
    gain = (delta.where(delta>0,0)).rolling(window=14).mean()
    loss = (-delta.where(delta<0,0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data


def get_trading_signal(row):
    score = 0
    reasons = []
    if pd.notna(row.get('SMA_50')) and pd.notna(row.get('SMA_200')):
        if row['SMA_50'] > row['SMA_200']:
            score += 1; reasons.append('Trend: býčí (SMA 50 > SMA 200)')
        else:
            score -= 1; reasons.append('Trend: medvědí (SMA 50 < SMA 200)')
    else:
        reasons.append('Trend: nedostatek dat')
    if pd.notna(row.get('RSI')):
        if row['RSI'] < 30:
            score += 1; reasons.append('RSI: podhodnoceno (<30)')
        elif row['RSI'] > 70:
            score -= 1; reasons.append('RSI: přehřáto (>70)')
        else:
            reasons.append('RSI: neutrální (30-70)')
    else:
        reasons.append('RSI: nedostatek dat')
    if pd.notna(row.get('MACD')) and pd.notna(row.get('Signal_Line')):
        if row['MACD'] > row['Signal_Line']:
            score += 1; reasons.append('MACD: rostoucí momentum')
        else:
            score -= 1; reasons.append('MACD: klesající momentum')
    else:
        reasons.append('MACD: nedostatek dat')
    if score >= 2:
        return score, 'STRONG BUY', '#0f9d58', reasons
    elif score == 1:
        return score, 'BUY', '#7bd389', reasons
    elif score == 0:
        return score, 'HOLD', '#6b7280', reasons
    elif score == -1:
        return score, 'SELL', '#f59e0b', reasons
    else:
        return score, 'STRONG SELL', '#e02424', reasons


def format_currency(v):
    try: return f"${v:,.2f}"
    except: return '-'

# --- RENDER UI ---
raw = load_data(ticker, period)
if raw.empty:
    st.error('Nepodařilo se stáhnout data — zkontroluj ticker.')
else:
    df = calculate_technicals(raw)
    last = df.iloc[-1]
    price = last['Close']
    prev = df.iloc[-2]['Close'] if len(df) > 1 else price
    pct = (price - prev) / prev * 100 if prev != 0 else 0
    score, verdict, color, reasons = get_trading_signal(last)

    # TOP ROW — clean cards
    st.divider()
    c1,c2,c3 = st.columns([2,1,1])
    with c1:
        st.markdown("<div class='bft-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center'><div><div style='font-weight:800; font-size:20px'>{format_currency(price)}</div><div class='bft-small'>Změna: {pct:.2f}%</div></div><div style='text-align:right'><span class='bft-badge' style='background:{color}; color:white'>{verdict}</span><div class='bft-small' style='margin-top:6px'>Skóre: {score}/3</div></div></div>")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='bft-card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown("<div class='bft-small'>Export</div>")
        csv = df.to_csv(index=True)
        st.download_button('📥 Stáhnout CSV', data=csv, file_name=f'{ticker}_data.csv', mime='text/csv')
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='bft-card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown("<div class='bft-small'>Detaily</div>")
        for r in reasons:
            st.markdown(f"- {r}")
        st.markdown("</div>", unsafe_allow_html=True)

    # CHARTS
    st.subheader('Vizualizace')
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.55,0.22,0.23])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(width=1.4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(width=1.4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(width=1.4)), row=2, col=1)
    fig.add_hline(y=70, line_dash='dash', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(width=1.4)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal', line=dict(width=1.4)), row=3, col=1)
    fig.update_layout(height=760, xaxis_rangeslider_visible=False, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

    # TECHNICALS (deemphasized)
    with st.expander('Technické indikátory — podrobně'):
        st.markdown('- SMA 50 / SMA 200: určení trendu')
        st.markdown('- RSI (14): překoupenost / přeprodanost')
        st.markdown('- MACD (12,26,9): momentum')
        st.dataframe(df.tail(10).style.format('{:.2f}'))

    # FOOTER (marketing)
    st.divider()
    f1,f2 = st.columns(2)
    with f1:
        st.markdown("<div class='bft-card'><strong>Pro týmy</strong><div class='bft-small'>Rychlé vizuály pro reporty a prezentace. CSV export pro další zpracování.</div></div>", unsafe_allow_html=True)
    with f2:
        st.markdown("<div class='bft-card'><strong>Potřebujete prezentaci?</strong><div class='bft-small'>Můžu připravit PPTX s vysvětlením metrik a grafy.</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="bft-small">Stabilní futuristický UI — technika je dostupná, UX je prioritou.</div>', unsafe_allow_html=True)

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# -----------------------------
# BTC ALGO TRADER — FUTURISTIC UI
# Marketing-forward, technické části jsou dostupné, ale vizuálně upozaděné.
# -----------------------------

st.set_page_config(page_title="BTC FUTURE Trader", page_icon="🚀", layout="wide")

# --- STYLING: futuristický, světlý s neon akcenty ---
st.markdown("""
<style>
:root{ --bg:#0f1724; --card:#0b1220; --muted:#9aa6b2; --accent:#7c3aed; --glass: rgba(255,255,255,0.04);} 
/* overall */
body { background: linear-gradient(180deg, #f8fbff 0%, #eef6ff 100%); color: #061126; font-family: Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto;}
/* hero */
.hero { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(59,130,246,0.04)); padding:22px; border-radius:14px; box-shadow: 0 8px 30px rgba(99,102,241,0.08); }
.h1 { font-size:28px; font-weight:800; margin-bottom:6px }
.h2 { font-size:14px; color:var(--muted); margin-top:0 }
/* cards */
.card { background: white; border-radius:12px; padding:16px; box-shadow: 0 6px 18px rgba(15,23,42,0.04); border: 1px solid rgba(11,22,35,0.04); }
.metric { font-weight:700; font-size:18px }
.badge { display:inline-block; padding:8px 12px; border-radius:999px; font-weight:700 }
/* subtle neon accents */
.accent { color: var(--accent); }
.small { color: var(--muted); font-size:13px }
/* marketing box */
.pitch { border-radius:12px; padding:14px; background: linear-gradient(180deg, rgba(124,58,237,0.06), rgba(124,58,237,0.02)); }
</style>
""", unsafe_allow_html=True)

# --- HERO / MARKETING FIRST ---
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    st.markdown("<div class='h1'>BTC FUTURE Trader — Predict. Prepare. Profit.</div>", unsafe_allow_html=True)
    st.markdown("<div class='h2'>Interaktivní zážitek pro obchodníky i nadšence. Rychlé rozhodnutí, moderní vizualizace, jednoduché signály. Ne investiční rada — analytický nástroj.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>")
    st.markdown("<div class='pitch card'><strong>Pro koho je to nejlepší:</strong> pro vizuální analytiky, marketingové týmy a aktivní tradery, kteří chtějí rychlé rozhodnutí bez ztráty transparency.</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='card' style='text-align:center'>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Current tech</div>")
    st.markdown(f"<h3 class='metric accent'>Automatické skórování — SMA · RSI · MACD</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small' style='margin-top:6px'>Upozaděné odborné indikátory — klikněte na 'Technické' pro podrobnosti.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS (compact) ---
with st.sidebar:
    st.header("Start")
    ticker = st.text_input("Ticker", value="BTC-USD")
    period = st.selectbox("Rozsah dat", options=['1y','2y','5y'], index=1)
    st.markdown("<div class='small'>Data: Yahoo Finance · Analýza: SMA/RSI/MACD</div>", unsafe_allow_html=True)
    if st.button("🔄 Obnovit data"):
        st.cache_data.clear()

# --- DATA & INDICATORS (nedotčeno) ---
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

# --- RENDERING ---
raw = load_data(ticker, period)
if raw.empty:
    st.error('Nepodařilo se stáhnout data — zkontrolujte ticker.')
else:
    df = calculate_technicals(raw)
    last = df.iloc[-1]
    price = last['Close']
    prev = df.iloc[-2]['Close'] if len(df) > 1 else price
    pct = (price - prev) / prev * 100 if prev != 0 else 0
    score, verdict, color, reasons = get_trading_signal(last)

    # Top CTA row — marketing style
    st.divider()
    a,b = st.columns([3,1])
    with a:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center'><div><div style='font-weight:800; font-size:20px'>{format_currency(price)}</div><div class='small'>Změna: {pct:.2f}%</div></div><div style='text-align:right'><span class='badge' style='background:{color}; color:white'>{verdict}</span><div class='small' style='margin-top:6px'>Algoritmické skóre: {score}/3</div></div></div>")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>")
        st.markdown("<div class='card'><strong>Co dělá aplikace:</strong> agreguje trend, momentum a oscilátor do jednoduchého signálu. Marketingově: rychle ukazuje, zda trh dýchá nahoru nebo dolů.</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown("<div class='small'>Share / Export</div>")
        if st.button('📤 Exportovat CSV'):
            st.download_button('Stáhnout CSV', df.to_csv(index=True), file_name=f'{ticker}_data.csv')
        st.markdown("</div>", unsafe_allow_html=True)

    # Charts (prominent)
    st.subheader('Vizualizace — moderní')
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.55,0.22,0.23])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(width=1.4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(width=1.4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(width=1.4)), row=2, col=1)
    fig.add_hline(y=70, line_dash='dash', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(width=1.4)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal', line=dict(width=1.4)), row=3, col=1)
    fig.update_layout(height=780, xaxis_rangeslider_visible=False, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)

    # Technicals are present but de-emphasized
    with st.expander('Technické indikátory — podrobně (pro odborníky)', expanded=False):
        st.markdown('''
        - **SMA 50 / SMA 200** — klasik: dlouhodobý vs. krátkodobý trend.
        - **RSI (14)** — indikátor překoupenosti/přeprodanosti.
        - **MACD (12,26,9)** — měření momenta.
        ''')
        st.dataframe(df.tail(10).style.format("{:.2f}"))

    # Marketing footer
    st.divider()
    st.markdown("<div style='display:flex; gap:14px'>", unsafe_allow_html=True)
    st.markdown("<div class='card' style='flex:1'><strong>Proč to funguje pro týmy</strong><div class='small'>Jednoduché KPI, vizuály vhodné pro prezentace, export dat pro reporting.</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='card' style='flex:1'><strong>Chcete bílou knihu?</strong><div class='small'>Nabízíme připravený marketingový deck, který shrne metodu a přínosy pro management (kontaktujte nás).</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="small">Verze: Futuristic UI — marketing-first. Technika dostupná po rozkliknutí.</div>', unsafe_allow_html=True)

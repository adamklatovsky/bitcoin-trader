import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="BTC Algo Trader",
    page_icon="📈",
    layout="wide"
)

# --- LIGHT MODERN STYLING (simple, inline) ---
st.markdown(
    """
    <style>
    /* Page background and font */
    .reportview-container, .main {
        background: linear-gradient(180deg, #ffffff 0%, #f7f9fb 100%);
        color: #0f1724;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }
    /* Card like boxes */
    .card {
        background: #ffffff;
        padding: 14px;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(15, 23, 36, 0.06);
        border: 1px solid rgba(15,23,36,0.04);
    }
    /* Small muted text */
    .muted { color: #6b7280; font-size: 13px }
    /* Badge for verdict */
    .verdict { padding: 8px 14px; border-radius: 999px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- HEADER ---
colh1, colh2 = st.columns([3,1])
with colh1:
    st.title("₿ Bitcoin Algorithmic Trader & Analyzer")
    st.markdown("""
    **Abstrakt:** Interaktivní a přístupný nástroj pro analýzu BTC. Kombinuje klasické technické indikátory (SMA, RSI, MACD) do jednoho kompozitního skóre a jednoduchého verdiktu.
    """)
with colh2:
    st.markdown("<div style='text-align:right'><small class='muted'>Aktualizováno: {}</small></div>".format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')), unsafe_allow_html=True)

# --- HELP / VYSVĚTLIVKY (layman-friendly) ---
with st.expander("❓ Vysvětlivky (rychle, pro laiky)", expanded=False):
    st.markdown("""
    - **SMA (Simple Moving Average)** — průměrná cena za posledních N dní. Pomáhá určit, zda je trh v dlouhodobějším vzestupu nebo poklesu.
    - **RSI (Relative Strength Index)** — ukazatel „přehřátí“ trhu. Hodnoty nad 70 mohou znamenat přehřátí (může následovat korekce), pod 30 znamená možnou „sleva" (přeprodané).
    - **MACD** — měří tempo změn cen (momentum). Křížení MACD nad signální linkou je býčí signál, pod ní medvědí.
    - **Kompozitní skóre & verdikt** — jednoduché sčítání signálů: trend (SMA), moment (MACD) a oscilátor (RSI). Výsledek je orientační – není to investiční rada.
    """)

# --- FUNCTIONS ---
@st.cache_data
def load_data(symbol, period):
    try:
        df = yf.download(symbol, period=period, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return pd.DataFrame()


def calculate_technicals(df):
    """Vypočítá technické indikátory: SMA_50, SMA_200, RSI(14), MACD(12,26,9)"""
    data = df.copy()
    if data.empty:
        return data

    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()

    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

    return data


def get_trading_signal(row):
    """Jednoduchý rozhodovací strom: vrací skóre, verdikt, barvu a důvody (pro zobrazení uživateli)."""
    score = 0
    reasons = []

    # Trend (SMA)
    if pd.notna(row.get('SMA_50')) and pd.notna(row.get('SMA_200')):
        if row['SMA_50'] > row['SMA_200']:
            score += 1
            reasons.append("Trend: býčí (SMA 50 > SMA 200)")
        else:
            score -= 1
            reasons.append("Trend: medvědí (SMA 50 < SMA 200)")
    else:
        reasons.append("Trend: nedostatek dat pro SMA")

    # RSI
    if pd.notna(row.get('RSI')):
        if row['RSI'] < 30:
            score += 1
            reasons.append("RSI: podhodnoceno (<30)")
        elif row['RSI'] > 70:
            score -= 1
            reasons.append("RSI: přehřáto (>70)")
        else:
            reasons.append("RSI: neutrální (30-70)")
    else:
        reasons.append("RSI: nedostatek dat")

    # MACD
    if pd.notna(row.get('MACD')) and pd.notna(row.get('Signal_Line')):
        if row['MACD'] > row['Signal_Line']:
            score += 1
            reasons.append("MACD: rostoucí momentum (MACD > Signal)")
        else:
            score -= 1
            reasons.append("MACD: klesající momentum (MACD < Signal)")
    else:
        reasons.append("MACD: nedostatek dat")

    if score >= 2:
        verdict = "STRONG BUY"
        color = "#0f9d58"
    elif score == 1:
        verdict = "BUY"
        color = "#7bd389"
    elif score == 0:
        verdict = "HOLD"
        color = "#6b7280"
    elif score == -1:
        verdict = "SELL"
        color = "#f59e0b"
    else:
        verdict = "STRONG SELL"
        color = "#e02424"

    return score, verdict, color, reasons


def format_currency(v):
    try:
        return f"${v:,.2f}"
    except:
        return "-"

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Nastavení")
    ticker = st.text_input("Ticker Symbol", value="BTC-USD")
    period = st.selectbox("Rozsah dat", options=["1y", "2y", "5y"], index=1)
    st.markdown("<div class='muted'>Data jsou stahována živě z Yahoo Finance. Aplikace slouží pouze pro vzdělávací a analytické účely.</div>", unsafe_allow_html=True)
    if st.button("🔄 Obnovit data"):
        st.cache_data.clear()

# --- LOAD + CALC ---
raw_df = load_data(ticker, period)
if raw_df.empty:
    st.error("Nepodařilo se stáhnout data. Zkontrolujte ticker nebo zvolte jiný rozsah.")
else:
    df = calculate_technicals(raw_df)
    last_row = df.iloc[-1]
    current_price = last_row['Close']
    prev_price = df.iloc[-2]['Close'] if len(df) > 1 else current_price
    price_change = current_price - prev_price
    pct_change = (price_change / prev_price) * 100 if prev_price != 0 else 0

    score, verdict, color, reasons = get_trading_signal(last_row)

    # --- TOP DASHBOARD ---
    st.divider()
    c1, c2, c3, c4 = st.columns([2,1,1,2])

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Aktuální cena**")
        st.markdown(f"<h2>{format_currency(current_price)} <small style='color:#6b7280'>({pct_change:.2f}%)</small></h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown("**Algoritmické skóre**")
        st.markdown(f"<h3>{score}/3</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown("**Verdikt**")
        st.markdown(f"<div class='verdict' style='background:{color}; color:white; display:inline-block'>{verdict}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Detaily rozhodnutí**")
        for r in reasons:
            st.markdown(f"- {r}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- PLOTLY CHARTS ---
    st.subheader("📊 Technická analýza v čase")

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.05,
                        row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=(f"Cena {ticker} + SMA", "RSI (14)", "MACD (12,26,9)"))

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Cena'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(width=1.6)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(width=1.6)), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(width=1.6)), row=2, col=1)
    fig.add_hline(y=70, line_width=1, line_dash='dash', line_color='red', row=2, col=1)
    fig.add_hline(y=30, line_width=1, line_dash='dash', line_color='green', row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(width=1.6)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal', line=dict(width=1.6)), row=3, col=1)

    fig.update_layout(height=800, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- RAW DATA ---
    st.divider()
    with st.expander("📋 Zobrazit surová data (posledních 10 řádků)"):
        st.dataframe(df.tail(10).style.format("{:.2f}"))

    # --- SHORT NOTES FOR LAYMAN (visible) ---
    with st.expander("📝 Rychlé shrnutí (co to znamená)", expanded=False):
        st.markdown("""
        - <b>BUY / SELL</b> jsou pouze orientační signály. Neberte je jako investiční radu.
        - Pokud chcete konzervativnější pohled, zvyšte váhu SMA a vyčkejte na potvrzení (více než 1 den).
        - Na historická data se dá nahlédnout v sekci surových dat.
        """, unsafe_allow_html=True)

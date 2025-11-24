import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. KONFIGURACE STRÁNKY A MODERNÍ DESIGN ---
st.set_page_config(
    page_title="BTC Algo Trader Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Vlastní CSS pro "Financial Dashboard" vzhled
st.markdown("""
<style>
    /* Hlavní pozadí a barvy textu */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Stylování metrik (karty) */
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        border: 1px solid #374151;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #9ca3af;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 700;
        color: white;
    }
    
    /* Nadpisy */
    h1, h2, h3 {
        color: white !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
    
    /* Alert boxy */
    div.stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNKCE (LOGIKA ZŮSTÁVÁ STEJNÁ) ---
def calculate_technicals(df):
    data = df.copy()
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
    score = 0
    reasons = []
    
    # SMA
    if row['SMA_50'] > row['SMA_200']:
        score += 1
        reasons.append("✅ TREND: Býčí (Golden Cross)")
    else:
        score -= 1
        reasons.append("⛔ TREND: Medvědí (Death Cross)")
        
    # RSI
    if row['RSI'] < 30:
        score += 1
        reasons.append("✅ RSI: Podhodnoceno (Oversold)")
    elif row['RSI'] > 70:
        score -= 1
        reasons.append("⛔ RSI: Přehřáto (Overbought)")
    else:
        reasons.append("⚖️ RSI: Neutrální zóna")
        
    # MACD
    if row['MACD'] > row['Signal_Line']:
        score += 1
        reasons.append("✅ MACD: Rostoucí momentum")
    else:
        score -= 1
        reasons.append("⛔ MACD: Klesající momentum")
        
    # Verdikt s barvami pro UI
    if score >= 2:
        verdict = "STRONG BUY"
        bg_color = "#10B981" # Green
    elif score == 1:
        verdict = "BUY"
        bg_color = "#34D399" # Light Green
    elif score == 0:
        verdict = "HOLD"
        bg_color = "#6B7280" # Grey
    elif score == -1:
        verdict = "SELL"
        bg_color = "#F59E0B" # Orange
    else:
        verdict = "STRONG SELL"
        bg_color = "#EF4444" # Red
        
    return score, verdict, bg_color, reasons

@st.cache_data
def load_data(symbol, period):
    df = yf.download(symbol, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# --- 3. UI ROZLOŽENÍ ---

# Sidebar
with st.sidebar:
    st.title("⚡ AlgoTrader")
    st.markdown("---")
    ticker = st.text_input("Symbol", value="BTC-USD").upper()
    period = st.selectbox("Historie", options=["6mo", "1y", "2y", "5y"], index=1)
    
    st.markdown("### 📊 Indikátory")
    st.caption("• SMA (50/200)\n• RSI (14)\n• MACD (12,26,9)")
    
    if st.button("🔄 Aktualizovat trh", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #6b7280; font-size: 12px;'>Powered by Python & Plotly</div>", unsafe_allow_html=True)

# Main Content
st.markdown(f"# ₿ {ticker} Algorithmic Analysis")
st.markdown("Automatizovaná analýza technických indikátorů v reálném čase.")

try:
    raw_df = load_data(ticker, period)
    
    if raw_df.empty:
        st.error(f"❌ Nelze načíst data pro {ticker}. Zkontrolujte symbol.")
    else:
        df = calculate_technicals(raw_df)
        last_row = df.iloc[-1]
        
        # Výpočty pro metriky
        curr_price = last_row['Close']
        prev_price = df.iloc[-2]['Close']
        change = curr_price - prev_price
        pct_change = (change / prev_price) * 100
        score, verdict, bg_color, reasons = get_trading_signal(last_row)

        st.markdown("---")

        # --- SEKCE METRIK A VERDIKTU ---
        col_main1, col_main2, col_main3 = st.columns([1, 1, 1.5])

        with col_main1:
            st.metric("Aktuální Cena", f"${curr_price:,.2f}", f"{pct_change:+.2f}%")
        
        with col_main2:
            st.metric("Algo Skóre (-3 až +3)", f"{score}")

        with col_main3:
            # Custom HTML karta pro Verdikt
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            ">
                <h4 style="margin:0; color:white; opacity: 0.9;">ALGORITMICKÝ SIGNÁL</h4>
                <h1 style="margin:0; color:white; font-size: 36px; letter-spacing: 2px;">{verdict}</h1>
            </div>
            """, unsafe_allow_html=True)

        # --- DŮVODY ROZHODNUTÍ ---
        with st.expander("🔍 Zobrazit detailní analýzu rozhodnutí", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.info(reasons[0]) # Trend
            c2.info(reasons[1]) # RSI
            c3.info(reasons[2]) # MACD

        # --- GRAFY (DARK MODE PLOTLY) ---
        st.markdown("### 📈 Technický Přehled")
        
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(f"Price Action & SMA", "RSI Momentum", "MACD Oscillator")
        )

        # 1. Candlestick
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], 
                        name="Cena"), row=1, col=1)
        
        # SMA Lines
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#F59E0B', width=1), name="SMA 50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='#3B82F6', width=1), name="SMA 200"), row=1, col=1)

        # 2. RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#A78BFA', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#EF4444", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#10B981", row=2, col=1)
        # Výplň pro RSI neutrální zónu
        fig.add_hrect(y0=30, y1=70, fillcolor="#374151", opacity=0.1, line_width=0, row=2, col=1)

        # 3. MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#FFFFFF', width=1), name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], line=dict(color='#EF4444', width=1), name="Signal"), row=3, col=1)
        
        # Histogram pro MACD (volitelné vylepšení)
        colors = ['#10B981' if v >= 0 else '#EF4444' for v in (df['MACD'] - df['Signal_Line'])]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD'] - df['Signal_Line'], marker_color=colors, name="Hist"), row=3, col=1)

        # Globální styling grafu (Dark Mode)
        fig.update_layout(
            template="plotly_dark",
            height=900, 
            xaxis_rangeslider_visible=False, 
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', # Průhledné pozadí
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Segoe UI", color="#9ca3af")
        )
        
        # Odstranění mřížek pro čistší vzhled
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor='#374151', zeroline=False)

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Kritická chyba: {e}")

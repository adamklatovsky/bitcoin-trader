import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(
    page_title="BTC Algo Trader",
    page_icon="📈",
    layout="wide"
)

# --- HLAVIČKA ---
st.title("₿ Bitcoin Algorithmic Trader & Analyzer")
st.markdown("""
**Abstrakt:** Interaktivní nástroj pro analýzu trhu v reálném čase. 
Kombinuje **Trend (SMA)**, **Momentum (MACD)** a **Oscilátor (RSI)** pro výpočet kompozitního skóre a obchodního signálu.
""")

# --- FUNKCE PRO VÝPOČET INDIKÁTORŮ ---
def calculate_technicals(df):
    """Vypočítá SMA, RSI a MACD."""
    data = df.copy()
    
    # 1. SMA (Simple Moving Average)
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    
    # 2. RSI (Relative Strength Index) - 14 period
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # 3. MACD (12, 26, 9)
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    return data

# --- FUNKCE PRO SKÓROVÁNÍ ---
def get_trading_signal(row):
    """Aplikuje rozhodovací strom a vrací skóre + verdikt."""
    score = 0
    reasons = []
    
    # 1. Trend (SMA)
    if row['SMA_50'] > row['SMA_200']:
        score += 1
        reasons.append("📈 Trend: Býčí (SMA 50 > SMA 200)")
    else:
        score -= 1
        reasons.append("📉 Trend: Medvědí (SMA 50 < SMA 200)")
        
    # 2. Oscilátor (RSI)
    if row['RSI'] < 30:
        score += 1
        reasons.append("💎 RSI: Podhodnoceno (<30)")
    elif row['RSI'] > 70:
        score -= 1
        reasons.append("🔥 RSI: Přehřáto (>70)")
    else:
        reasons.append("⚖️ RSI: Neutrální (30-70)")
        
    # 3. Momentum (MACD)
    if row['MACD'] > row['Signal_Line']:
        score += 1
        reasons.append("🚀 MACD: Rostoucí momentum")
    else:
        score -= 1
        reasons.append("🐌 MACD: Klesající momentum")
        
    # Vyhodnocení
    if score >= 2:
        verdict = "STRONG BUY"
        color = "green"
    elif score == 1:
        verdict = "BUY"
        color = "lightgreen"
    elif score == 0:
        verdict = "HOLD"
        color = "gray"
    elif score == -1:
        verdict = "SELL"
        color = "orange"
    else: # <= -2
        verdict = "STRONG SELL"
        color = "red"
        
    return score, verdict, color, reasons

# --- NAČTENÍ DAT ---
with st.sidebar:
    st.header("⚙️ Nastavení")
    ticker = st.text_input("Ticker Symbol", value="BTC-USD")
    period = st.selectbox("Rozsah dat", options=["1y", "2y", "5y"], index=1)
    st.info("Data jsou stahována živě z Yahoo Finance.")
    if st.button("🔄 Obnovit data"):
        st.cache_data.clear()

@st.cache_data
def load_data(symbol, period):
    df = yf.download(symbol, period=period, progress=False)
    return df

try:
    # Načtení a výpočet
    raw_df = load_data(ticker, period)
    
    if raw_df.empty:
        st.error("Nepodařilo se stáhnout data. Zkontrolujte ticker.")
    else:
        df_processed = calculate_technicals(raw_df)
        
        # Získání posledního řádku pro aktuální analýzu
        last_row = df_processed.iloc[-1]
        current_price = last_row['Close']
        prev_price = df_processed.iloc[-2]['Close']
        price_change = current_price - prev_price
        pct_change = (price_change / prev_price) * 100
        
        score, verdict, color, reasons = get_trading_signal(last_row)

        # --- DASHBOARD TOP SECTION ---
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Aktuální Cena", f"${current_price:,.2f}", f"{pct_change:.2f}%")
        
        with col2:
            st.metric("Algoritmické Skóre", f"{score}/3")
            
        with col3:
            st.markdown(f"### Verdikt:")
            st.markdown(f"<h2 style='color: {color}; margin-top: -20px'>{verdict}</h2>", unsafe_allow_html=True)

        with col4:
            with st.expander("🔍 Detaily rozhodnutí"):
                for reason in reasons:
                    st.write(reason)

        # --- VIZUALIZACE (PLOTLY) ---
        st.subheader("📊 Technická Analýza v čase")
        
        # Vytvoření subplotů (Cena, RSI, MACD)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            row_heights=[0.5, 0.25, 0.25],
                            subplot_titles=(f"Cena {ticker} + SMA", "RSI (14)", "MACD (12,26,9)"))

        # 1. Graf Ceny + SMA
        fig.add_trace(go.Candlestick(x=df_processed.index,
                        open=df_processed['Open'], high=df_processed['High'],
                        low=df_processed['Low'], close=df_processed['Close'], 
                        name="Cena"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df_processed.index, y=df_processed['SMA_50'], 
                                 line=dict(color='orange', width=1.5), name="SMA 50"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df_processed.index, y=df_processed['SMA_200'], 
                                 line=dict(color='blue', width=1.5), name="SMA 200"), row=1, col=1)

        # 2. Graf RSI
        fig.add_trace(go.Scatter(x=df_processed.index, y=df_processed['RSI'], 
                                 line=dict(color='purple', width=1.5), name="RSI"), row=2, col=1)
        # Linky překoupenosti/přeprodanosti
        fig.add_hline(y=70, line_width=1, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_width=1, line_dash="dash", line_color="green", row=2, col=1)

        # 3. Graf MACD
        fig.add_trace(go.Scatter(x=df_processed.index, y=df_processed['MACD'], 
                                 line=dict(color='black', width=1.5), name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df_processed.index, y=df_processed['Signal_Line'], 
                                 line=dict(color='red', width=1.5), name="Signal"), row=3, col=1)

        # Úprava vzhledu
        fig.update_layout(height=800, xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- DATA TABLE ---
        st.divider()
        with st.expander("📋 Zobrazit surová data (posledních 10 dní)"):
            st.dataframe(df_processed.tail(10).style.format("{:.2f}"))

except Exception as e:
    st.error(f"Nastala chyba při zpracování aplikace: {e}")

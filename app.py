import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import os

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ACDP Market Leaders", 
    layout="wide", 
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. MASTER UNIVERSE CONFIGURATION (50 ASSETS)
# -----------------------------------------------------------------------------
MASTER_UNIVERSE = {
    # Global Indices
    "🇺🇸 S&P 500": "^GSPC",
    "🇺🇸 Nasdaq 100": "^NDX",
    "🇺🇸 Dow Jones": "^DJI",
    "🇺🇸 Russell 2000": "^RUT",
    "🇮🇳 Nifty 50": "^NSEI",
    "🇮🇳 Nifty Bank": "^NSEBANK",
    "🇨🇳 Shanghai Comp": "000001.SS",
    "🇭🇰 Hang Seng": "^HSI",
    "🇯🇵 Nikkei 225": "^N225",
    "🇬🇧 FTSE 100": "^FTSE",
    "🇩🇪 DAX": "^GDAXI",
    "🇫🇷 CAC 40": "^FCHI",
    "🇪🇺 STOXX 50": "^STOXX50E",
    "🇧🇷 Bovespa": "^BVSP",
    "🇦🇺 ASX 200": "^AXJO",
    "🇰🇷 KOSPI": "^KS11",
    "🇹🇼 Taiwan Wght": "^TWII",
    "🇿🇦 JSE Top 40": "^J203.JO",
    "🇨🇦 TSX Comp": "^GSPTSE",
    
    # Commodities & Crypto
    "🥇 Gold": "GC=F",
    "🥈 Silver": "SI=F",
    "🛢️ Crude Oil (WTI)": "CL=F",
    "🛢️ Brent Crude": "BZ=F",
    "🔥 Natural Gas": "NG=F",
    "🥉 Copper": "HG=F",
    "₿ Bitcoin": "BTC-USD",
    "⟠ Ethereum": "ETH-USD",
    "🚀 Solana": "SOL-USD",
    
    # US Sector ETFs (To catch sector rotation)
    "💻 Tech (XLK)": "XLK",
    "🏦 Financials (XLF)": "XLF",
    "🏥 Health Care (XLV)": "XLV",
    "⚡ Energy (XLE)": "XLE",
    "🏭 Industrials (XLI)": "XLI",
    "🛒 Consumer Disc (XLY)": "XLY",
    "🍞 Consumer Staples (XLP)": "XLP",
    "💡 Utilities (XLU)": "XLU",
    "🧱 Materials (XLB)": "XLB",
    "🏢 Real Estate (XLRE)": "XLRE",
    "🔬 Biotech (XBI)": "XBI",
    "💾 Semiconductors (SMH)": "SMH",
    
    # Bonds & Fixed Income ETFs (Absolute regime filters)
    "💵 20Y+ Treasury (TLT)": "TLT",
    "💵 7-10Y Treasury (IEF)": "IEF",
    "💵 1-3Y Treasury (SHY)": "SHY",
    "🏢 Corp Bonds (LQD)": "LQD",
    "⚠️ High Yield Bonds (HYG)": "HYG",
    
    # Broad International ETFs
    "🌍 Emerging Mkts (EEM)": "EEM",
    "🌍 Developed Mkts (VEA)": "VEA",
    "🇲🇽 Mexico (EWW)": "EWW",
    "🇮🇳 India ETF (INDA)": "INDA"
}

# -----------------------------------------------------------------------------
# 3. CSS & STYLING (English Lavender Theme)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #fbfaff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9d5ff; box-shadow: 4px 0 15px rgba(139, 92, 246, 0.03); }
    [data-testid="stSidebar"] h1 { color: #4B365F; font-weight: 700; letter-spacing: -1px; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #6b5b95; }
    .canvas-container { background: linear-gradient(135deg, #ffffff 0%, #f3e8ff 100%); padding: 30px; border-radius: 20px; border: 1px solid #d8b4fe; box-shadow: 0 10px 30px rgba(124, 58, 237, 0.08); margin-bottom: 25px; }
    .big-title { font-family: 'Arial Black', sans-serif; font-size: 3em; text-transform: uppercase; background: -webkit-linear-gradient(top, #4B365F, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 5px; }
    .subtitle { color: #8b5cf6; font-family: 'Courier New', monospace; text-align: center; font-size: 1em; font-weight: 600; }
    [data-testid="stDataFrame"] { border: 1px solid #e9d5ff; border-radius: 12px; overflow: hidden; background-color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 4px; color: #4B365F; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #f3e8ff; color: #7c3aed; border: 1px solid #d8b4fe; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. QUANT ENGINE & DYNAMIC FILTER
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_and_analyze_data():
    stats_data = []
    history_dict = {}
    
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    total = len(MASTER_UNIVERSE)
    
    for i, (name, ticker) in enumerate(MASTER_UNIVERSE.items()):
        try:
            progress_bar.progress((i + 1) / total)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")
            
            if hist.empty or len(hist) < 260:
                continue
                
            hist.index = hist.index.tz_localize(None)
            current_price = hist['Close'].iloc[-1]
            
            def get_price_lag(days):
                target_date = datetime.now() - timedelta(days=days)
                idx = hist.index.get_indexer([target_date], method='nearest')[0]
                return hist['Close'].iloc[idx]

            p12m = get_price_lag(365)
            p6m  = get_price_lag(180)
            p3m  = get_price_lag(90)
            p1m  = get_price_lag(30)
            
            r12 = (current_price - p12m) / p12m
            r6  = (current_price - p6m)  / p6m
            r3  = (current_price - p3m)  / p3m
            r1  = (current_price - p1m)  / p1m
            
            avg_score = (r12 + r6 + r3 + r1) / 4
            
            daily_returns = hist['Close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252)
            
            stats_data.append({
                "Asset": name,
                "Price": current_price,
                "Score": avg_score,
                "Vol": volatility
            })
            
            history_dict[name] = hist['Close']
            
        except Exception:
            continue
            
    progress_placeholder.empty()
    
    df_stats = pd.DataFrame(stats_data)
    
    if not df_stats.empty:
        # 1. Sort ALL 50 assets and assign their TRUE Global Rank first
        df_stats = df_stats.sort_values("Score", ascending=False).reset_index(drop=True)
        df_stats['Rank'] = df_stats.index + 1
        
        # 2. Slice the Top 20 Leaders
        display_df = df_stats.head(20).copy()
        
        # 3. Pin India (Nifty 50) to the bottom if it falls out of the Top 20
        india_row = df_stats[df_stats['Asset'] == "🇮🇳 Nifty 50"]
        if not india_row.empty and "🇮🇳 Nifty 50" not in display_df['Asset'].values:
            display_df = pd.concat([display_df, india_row])
        
        # 4. Filter history dictionary to only include the displayed assets
        display_assets = display_df['Asset'].tolist()
        history_dict = {k: v for k, v in history_dict.items() if k in display_assets}
        
        return display_df, history_dict

@st.cache_data(ttl=3600)
def calculate_correlation(history_dict):
    if not history_dict:
        return pd.DataFrame()
    df_prices = pd.DataFrame(history_dict)
    df_returns = df_prices.pct_change().dropna()
    return df_returns.corr()

# -----------------------------------------------------------------------------
# 5. SIDEBAR & HEADER
# -----------------------------------------------------------------------------
header_col1, header_col2 = st.columns([1, 8])
with header_col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=60)

with st.sidebar:
    st.title("ACDP")
    st.caption("Automated Concentrated\nDiversified Portfolio")
    st.write("---")
    st.info("Dynamic Quant Engine actively scanning 50 global assets. Displaying Top 20.")
    st.write("---")
    st.caption(f"Last Update:\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# -----------------------------------------------------------------------------
# 6. MAIN APP
# -----------------------------------------------------------------------------
st.markdown('<div class="canvas-container">', unsafe_allow_html=True)
st.markdown('<div class="big-title">GLOBAL MARKET LEADER</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">RANKING SYSTEM BY ADVANCED QUANT ANALYTICS</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.spinner("Scanning Master Universe and routing capital..."):
    df_stats, history_dict = fetch_and_analyze_data()
    df_corr = calculate_correlation(history_dict)

if not df_stats.empty:
    tab1, tab2 = st.tabs(["🏆 Global Performance Heatmap", "🧩 Risk Architecture"])
    
    # --- TAB 1: RANKING SYSTEM (HEATMAP) ---
    with tab1:
        st.caption("Derived from ACDP Quant Algorithm | Relative Strength using quant analytics")
        
        heatmap_df = df_stats[['Rank', 'Asset', 'Price', 'Vol']].copy()
        heatmap_df = heatmap_df.set_index('Rank')

        st.dataframe(
            heatmap_df.style
            .format({
                'Price': '{:,.2f}',
                'Vol': '{:.2%}'
            })
            # Heatmap Gradient strictly on Price column, driven by Rank (Green=Top, Red=Bottom)
            .background_gradient(
                cmap='RdYlGn_r', 
                subset=['Price'], 
                gmap=heatmap_df.index
            )
            .set_properties(**{'text-align': 'center', 'font-weight': '600', 'color': '#2e2e2e'})
            .set_table_styles([{
                'selector': 'th',
                'props': [
                    ('text-align', 'center'), 
                    ('background-color', '#f3e8ff'), 
                    ('color', '#4B365F'),
                    ('font-size', '1.1em')
                ]
            }]),
            use_container_width=True,
            height=800
        )

    # --- TAB 2: RISK ANALYSIS ---
    with tab2:
        st.subheader("Active Portfolio Correlation & Volatility")
        st.caption("Risk parameters dynamically updated for the current Top 20 inclusions.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Correlation Matrix (Current Leaders)**")
            if not df_corr.empty:
                fig_corr = px.imshow(
                    df_corr, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r", zmin=-1, zmax=1
                )
                fig_corr.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#4B365F"), height=650
                )
                st.plotly_chart(fig_corr, use_container_width=True)
                
        with col2:
            st.markdown("**Annualized Volatility Matrix**")
            fig_vol = px.scatter(
                df_stats, x="Vol", y="Score", text="Asset",
                size=[15]*len(df_stats), color="Score",
                color_continuous_scale="Viridis",
                labels={"Vol": "Volatility (Risk)", "Score": "Momentum (Reward)"}
            )
            fig_vol.update_traces(textposition='top center')
            fig_vol.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,240,255,0.5)",
                font=dict(color="#4B365F"), height=650, showlegend=False
            )
            st.plotly_chart(fig_vol, use_container_width=True)

else:
    st.error("Unable to scan market. Please check internet connection.")

# Footer
st.write("---")
st.markdown(
    """
    <div style='text-align: center; color: #887bb0; font-size: 0.8em; font-family: sans-serif;'>
        © ACDP Framework • Built for Rajan Yadav • Powered by Investopedia Analytics Logic
    </div>
    """, 
    unsafe_allow_html=True
)

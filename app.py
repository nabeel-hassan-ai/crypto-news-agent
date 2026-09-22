import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import time
from datetime import datetime
from config import SOURCES_CONFIG
from collectors import collect_all_data, fetch_live_market_context, fetch_technical_indicators
from analyzer import CryptoNewsAnalyzer
from news_advisor import NewsSentimentRiskAdvisor

st.set_page_config(
    page_title="Crypto & Gold News Risk AI Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling - Modern Dark Trading Terminal Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0d1117 0%, #06090e 90%);
        color: #e6edf3;
    }
    
    /* Top Ticker Ribbon */
    .ticker-bar {
        display: flex;
        gap: 15px;
        overflow-x: auto;
        padding: 10px 18px;
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 12px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    
    .ticker-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.92rem;
        font-weight: 600;
        white-space: nowrap;
    }
    
    .ticker-up {
        color: #3fb950;
        background: rgba(63, 185, 80, 0.15);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    
    .ticker-down {
        color: #f85149;
        background: rgba(248, 81, 73, 0.15);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }

    /* Cards */
    .metric-card {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    .card-title {
        color: #8b949e;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        font-weight: 600;
    }

    .param-box {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    .param-label {
        font-size: 0.76rem;
        color: #94a3b8;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .param-val {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Bottom Refresh Bar */
    .bottom-refresh-card {
        background: linear-gradient(90deg, #161b22 0%, #1c2128 100%);
        border: 2px solid #388bfd;
        border-radius: 14px;
        padding: 20px;
        margin-top: 35px;
        margin-bottom: 25px;
        box-shadow: 0 6px 24px rgba(56, 139, 253, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.svg", width=44)
    st.title("Settings & Sources")
    st.caption("Crypto & Gold News Risk Gatekeeper")
    st.divider()

    st.subheader("⚡ Refresh Interval")
    auto_refresh = st.selectbox(
        "Auto-Refresh Schedule",
        ["Off (Manual Only)", "Every 1 Minute", "Every 2 Minutes", "Every 5 Minutes"],
        index=0
    )
    if auto_refresh != "Off (Manual Only)":
        seconds_map = {"Every 1 Minute": 60, "Every 2 Minutes": 120, "Every 5 Minutes": 300}
        interval = seconds_map[auto_refresh]
        st.info(f"⏱️ Auto-refresh active ({auto_refresh}).")
        time_elapsed = time.time() - st.session_state.get("last_refresh_time", time.time())
        if time_elapsed > interval:
            st.session_state["last_refresh_time"] = time.time()
            st.rerun()

    st.divider()
    st.subheader("🤖 AI Model")
    gemini_key = st.text_input("Gemini API Key (Optional)", type="password", placeholder="Paste Google Gemini Key")
    model_choice = st.selectbox(
        "Reasoning Engine",
        ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro", "Heuristic + TA Rule Engine (Offline)"],
        index=0
    )
    if not gemini_key:
        st.caption("💡 Running via High-Performance Heuristic & Binance TA Engine.")

    st.divider()
    st.subheader("🌐 Monitored Feeds (12 Sources)")
    active_sources = []
    for key, conf in SOURCES_CONFIG.items():
        if st.checkbox(conf["name"], value=True, key=f"src_{key}"):
            active_sources.append(key)

    st.caption(f"Active Monitoring: {len(active_sources)} sources")

# ----------------- SESSION STATE -----------------
if "analysis_data" not in st.session_state:
    st.session_state["analysis_data"] = None
if "collected_raw" not in st.session_state:
    st.session_state["collected_raw"] = None
if "last_refresh_time" not in st.session_state:
    st.session_state["last_refresh_time"] = time.time()

# ----------------- TOP TICKER RIBBON -----------------
if "market_context" not in st.session_state:
    st.session_state["market_context"] = fetch_live_market_context()

m_ctx = st.session_state.get("market_context", {})
prices = m_ctx.get("prices", {})

ticker_html = '<div class="ticker-bar">'
if prices:
    for coin, data in prices.items():
        p = data.get("usd", 0)
        c = data.get("usd_24h_change", 0)
        change_class = "ticker-up" if c >= 0 else "ticker-down"
        arrow = "▲" if c >= 0 else "▼"
        ticker_html += f'<div class="ticker-item"><span style="color:#8b949e">{coin.upper()}:</span> <span>${p:,.2f}</span> <span class="{change_class}">{arrow} {c:+.2f}%</span></div>'
else:
    ticker_html += '<div class="ticker-item"><span style="color:#8b949e">BTC:</span> <span>$85,745.00</span></div><div class="ticker-item"><span style="color:#8b949e">GOLD (XAU):</span> <span>$2,654.50</span></div>'
ticker_html += '</div>'
st.markdown(ticker_html, unsafe_allow_html=True)

# ----------------- EXECUTE RESEARCH FUNCTION -----------------
def execute_research():
    with st.spinner("🔍 Scanning ForexFactory, CryptoCraft, 10 news wires & Binance Technicals..."):
        raw_data = collect_all_data(active_sources=active_sources)
        st.session_state["collected_raw"] = raw_data
        st.session_state["market_context"] = raw_data.get("market_context", {})
        st.session_state["last_refresh_time"] = time.time()

    with st.spinner("🧠 Synthesizing trade playbook & technical parameters..."):
        use_model = model_choice if "Heuristic" not in model_choice else None
        analyzer = CryptoNewsAnalyzer(api_key=gemini_key, model_name=use_model or "gemini-2.5-flash")
        analysis_result = analyzer.analyze(raw_data)
        st.session_state["analysis_data"] = analysis_result

# Run initial analysis if not yet run
if st.session_state.get("analysis_data") is None:
    execute_research()

analysis = st.session_state.get("analysis_data", {})
raw_data = st.session_state.get("collected_raw", {})

# ----------------- TOP BAR -----------------
col_hdr, col_top_refresh = st.columns([3, 1.2])
with col_hdr:
    st.title("⚡ Crypto & Gold News Sentiment & TA Safety Agent")
    st.caption("Answers: (1) Is news pointing Bullish or Bearish? (2) Will news spoil your Technical Analysis or is it safe to trade?")
with col_top_refresh:
    st.write("")
    if st.button("🔄 Refresh Live Research", key="top_refresh", type="primary", use_container_width=True):
        execute_research()
        st.rerun()

# ----------------- ASSET SELECTOR: BITCOIN vs GOLD vs OVERALL -----------------
st.markdown("### 🎯 Select Target Asset for Questions 1 & 2:")
asset_choice = st.radio(
    "Target Market Selection:",
    ["₿ Bitcoin (BTC)", "🥇 Gold (XAU/USD)", "🌐 Overall Market"],
    horizontal=True,
    label_visibility="collapsed"
)

if "Bitcoin" in asset_choice:
    chosen_asset_key = "BTC"
    asset_display_name = "Bitcoin (BTC)"
    tech_symbol = "BTCUSDT"
    tv_default_symbol = "BINANCE:BTCUSDT"
elif "Gold" in asset_choice:
    chosen_asset_key = "GOLD"
    asset_display_name = "Gold (XAU/USD)"
    tech_symbol = "PAXGUSDT"
    tv_default_symbol = "OANDA:XAUUSD"
else:
    chosen_asset_key = "OVERALL"
    asset_display_name = "Overall Market"
    tech_symbol = "BTCUSDT"
    tv_default_symbol = "BINANCE:BTCUSDT"

# Evaluate dedicated advisor for chosen asset
advisor = NewsSentimentRiskAdvisor()
advisor_data = advisor.evaluate_news_and_risk(
    raw_data.get("news_articles", []),
    raw_data.get("macro_events", []),
    raw_data.get("crypto_calendar_events", []),
    asset=chosen_asset_key
)

# ----------------- THE TWO CORE QUESTIONS DISPLAY -----------------
col_q1, col_q2 = st.columns(2)

# REQUIREMENT 1: IS THE NEWS POINTING BULLISH OR BEARISH?
with col_q1:
    news_lean = advisor_data.get("news_leaning", "NEUTRAL")
    bull_pct = advisor_data.get("bull_percentage", 50)
    bear_pct = advisor_data.get("bear_percentage", 50)
    
    if news_lean == "BULLISH":
        border_color = "#238636"
        lean_color = "#3fb950"
        lean_icon = "📈"
    elif news_lean == "BEARISH":
        border_color = "#da3633"
        lean_color = "#f85149"
        lean_icon = "📉"
    else:
        border_color = "#d29922"
        lean_color = "#d29922"
        lean_icon = "⚖️"

    box_html_q1 = (
        f'<div style="border:2px solid {border_color}; background:rgba(13, 17, 23, 0.95); border-radius:16px; padding:22px; height:100%; box-shadow:0 8px 30px rgba(0,0,0,0.4);">'
        f'<div style="font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; color:#8b949e; font-weight:700; margin-bottom:6px;">QUESTION 1: {asset_display_name.upper()} NEWS DIRECTION (بلش بمقابلہ بیئرش)</div>'
        f'<div style="font-size:1.8rem; font-weight:800; color:{lean_color}; font-family:\'JetBrains Mono\', monospace; margin-bottom:8px;">{lean_icon} LEANING {news_lean}</div>'
        f'<div style="font-size:0.92rem; color:#c9d1d9; margin-bottom:14px; line-height:1.4;">{advisor_data.get("bias_summary", "")}</div>'
        f'<div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:700; margin-bottom:6px;">'
        f'<span style="color:#3fb950;">🟢 Bullish: {bull_pct}%</span>'
        f'<span style="color:#f85149;">🔴 Bearish: {bear_pct}%</span>'
        f'</div>'
        f'<div style="width:100%; height:14px; background:#f85149; border-radius:7px; overflow:hidden; display:flex;">'
        f'<div style="width:{bull_pct}%; height:100%; background:#238636;"></div>'
        f'</div>'
        f'<div style="font-size:0.75rem; color:#8b949e; margin-top:10px;">Tailored analysis based on 12 sources, ForexFactory USD macro calendar & {asset_display_name} news.</div>'
        f'</div>'
    )
    st.markdown(box_html_q1, unsafe_allow_html=True)

# REQUIREMENT 2: WILL NEWS SPOIL YOUR TECHNICAL ANALYSIS? (TA VOLATILITY & SAFETY GATE)
with col_q2:
    is_danger = advisor_data.get("is_dangerous", False)
    verdict_badge = advisor_data.get("verdict_badge", "SAFE FOR TA")
    verdict_color = advisor_data.get("verdict_color", "#3fb950")
    trade_verdict = advisor_data.get("trade_verdict", "SAFE")
    advice = advisor_data.get("advice", "")
    risk_reasons = advisor_data.get("risk_reasons", [])

    border_q2 = "#da3633" if is_danger else "#238636"
    bg_q2 = "rgba(218, 54, 51, 0.12)" if is_danger else "rgba(35, 134, 54, 0.12)"
    risk_items_html = "".join([f"<div style='margin-bottom:4px;'>• {r}</div>" for r in risk_reasons]) if risk_reasons else f"<div>• No volatile shock catalysts detected for {asset_display_name}. Safe trading conditions.</div>"

    box_html_q2 = (
        f'<div style="border:2px solid {border_q2}; background:rgba(13, 17, 23, 0.95); border-radius:16px; padding:22px; height:100%; box-shadow:0 8px 30px rgba(0,0,0,0.4);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">'
        f'<span style="font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; color:#8b949e; font-weight:700;">QUESTION 2: NEWS THREAT TO {asset_display_name.upper()} TA (کیا نیوز TA خراب کرے گی؟)</span>'
        f'<span style="background:{verdict_color}; color:#ffffff; padding:3px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">{verdict_badge}</span>'
        f'</div>'
        f'<div style="font-size:1.4rem; font-weight:800; color:{verdict_color}; font-family:\'JetBrains Mono\', monospace; margin-bottom:10px; line-height:1.2;">'
        f'{"⚠️ " if is_danger else "✅ "}{trade_verdict}'
        f'</div>'
        f'<div style="font-size:0.92rem; color:#e6edf3; margin-bottom:12px; line-height:1.4;">'
        f'<b>Verdict:</b> {advice}'
        f'</div>'
        f'<div style="font-size:0.84rem; color:{"#ff7b72" if is_danger else "#7ee787"}; background:{bg_q2}; padding:10px 14px; border-radius:8px; border-left:4px solid {verdict_color};">'
        f'<b>{asset_display_name} Risk Status:</b><br/>{risk_items_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(box_html_q2, unsafe_allow_html=True)

# ----------------- SECTION 2: TECHNICAL TRADE PARAMETERS -----------------
st.markdown("<br/>", unsafe_allow_html=True)
st.markdown(f"### 🎯 {asset_display_name} Trade Parameters (Use if Question 2 confirms SAFE)")

# Get technical price for selected asset
asset_tech = raw_data.get("technicals", {}).get(tech_symbol, {})
if not asset_tech:
    asset_tech = fetch_technical_indicators(tech_symbol)
cur_p = asset_tech.get("price", 85000.0 if "BTC" in tech_symbol else 2650.0)
sup_p = asset_tech.get("support", cur_p * 0.97)
res_p = asset_tech.get("resistance", cur_p * 1.03)

if chosen_asset_key == "GOLD":
    entry_z = f"${cur_p * 0.995:,.2f} - ${cur_p:,.2f}"
    tp1_val = f"${cur_p * 1.015:,.2f}"
    tp2_val = f"${cur_p * 1.03:,.2f}"
    sl_val = f"${cur_p * 0.985:,.2f}"
elif chosen_asset_key == "BTC":
    entry_z = f"${cur_p * 0.995:,.0f} - ${cur_p:,.0f}"
    tp1_val = f"${res_p:,.0f}"
    tp2_val = f"${res_p * 1.03:,.0f}"
    sl_val = f"${sup_p:,.0f}"
else:
    params = analysis.get("trade_parameters", {})
    entry_z = params.get("entry_zone", f"${cur_p * 0.995:,.0f} - ${cur_p:,.0f}")
    tp1_val = params.get("take_profit_1", f"${res_p:,.0f}")
    tp2_val = params.get("take_profit_2", f"${res_p * 1.03:,.0f}")
    sl_val = params.get("stop_loss", f"${sup_p:,.0f}")

st.markdown(f"""
<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin-bottom:20px;">
    <div class="param-box">
        <div class="param-label">{asset_display_name} Target Entry</div>
        <div class="param-val" style="color:#58a6ff;">{entry_z}</div>
    </div>
    <div class="param-box">
        <div class="param-label">Take Profit 1</div>
        <div class="param-val" style="color:#3fb950;">{tp1_val}</div>
    </div>
    <div class="param-box">
        <div class="param-label">Take Profit 2</div>
        <div class="param-val" style="color:#2ea043;">{tp2_val}</div>
    </div>
    <div class="param-box">
        <div class="param-label">Stop-Loss (Invalidation)</div>
        <div class="param-val" style="color:#f85149;">{sl_val}</div>
    </div>
    <div class="param-box">
        <div class="param-label">Risk / Reward</div>
        <div class="param-val" style="color:#bc8cff;">1 : 2.5</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- SECTION 3: DEEP-DIVE TABS (NEWS, MACRO & CATALYSTS) -----------------
st.markdown("### 📰 News Catalysts Breakdown & Macro Calendar")

tab_catalysts, tab_calendar, tab_news_feed, tab_export = st.tabs([
    f"⚡ High-Weight {asset_display_name} Headlines",
    "📅 ForexFactory (USD Macro) & CryptoCraft Calendar",
    "📰 Live 12-Source News Wire",
    "💾 Export Full Report"
])

with tab_catalysts:
    col_bull_hl, col_bear_hl = st.columns(2)
    with col_bull_hl:
        st.subheader(f"🟢 Top Bullish Headlines ({asset_display_name})")
        bull_items = advisor_data.get("top_bullish_headlines", [])
        if bull_items:
            for item in bull_items:
                st.markdown(f"""
                <div style="background:rgba(35, 134, 54, 0.1); border:1px solid #238636; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#3fb950;">
                        <b>{item.get('source')}</b> <span>Weight: {item.get('strength')}</span>
                    </div>
                    <div style="font-size:0.95rem; font-weight:600; margin-top:4px;">
                        <a href="{item.get('link')}" target="_blank" style="color:#e6edf3; text-decoration:none;">{item.get('title')} ↗</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No strong bullish news headlines detected for {asset_display_name}.")

    with col_bear_hl:
        st.subheader(f"🔴 Top Bearish Headlines ({asset_display_name})")
        bear_items = advisor_data.get("top_bearish_headlines", [])
        if bear_items:
            for item in bear_items:
                st.markdown(f"""
                <div style="background:rgba(218, 54, 51, 0.1); border:1px solid #da3633; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#f85149;">
                        <b>{item.get('source')}</b> <span>Weight: {item.get('strength')}</span>
                    </div>
                    <div style="font-size:0.95rem; font-weight:600; margin-top:4px;">
                        <a href="{item.get('link')}" target="_blank" style="color:#e6edf3; text-decoration:none;">{item.get('title')} ↗</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No strong bearish news headlines detected for {asset_display_name}.")

with tab_calendar:
    st.subheader("ForexFactory (USD Macro) & CryptoCraft Calendar")
    st.write("Track scheduled releases (CPI, Interest Rate Decisions, FOMC, NFP) that create 3%–8% volatility spikes in Bitcoin and Gold.")
    
    macro_events = raw_data.get("macro_events", [])
    crypto_events = raw_data.get("crypto_calendar_events", [])

    c_filter = st.radio("Calendar Filter:", ["All High/Medium Impact Events", "USD Macro Events (ForexFactory - Gold/BTC Impact)", "Crypto Protocol Events (CryptoCraft)"], horizontal=True)

    combined_events = []
    if "USD Macro" in c_filter or "All" in c_filter:
        combined_events.extend(macro_events)
    if "Crypto Protocol" in c_filter or "All" in c_filter:
        combined_events.extend(crypto_events)

    if combined_events:
        df_events = pd.DataFrame(combined_events)[["date", "time", "country", "impact", "title", "forecast", "previous", "source"]]
        st.dataframe(df_events, use_container_width=True, hide_index=True)
    else:
        st.info("No matching calendar events found.")

with tab_news_feed:
    st.subheader("Breaking News Stream (CoinDesk, Cointelegraph, WatcherGuru, etc.)")
    articles = raw_data.get("news_articles", [])
    search_query = st.text_input("🔍 Search headlines...", "")
    if search_query:
        articles = [a for a in articles if search_query.lower() in a.get("title", "").lower() or search_query.lower() in a.get("summary", "").lower()]

    st.caption(f"Showing {len(articles)} articles")
    for art in articles[:20]:
        st.markdown(f"""
        <div style="background:rgba(22, 27, 34, 0.7); border:1px solid #30363d; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color:#58a6ff; font-weight:600; font-size:0.85rem;">{art.get('source')}</span>
                <span style="color:#8b949e; font-size:0.8rem;">{art.get('pub_date', '')}</span>
            </div>
            <div style="font-size:1.02rem; font-weight:600; margin-bottom:4px;">
                <a href="{art.get('link')}" target="_blank" style="color:#e6edf3; text-decoration:none;">{art.get('title')} ↗</a>
            </div>
            <div style="color:#8b949e; font-size:0.88rem;">{art.get('summary')}</div>
        </div>
        """, unsafe_allow_html=True)

with tab_export:
    st.subheader("💾 Export Full Intelligence Report")
    export_payload = {
        "asset_evaluated": chosen_asset_key,
        "news_advisor": advisor_data,
        "trading_analysis": analysis
    }
    json_str = json.dumps(export_payload, indent=2)
    st.download_button("📥 Download JSON Report", data=json_str, file_name=f"{chosen_asset_key}_news_advisor_report.json", mime="application/json")
    st.code(json_str, language="json")

# ----------------- SECTION 4: END TIME / COMPLETE TECHNICAL ANALYSIS -----------------
st.markdown("---")
st.markdown("### 📈 3. End-Time Technical Analysis (TA Verification & Live Charts)")
st.write("Verify your technical indicators (RSI, EMAs, Support/Resistance) and chart patterns.")

col_c_sel, col_c_info = st.columns([1.5, 3])
with col_c_sel:
    available_symbols = ["BTCUSDT", "PAXGUSDT", "ETHUSDT", "SOLUSDT"]
    default_idx = 1 if chosen_asset_key == "GOLD" else 0
    selected_coin = st.selectbox("Select Asset for Live Technical Verification:", available_symbols, index=default_idx)

tech_data = raw_data.get("technicals", {}).get(selected_coin, {})
if not tech_data:
    tech_data = fetch_technical_indicators(selected_coin)

# Metrics Grid
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">Live Price</div>
        <div style="font-size:1.4rem; font-weight:700; color:#f0f6fc;">${tech_data.get('price', 0):,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    rsi_val = tech_data.get('rsi', 50)
    rsi_color = "#f85149" if rsi_val >= 75 else ("#3fb950" if rsi_val <= 30 else "#58a6ff")
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">1h RSI (14)</div>
        <div style="font-size:1.4rem; font-weight:700; color:{rsi_color};">{rsi_val}</div>
        <div style="font-size:0.75rem; color:#8b949e;">{tech_data.get('rsi_status', 'Neutral')}</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    trend_val = tech_data.get('trend', 'Neutral')
    trend_color = "#3fb950" if "BULLISH" in trend_val else ("#f85149" if "BEARISH" in trend_val else "#d29922")
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">EMA Trend (9/21)</div>
        <div style="font-size:1.15rem; font-weight:700; color:{trend_color};">{trend_val.split(' ')[0]}</div>
        <div style="font-size:0.75rem; color:#8b949e;">EMA9: ${tech_data.get('ema9', 0):,.1f}</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">24h Key Support</div>
        <div style="font-size:1.4rem; font-weight:700; color:#3fb950;">${tech_data.get('support', 0):,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with m5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">24h Key Resistance</div>
        <div style="font-size:1.4rem; font-weight:700; color:#f85149;">${tech_data.get('resistance', 0):,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"**Technical Confluence:** {analysis.get('technical_confluence', '')}")

# Interactive TradingView Chart
tv_symbol = "OANDA:XAUUSD" if selected_coin == "PAXGUSDT" else f"BINANCE:{selected_coin}"
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:520px; width:100%;">
  <div id="tradingview_widget" style="height:520px; width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "60",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#0d1117",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "studies": [
      "RSI@tv-basicstudies",
      "MASimple@tv-basicstudies"
    ],
    "container_id": "tradingview_widget"
  }}
  );
  </script>
</div>
"""
components.html(tradingview_html, height=530)

# ----------------- SECTION 5: UNMISSABLE BOTTOM REFRESH OPTION -----------------
st.markdown("""
<div class="bottom-refresh-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h3 style="margin:0; color:#58a6ff;">🔄 Refresh Live Market & News Research</h3>
            <p style="margin:4px 0 0 0; color:#8b949e; font-size:0.92rem;">
                Click this button at any time to re-scan all 12 websites (ForexFactory, CryptoCraft, CoinDesk, etc.) and re-verify News vs TA safety.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

c_b1, c_b2 = st.columns([1, 3])
with c_b1:
    if st.button("🔄 Click to Refresh Research Now", key="bottom_main_refresh", type="primary", use_container_width=True):
        execute_research()
        st.success("✅ Research refreshed successfully!")
        st.rerun()
with c_b2:
    st.markdown(f"""
    <div style="padding-top:10px; color:#8b949e; font-size:0.9rem;">
        🕒 <b>Last Research Update:</b> {raw_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
    </div>
    """, unsafe_allow_html=True)

st.caption(f"⚠️ Financial Risk Disclaimer: {analysis.get('disclaimer', '')}")

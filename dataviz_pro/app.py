import streamlit as st
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="APEX Analytics",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --red: #E8002D;
    --red-dark: #B8001F;
    --red-light: #FF1A45;
    --red-ultra: #FF0038;
    --white: #FFFFFF;
    --off-white: #F7F7F7;
    --cream: #FFF5F5;
    --gray-100: #F2F2F2;
    --gray-200: #E5E5E5;
    --gray-300: #D4D4D4;
    --gray-500: #737373;
    --gray-700: #404040;
    --gray-900: #171717;
    --black: #0A0A0A;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.10);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.12);
    --shadow-red: 0 4px 24px rgba(232,0,45,0.18);
}

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--white) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: var(--black) !important;
    border-right: none !important;
}

[data-testid="stSidebar"] > div {
    background: var(--black) !important;
}

[data-testid="stSidebarContent"] {
    background: var(--black) !important;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: var(--white) !important;
}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stRadio label span {
    color: rgba(255,255,255,0.75) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.02em;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px dashed rgba(232,0,45,0.5) !important;
    border-radius: 10px !important;
}

/* Radio buttons in sidebar */
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* Active radio */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) span {
    color: var(--red-light) !important;
    font-weight: 600 !important;
}

/* Main content area */
.main .block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1600px !important;
}

/* Headers */
h1, h2, h3 { font-family: 'DM Sans', sans-serif !important; }

.apex-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem;
    letter-spacing: 0.1em;
    color: var(--white);
    line-height: 1;
}

.apex-logo span {
    color: var(--red);
}

.apex-tagline {
    font-size: 0.65rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
    margin-top: 2px;
    font-family: 'DM Sans', sans-serif;
}

.page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 2px solid var(--gray-100);
}

.page-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    letter-spacing: 0.06em;
    color: var(--gray-900);
    line-height: 1;
    margin: 0;
}

.page-title span {
    color: var(--red);
}

.page-subtitle {
    font-size: 0.82rem;
    color: var(--gray-500);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Metric cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    margin: 1.5rem 0;
}

.metric-card {
    background: var(--white);
    border: 1.5px solid var(--gray-200);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: var(--red);
    box-shadow: var(--shadow-red);
    transform: translateY(-2px);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--red);
}

.metric-card .label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--gray-500);
    font-weight: 600;
    margin-bottom: 6px;
}

.metric-card .value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 0.04em;
    color: var(--gray-900);
    line-height: 1;
}

.metric-card .sub {
    font-size: 0.7rem;
    color: var(--gray-500);
    margin-top: 4px;
}

/* Section titles */
.section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem;
    letter-spacing: 0.08em;
    color: var(--gray-900);
    margin: 2rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

.section-title::after {
    content: '';
    flex: 1;
    height: 1.5px;
    background: linear-gradient(90deg, var(--red) 0%, var(--gray-200) 100%);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--gray-100) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: none !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--gray-500) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    transition: all 0.18s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--white) !important;
    color: var(--red) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

/* Buttons */
.stButton > button {
    background: var(--red) !important;
    color: var(--white) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: var(--red-dark) !important;
    box-shadow: var(--shadow-red) !important;
    transform: translateY(-1px) !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: var(--gray-900) !important;
    color: var(--white) !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
    padding: 9px 18px !important;
    transition: all 0.2s ease !important;
}

.stDownloadButton > button:hover {
    background: var(--red) !important;
    transform: translateY(-1px) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: var(--white) !important;
    border: 1.5px solid var(--gray-200) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--gray-900) !important;
}

.stSelectbox > div > div:focus-within {
    border-color: var(--red) !important;
    box-shadow: 0 0 0 2px rgba(232,0,45,0.12) !important;
}

/* Sliders */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--red) !important;
    border-color: var(--red) !important;
}

.stSlider [data-baseweb="slider"] [data-testid="stSliderTrackFill"] {
    background: var(--red) !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: var(--off-white) !important;
    border: 1px solid var(--gray-200) !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.8rem !important;
    letter-spacing: 0.05em !important;
    color: var(--gray-900) !important;
}

[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--gray-500) !important;
    font-weight: 600 !important;
}

/* DataFrames */
[data-testid="stDataFrame"] {
    border: 1.5px solid var(--gray-200) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Alerts */
.stSuccess {
    background: #F0FFF4 !important;
    border-color: #22C55E !important;
    border-radius: 8px !important;
}

.stWarning {
    background: #FFFBEB !important;
    border-color: #F59E0B !important;
    border-radius: 8px !important;
}

.stInfo {
    background: var(--cream) !important;
    border-color: var(--red) !important;
    border-radius: 8px !important;
}

/* Dividers */
hr {
    border: none !important;
    border-top: 1.5px solid var(--gray-100) !important;
    margin: 1.5rem 0 !important;
}

/* Insight boxes */
.insight-card {
    background: var(--white);
    border: 1px solid var(--gray-200);
    border-left: 3px solid var(--red);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 0.84rem;
    color: var(--gray-700);
    font-family: 'DM Sans', sans-serif;
}

.badge-red {
    display: inline-block;
    background: var(--red);
    color: white;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 4px;
    margin-right: 6px;
}

.badge-dark {
    display: inline-block;
    background: var(--gray-900);
    color: white;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 4px;
    margin-right: 6px;
}

/* Radio */
.stRadio [data-testid="stMarkdownContainer"] p {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--gray-500) !important;
    font-weight: 600 !important;
}

/* Checkbox */
.stCheckbox label span {
    font-size: 0.84rem !important;
    color: var(--gray-700) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--gray-100) !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* Multiselect */
.stMultiSelect [data-baseweb="tag"] {
    background: var(--red) !important;
    border-radius: 4px !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--gray-300) !important;
    border-radius: 12px !important;
    background: var(--off-white) !important;
}

/* Plotly charts */
.js-plotly-plot {
    border-radius: 12px !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Success alert with red theme */
.stAlert [data-testid="stMarkdownContainer"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
}

/* Sidebar nav labels */
.sidebar-nav-label {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: rgba(255,255,255,0.3);
    margin: 16px 0 8px;
    padding-left: 2px;
    font-family: 'DM Sans', sans-serif;
}

.sidebar-version {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: rgba(255,255,255,0.2);
    letter-spacing: 0.1em;
    margin-top: 4px;
}

.hero-welcome {
    background: var(--black);
    border-radius: 16px;
    padding: 3rem;
    text-align: center;
    margin: 2rem 0;
}

.hero-welcome h1 {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 4rem;
    letter-spacing: 0.1em;
    color: var(--white);
    margin: 0 0 0.5rem;
}

.hero-welcome h1 span { color: var(--red); }

.hero-welcome p {
    color: rgba(255,255,255,0.45);
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0;
}

.feature-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 2rem;
}

.feature-card {
    background: var(--white);
    border: 1px solid var(--gray-200);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: left;
}

.feature-card .icon {
    font-size: 1.5rem;
    margin-bottom: 0.8rem;
}

.feature-card .name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.2rem;
    letter-spacing: 0.08em;
    color: var(--gray-900);
    margin-bottom: 0.4rem;
}

.feature-card .desc {
    font-size: 0.8rem;
    color: var(--gray-500);
    line-height: 1.5;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--gray-100); }
::-webkit-scrollbar-thumb { background: var(--gray-300); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--red); }

/* Main block container fix */
.block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

from utils.loader import load_data, get_file_info

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0 16px;">
        <div class="apex-logo">APEX<span>.</span></div>
        <div class="apex-tagline">Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:0 0 16px;"></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "LOAD DATASET",
        type=["xlsx", "xls", "csv", "tsv"],
        help="Excel (.xlsx/.xls) or CSV/TSV",
        label_visibility="visible"
    )

    if uploaded_file:
        st.markdown(f"""
        <div style="background:rgba(232,0,45,0.12);border:1px solid rgba(232,0,45,0.3);
                    border-radius:8px;padding:8px 12px;margin:8px 0;font-size:0.75rem;
                    color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;">
            ✓ &nbsp;<strong style="color:white;">{uploaded_file.name}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-nav-label">Navigation</div>', unsafe_allow_html=True)

    page = st.radio(
        "Module",
        ["🏠  Overview & Profiling",
         "📈  Univariate Analysis",
         "🔗  Correlations & Bivariate",
         "🎯  KPI Dashboard",
         "📅  Time Series",
         "📤  Export & Report"],
        label_visibility="collapsed"
    )

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-version">APEX v2.0 · WORLD CLASS</div>', unsafe_allow_html=True)

# ── Main Header ─────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div class="hero-welcome">
        <h1>APEX<span>.</span>ANALYTICS</h1>
        <p>World-class data intelligence platform · Upload your dataset to begin</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-row">
        <div class="feature-card">
            <div class="icon">🔍</div>
            <div class="name">Auto Profiling</div>
            <div class="desc">Instant column profiling, missing values, outlier detection, and distribution analysis.</div>
        </div>
        <div class="feature-card">
            <div class="icon">📊</div>
            <div class="name">50+ Chart Types</div>
            <div class="desc">Histograms, scatter matrices, heatmaps, candlesticks, sunbursts, funnels, and more.</div>
        </div>
        <div class="feature-card">
            <div class="icon">🎯</div>
            <div class="name">KPI Dashboards</div>
            <div class="desc">Auto-built KPI gauges, waterfalls, treemaps, and funnel charts from your data.</div>
        </div>
        <div class="feature-card">
            <div class="icon">📅</div>
            <div class="name">Time Series</div>
            <div class="desc">OHLC candlesticks, seasonality heatmaps, moving averages, and cumulative returns.</div>
        </div>
        <div class="feature-card">
            <div class="icon">🔗</div>
            <div class="name">Correlation Engine</div>
            <div class="desc">Pearson / Spearman / Kendall matrices, ANOVA, Kruskal-Wallis significance tests.</div>
        </div>
        <div class="feature-card">
            <div class="icon">📤</div>
            <div class="name">One-Click Export</div>
            <div class="desc">Markdown reports, cleaned Excel/CSV, column profiles — all downloadable instantly.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Load data
df, sheet_info = load_data(uploaded_file)

if df is None:
    st.error("❌ Cannot read file. Check the format and try again.")
    st.stop()

st.session_state["df"] = df
st.session_state["filename"] = uploaded_file.name

# ── PAGE ROUTER ──────────────────────────────────────────────────────────────
if page == "🏠  Overview & Profiling":
    from pages.profiling import show
    show(df, uploaded_file.name, sheet_info)
elif page == "📈  Univariate Analysis":
    from pages.univariate import show
    show(df)
elif page == "🔗  Correlations & Bivariate":
    from pages.bivariate import show
    show(df)
elif page == "🎯  KPI Dashboard":
    from pages.kpi import show
    show(df)
elif page == "📅  Time Series":
    from pages.timeseries import show
    show(df)
elif page == "📤  Export & Report":
    from pages.export import show
    show(df, uploaded_file.name)

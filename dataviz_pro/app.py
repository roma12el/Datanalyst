import streamlit as st
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Décision Analytique",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --red: #E8002D;
    --red-soft: #FFF0F3;
    --white: #FFFFFF;
    --gray-50: #FAFAFA;
    --gray-100: #F4F4F5;
    --gray-200: #E4E4E7;
    --gray-400: #A1A1AA;
    --gray-600: #52525B;
    --gray-900: #09090B;
    --green: #16A34A;
    --green-soft: #F0FDF4;
    --orange: #EA580C;
    --orange-soft: #FFF7ED;
}

*, body { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] { background: var(--gray-50) !important; }

[data-testid="stSidebar"] {
    background: var(--gray-900) !important;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px dashed rgba(232,0,45,0.4) !important;
    border-radius: 8px !important;
}
.main .block-container {
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1400px !important;
}

/* Decision card */
.decision-card {
    background: white;
    border-radius: 12px;
    border: 1px solid var(--gray-200);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

/* Alert cards */
.alert-red {
    background: var(--red-soft);
    border: 1px solid rgba(232,0,45,0.25);
    border-left: 4px solid var(--red);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.84rem;
    color: #7F0018;
}
.alert-green {
    background: var(--green-soft);
    border: 1px solid rgba(22,163,74,0.25);
    border-left: 4px solid var(--green);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.84rem;
    color: #14532D;
}
.alert-orange {
    background: var(--orange-soft);
    border: 1px solid rgba(234,88,12,0.25);
    border-left: 4px solid var(--orange);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 0.84rem;
    color: #7C2D12;
}

/* KPI */
.kpi-row { display: flex; gap: 12px; margin: 1rem 0; flex-wrap: wrap; }
.kpi {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 10px;
    padding: 1rem 1.3rem;
    flex: 1;
    min-width: 130px;
}
.kpi .label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--gray-400);
    margin-bottom: 4px;
}
.kpi .val {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--gray-900);
    line-height: 1.1;
}
.kpi .sub { font-size: 0.72rem; color: var(--gray-400); margin-top: 3px; }
.kpi.danger .val { color: var(--red); }
.kpi.good .val { color: var(--green); }

/* Section header */
.section-header {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--gray-400);
    margin: 1.8rem 0 0.8rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--gray-200);
}

/* Page title */
.page-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--gray-900);
    margin: 0 0 4px;
}
.page-title span { color: var(--red); }
.page-sub {
    font-size: 0.8rem;
    color: var(--gray-400);
    margin-bottom: 1.5rem;
}

/* Buttons */
.stButton > button {
    background: var(--red) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 9px 18px !important;
}
.stDownloadButton > button {
    background: var(--gray-900) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--gray-100) !important;
    border-radius: 8px !important;
    padding: 3px !important;
    border: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--gray-400) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 7px 14px !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: var(--red) !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08) !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid var(--gray-200) !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: var(--gray-900) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid var(--gray-200) !important;
    border-radius: 8px !important;
}

/* Radio */
.stRadio [data-testid="stMarkdownContainer"] p {
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 600 !important;
    color: var(--gray-400) !important;
}
hr { border: none !important; border-top: 1px solid var(--gray-200) !important; margin: 1rem 0 !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--gray-100); }
::-webkit-scrollbar-thumb { background: var(--gray-200); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 12px">
        <div style="font-size:1.3rem;font-weight:800;color:white;letter-spacing:-0.02em">
            Décision <span style="color:#E8002D">Analytique</span>
        </div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.35);text-transform:uppercase;
                    letter-spacing:0.15em;margin-top:2px">Aide à la décision</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin-bottom:14px"></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Charger un fichier", type=["xlsx", "xls", "csv", "tsv"])

    if uploaded_file:
        st.markdown(f"""
        <div style="background:rgba(232,0,45,0.1);border:1px solid rgba(232,0,45,0.25);
                    border-radius:6px;padding:8px 10px;margin:8px 0;font-size:0.75rem;color:rgba(255,255,255,0.8)">
            ✓ {uploaded_file.name}
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:12px 0"></div>', unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Vue d'ensemble",
        "📊  Analyse des colonnes",
        "🔗  Relations entre variables",
        "⚠️  Alertes & Anomalies",
        "📤  Export",
    ], label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:rgba(255,255,255,0.08);margin:12px 0"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.6rem;color:rgba(255,255,255,0.2);letter-spacing:0.1em">DÉCISION ANALYTIQUE v1.0</div>', unsafe_allow_html=True)

# ── Welcome ───────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem">
        <div style="font-size:3rem;font-weight:800;color:#09090B;letter-spacing:-0.03em;margin-bottom:8px">
            Prenez de meilleures <span style="color:#E8002D">décisions</span>
        </div>
        <div style="font-size:1rem;color:#A1A1AA;max-width:520px;margin:0 auto 2.5rem;line-height:1.6">
            Chargez votre fichier Excel ou CSV. L'outil analyse automatiquement vos données
            et vous donne les insights clés pour agir.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1, "📋", "Vue d'ensemble instantanée", "KPIs, qualité des données, résumé en un coup d'œil"),
        (c2, "🔍", "Insights automatiques", "Anomalies, corrélations et patterns détectés automatiquement"),
        (c3, "⚠️", "Alertes décision", "Valeurs aberrantes, manques critiques, risques identifiés"),
    ]:
        with col:
            st.markdown(f"""
            <div class="decision-card" style="text-align:center">
                <div style="font-size:1.8rem;margin-bottom:10px">{icon}</div>
                <div style="font-weight:700;font-size:0.95rem;color:#09090B;margin-bottom:6px">{title}</div>
                <div style="font-size:0.8rem;color:#A1A1AA;line-height:1.5">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
from utils.loader import load_data
df, sheet_info = load_data(uploaded_file)
if df is None:
    st.error("❌ Impossible de lire ce fichier.")
    st.stop()

# ── Route ──────────────────────────────────────────────────────────────────────
if page == "🏠  Vue d'ensemble":
    from pages.overview import show; show(df, uploaded_file.name)
elif page == "📊  Analyse des colonnes":
    from pages.columns import show; show(df)
elif page == "🔗  Relations entre variables":
    from pages.relations import show; show(df)
elif page == "⚠️  Alertes & Anomalies":
    from pages.alerts import show; show(df)
elif page == "📤  Export":
    from pages.export import show; show(df, uploaded_file.name)

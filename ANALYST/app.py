import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="DataViz Pro — BI Trophy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header { color: #888; font-size: 0.95rem; margin-bottom: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem 1.5rem; border-radius: 12px;
        border-left: 4px solid #667eea;
        margin-bottom: 0.5rem;
    }
    .section-title {
        font-size: 1.3rem; font-weight: 600;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.4rem; margin: 1.5rem 0 1rem;
    }
    .insight-box {
        background: #f0f4ff; border: 1px solid #c3d0f7;
        border-radius: 8px; padding: 0.8rem 1rem;
        font-size: 0.88rem; color: #3a3a8c;
    }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 500; }
    div[data-testid="metric-container"] {
        background: #fafafa; border: 1px solid #eee;
        border-radius: 10px; padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

from utils.loader import load_data, get_file_info
from utils.profiling import compute_profile
from utils.charts import (univariate_charts, bivariate_charts,
                           time_series_charts, kpi_dashboard_charts)
from utils.export import export_report

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DataViz Pro")
    st.markdown("*BI Trophy — Analyse complète*")
    st.divider()

    uploaded_file = st.file_uploader(
        "📂 Charger un fichier",
        type=["xlsx", "xls", "csv", "tsv"],
        help="Excel (.xlsx/.xls) ou CSV/TSV"
    )

    if uploaded_file:
        st.success(f"✅ {uploaded_file.name}")

    st.divider()
    st.markdown("**Navigation**")
    page = st.radio(
        "Module",
        ["🏠 Accueil & Profiling",
         "📈 Analyse univariée",
         "🔗 Corrélations & Bivariée",
         "🎯 Tableau de bord KPI",
         "📅 Analyse temporelle",
         "📤 Export & Rapport"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("v1.0 — DataViz Pro Trophy")

# ── Main ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">📊 DataViz Pro — Business Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Analyse de données Excel/CSV de A à Z · Visualisations avancées Plotly · Reporting automatique</p>', unsafe_allow_html=True)

if not uploaded_file:
    st.info("👈 **Commencez** par charger un fichier Excel ou CSV dans la barre latérale.")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📂 Upload")
        st.markdown("Glissez n'importe quel fichier `.xlsx`, `.xls`, `.csv` ou `.tsv`.")
    with col2:
        st.markdown("### 🔍 Analyse")
        st.markdown("Profiling automatique, statistiques, valeurs manquantes, corrélations.")
    with col3:
        st.markdown("### 📤 Export")
        st.markdown("Rapport PDF complet, Excel nettoyé, tous graphiques PNG.")
    st.stop()

# Load data
df, sheet_info = load_data(uploaded_file)

if df is None:
    st.error("❌ Impossible de lire le fichier. Vérifiez le format.")
    st.stop()

# Store in session
st.session_state["df"] = df
st.session_state["filename"] = uploaded_file.name

# ── PAGE ROUTER ──────────────────────────────────────────────────────────────
if page == "🏠 Accueil & Profiling":
    from pages.profiling import show
    show(df, uploaded_file.name, sheet_info)

elif page == "📈 Analyse univariée":
    from pages.univariate import show
    show(df)

elif page == "🔗 Corrélations & Bivariée":
    from pages.bivariate import show
    show(df)

elif page == "🎯 Tableau de bord KPI":
    from pages.kpi import show
    show(df)

elif page == "📅 Analyse temporelle":
    from pages.timeseries import show
    show(df)

elif page == "📤 Export & Rapport":
    from pages.export import show
    show(df, uploaded_file.name)
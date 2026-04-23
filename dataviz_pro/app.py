import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

st.set_page_config(
    page_title="DataViz Pro — Tableau de bord universel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f4f6f9; }
[data-testid="stSidebar"] { background: #1e2d3d; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stRadio label { color: #ccd6e0 !important; font-size: 13px; }
[data-testid="stSidebar"] .stFileUploader label { color: white !important; }
[data-testid="stSidebar"] h3 { color: #e0e8f0 !important; border-bottom: 1px solid #2e4a63; padding-bottom: 6px; }
.block-container { padding: 1.5rem 2rem; }
div[data-testid="stMetric"] {
    background: white;
    border-radius: 10px;
    padding: 14px 16px;
    border-left: 4px solid #c0392b;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
div[data-testid="stMetric"] label { font-size: 12px !important; color: #666 !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 22px !important; color: #1e2d3d !important; }
</style>
""", unsafe_allow_html=True)

COLORS = [
    '#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad',
    '#16a085','#d35400','#2c3e50','#1abc9c','#e74c3c',
    '#3498db','#2ecc71','#e67e22','#9b59b6','#1abc9c'
]

# ─────────────────────────────────────────────
# LOADERS
# ─────────────────────────────────────────────

@st.cache_data
def load_excel(file_bytes, sheet_name):
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)

@st.cache_data
def load_csv(file_bytes):
    for sep in [';', ',', '\t', '|']:
        try:
            df = pd.read_csv(BytesIO(file_bytes), sep=sep, encoding='utf-8')
            if len(df.columns) > 1:
                return df
        except Exception:
            pass
    for sep in [';', ',', '\t']:
        try:
            df = pd.read_csv(BytesIO(file_bytes), sep=sep, encoding='latin-1')
            if len(df.columns) > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(BytesIO(file_bytes))

# ─────────────────────────────────────────────
# COLUMN TYPE DETECTION
# ─────────────────────────────────────────────

def detect_col_types(df):
    num_cols, cat_cols, date_cols = [], [], []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        # Already numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            num_cols.append(col)
            continue
        # Already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
            continue
        # Try numeric conversion (handle spaces, commas as decimal)
        cleaned = s.astype(str).str.replace(r'\s', '', regex=True).str.replace(',', '.', regex=False)
        try:
            converted_num = pd.to_numeric(cleaned, errors='coerce')
            num_ratio = converted_num.notna().sum() / len(s)
            if num_ratio > 0.8:
                df[col] = pd.to_numeric(cleaned, errors='coerce')
                num_cols.append(col)
                continue
        except Exception:
            pass
        # Try date conversion
        try:
            converted_date = pd.to_datetime(s, errors='coerce', dayfirst=True)
            date_ratio = converted_date.notna().sum() / len(s)
            if date_ratio > 0.7:
                df[col] = converted_date
                date_cols.append(col)
                continue
        except Exception:
            pass
        # Categorical
        cat_cols.append(col)
    return num_cols, cat_cols, date_cols

# ─────────────────────────────────────────────
# FORMATTERS
# ─────────────────────────────────────────────

def fmt_number(val):
    if pd.isna(val):
        return "N/A"
    val = float(val)
    if abs(val) >= 1_000_000_000:
        return f"{val/1_000_000_000:.2f} Md"
    elif abs(val) >= 1_000_000:
        return f"{val/1_000_000:.2f} M"
    elif abs(val) >= 1_000:
        return f"{val/1_000:.1f} K"
    elif val == int(val):
        return f"{int(val):,}"
    return f"{val:,.2f}"

def smart_chart(df, col, chart_type, max_cat, color_list, title=None):
    counts = df[col].astype(str).value_counts().head(max_cat).reset_index()
    counts.columns = [col, 'Nombre']
    t = title or col
    if chart_type == "Donut" and len(counts) <= 10:
        fig = px.pie(counts, names=col, values='Nombre',
                     color_discrete_sequence=color_list, hole=0.55, title=t)
        fig.update_traces(textposition='inside', textinfo='percent+label')
    elif chart_type == "Barres horizontales":
        fig = px.bar(counts, x='Nombre', y=col, orientation='h',
                     title=t, color=col, color_discrete_sequence=color_list)
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    else:
        fig = px.bar(counts, x=col, y='Nombre',
                     title=t, color=col, color_discrete_sequence=color_list)
    fig.update_layout(
        margin=dict(t=45, b=10, l=10, r=10),
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11),
        title_font_size=13,
        title_font_color='#c0392b'
    )
    return fig

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📁 Import données")
    uploaded = st.file_uploader(
        "Fichier Excel ou CSV",
        type=["xlsx", "xls", "csv"],
        help="Supporte : Excel (.xlsx/.xls) et CSV (séparateurs , ; tab)"
    )

    df = None
    num_cols, cat_cols, date_cols = [], [], []
    max_cat = 10
    chart_type = "Barres horizontales"

    if uploaded:
        file_bytes = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()

        try:
            if ext in ['xlsx', 'xls']:
                xl = pd.ExcelFile(BytesIO(file_bytes))
                sheets = xl.sheet_names
                if len(sheets) > 1:
                    sheet = st.selectbox("Feuille Excel", sheets)
                else:
                    sheet = sheets[0]
                df = load_excel(file_bytes, sheet)
            else:
                df = load_csv(file_bytes)
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

        if df is not None:
            # Clean column names
            df.columns = [str(c).strip() for c in df.columns]
            # Drop fully empty rows/cols
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df = df.reset_index(drop=True)

            num_cols, cat_cols, date_cols = detect_col_types(df)

            st.success(f"✅ {len(df):,} lignes · {len(df.columns)} colonnes")
            if num_cols:
                st.caption(f"Numériques : {', '.join(num_cols[:5])}{'...' if len(num_cols)>5 else ''}")
            if cat_cols:
                st.caption(f"Catégories : {', '.join(cat_cols[:5])}{'...' if len(cat_cols)>5 else ''}")
            if date_cols:
                st.caption(f"Dates : {', '.join(date_cols[:3])}")

            st.divider()
            st.markdown("### 🔽 Filtres")
            filters = {}
            for col in cat_cols[:5]:
                vals = sorted(df[col].dropna().astype(str).unique().tolist())
                if 2 <= len(vals) <= 50:
                    sel = st.multiselect(f"{col}", vals, default=[], key=f"f_{col}")
                    if sel:
                        filters[col] = sel

            for col, vals in filters.items():
                df = df[df[col].astype(str).isin(vals)]

            st.divider()
            st.markdown("### ⚙️ Options")
            max_cat = st.slider("Max catégories par graphique", 5, 25, 10)
            chart_type = st.radio(
                "Style graphiques catégories",
                ["Barres horizontales", "Barres verticales", "Donut"],
                horizontal=False
            )

# ─────────────────────────────────────────────
# MAIN — Accueil si pas de fichier
# ─────────────────────────────────────────────

if df is None:
    st.markdown("## 📊 DataViz Pro — Tableau de bord universel")
    st.markdown("**Importez n'importe quel fichier dans la barre latérale pour générer automatiquement votre tableau de bord.**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.info("**📈 Financier**\n\nCA, Charges, Marge, Budget, Écarts...")
    with c2:
        st.info("**⚙️ Opérationnel**\n\nProduction, Délais, Qualité, KPIs...")
    with c3:
        st.info("**👥 RH**\n\nEffectifs, Absences, Formations, Salaires...")
    with c4:
        st.info("**📦 Stocks / Ventes**\n\nInventaire, Commandes, Clients...")
    st.stop()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown(f"""
<div style="background:#1e2d3d;padding:18px 24px;border-radius:12px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center">
  <div>
    <span style="color:white;font-size:20px;font-weight:600">📊 Tableau de bord — {uploaded.name}</span>
    <span style="color:#8899aa;font-size:12px;margin-left:16px">{len(df):,} lignes · {len(df.columns)} colonnes</span>
  </div>
  <span style="background:#c0392b;color:white;padding:6px 14px;border-radius:8px;font-size:12px">DataViz Pro</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────

kpi_display = num_cols[:5]
n_kpis = len(kpi_display) + 1
kpi_cols = st.columns(n_kpis)

with kpi_cols[0]:
    st.metric("📋 Total lignes", f"{len(df):,}")

for i, col in enumerate(kpi_display):
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals) > 0:
        with kpi_cols[i + 1]:
            st.metric(
                label=f"∑ {col[:18]}",
                value=fmt_number(vals.sum()),
                delta=f"Moy: {fmt_number(vals.mean())}"
            )

st.divider()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Répartitions",
    "📈 Tendances & Croisements",
    "🔢 Statistiques",
    "🗂️ Données brutes"
])

# ── TAB 1 : Répartitions catégorielles ──
with tab1:
    if not cat_cols:
        st.info("Aucune colonne catégorielle détectée.")
    else:
        display_cats = cat_cols[:8]
        pairs = [display_cats[i:i+2] for i in range(0, len(display_cats), 2)]
        for pair in pairs:
            gcols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with gcols[ci]:
                    fig = smart_chart(df, col, chart_type, max_cat, COLORS)
                    st.plotly_chart(fig, use_container_width=True)

# ── TAB 2 : Tendances & Croisements ──
with tab2:
    all_time = date_cols + num_cols

    # Évolution temporelle
    if all_time and num_cols:
        st.markdown("#### 📈 Évolution dans le temps")
        h1, h2, h3 = st.columns(3)
        with h1:
            time_col = st.selectbox("Axe temporel", all_time, key="tc")
        with h2:
            val_col = st.selectbox("Valeur", num_cols, key="vc")
        with h3:
            if cat_cols:
                color_col = st.selectbox("Couleur par (optionnel)", ["Aucun"] + cat_cols, key="cc")
            else:
                color_col = "Aucun"

        try:
            ts = df[[time_col, val_col] + ([color_col] if color_col != "Aucun" else [])].copy()
            ts[time_col] = pd.to_datetime(ts[time_col], errors='coerce', dayfirst=True)
            ts = ts.dropna(subset=[time_col]).sort_values(time_col)
            if color_col != "Aucun":
                ts_g = ts.groupby([time_col, color_col])[val_col].sum().reset_index()
                fig3 = px.line(ts_g, x=time_col, y=val_col, color=color_col,
                               color_discrete_sequence=COLORS,
                               title=f"Évolution de {val_col}")
            else:
                ts_g = ts.groupby(time_col)[val_col].sum().reset_index()
                fig3 = px.line(ts_g, x=time_col, y=val_col,
                               color_discrete_sequence=[COLORS[0]],
                               title=f"Évolution de {val_col}")
                fig3.update_traces(fill='tozeroy', fillcolor='rgba(192,57,43,0.08)')
            fig3.update_layout(
                margin=dict(t=45,b=10,l=10,r=10), height=340,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                title_font_color='#c0392b', title_font_size=13
            )
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossible de tracer la tendance : {e}")

    st.divider()

    # Analyse croisée
    if num_cols and cat_cols:
        st.markdown("#### 🔀 Analyse croisée")
        h1, h2, h3 = st.columns(3)
        with h1:
            x_col = st.selectbox("Catégorie (axe X)", cat_cols, key="xc")
        with h2:
            y_col = st.selectbox("Valeur (axe Y)", num_cols, key="yc")
        with h3:
            agg = st.selectbox("Agrégation", ["Somme","Moyenne","Compte","Max","Min"], key="ag")

        agg_map = {"Somme":"sum","Moyenne":"mean","Compte":"count","Max":"max","Min":"min"}
        grouped = (df.groupby(x_col)[y_col]
                   .agg(agg_map[agg])
                   .reset_index()
                   .sort_values(y_col, ascending=False)
                   .head(max_cat))
        fig2 = px.bar(grouped, x=x_col, y=y_col,
                      color=x_col, color_discrete_sequence=COLORS,
                      title=f"{agg} de {y_col} par {x_col}")
        fig2.update_layout(
            margin=dict(t=45,b=10,l=10,r=10), height=340, showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            title_font_color='#c0392b', title_font_size=13
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Scatter
    if len(num_cols) >= 2:
        st.divider()
        st.markdown("#### 🔵 Nuage de points")
        h1, h2, h3 = st.columns(3)
        with h1: sx = st.selectbox("Axe X", num_cols, key="sx")
        with h2: sy = st.selectbox("Axe Y", num_cols, index=min(1,len(num_cols)-1), key="sy")
        with h3:
            sc = st.selectbox("Couleur", ["Aucun"] + cat_cols, key="scol") if cat_cols else "Aucun"
        fig_s = px.scatter(
            df, x=sx, y=sy,
            color=sc if sc != "Aucun" else None,
            color_discrete_sequence=COLORS,
            opacity=0.6,
            title=f"{sx} vs {sy}"
        )
        fig_s.update_layout(
            margin=dict(t=45,b=10,l=10,r=10), height=340,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            title_font_color='#c0392b', title_font_size=13
        )
        st.plotly_chart(fig_s, use_container_width=True)

# ── TAB 3 : Statistiques ──
with tab3:
    if num_cols:
        st.markdown("#### 📊 Statistiques descriptives")
        stats = df[num_cols].describe().T
        stats.index.name = "Colonne"
        stats = stats.round(2)
        st.dataframe(stats, use_container_width=True)

        st.divider()

        # Distribution
        st.markdown("#### 📉 Distribution d'une variable")
        dist_col = st.selectbox("Variable", num_cols, key="dist_col")
        fig_hist = px.histogram(
            df, x=dist_col, nbins=30,
            color_discrete_sequence=[COLORS[0]],
            title=f"Distribution de {dist_col}",
            marginal="box"
        )
        fig_hist.update_layout(
            margin=dict(t=45,b=10,l=10,r=10), height=340,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            title_font_color='#c0392b', title_font_size=13
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        # Corrélations
        if len(num_cols) >= 2:
            st.divider()
            st.markdown("#### 🔗 Matrice de corrélation")
            corr = df[num_cols].corr().round(2)
            fig_corr = px.imshow(
                corr, text_auto=True,
                color_continuous_scale='RdBu_r',
                title="Corrélations entre variables numériques"
            )
            fig_corr.update_layout(
                margin=dict(t=45,b=10,l=10,r=10), height=max(300, len(num_cols)*50),
                title_font_color='#c0392b', title_font_size=13
            )
            st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Aucune colonne numérique détectée pour les statistiques.")

# ── TAB 4 : Données brutes ──
with tab4:
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Rechercher dans les données", "", key="search")
    with col2:
        sort_col = st.selectbox("Trier par", ["—"] + list(df.columns), key="sort_col")

    display_df = df.copy()

    if search:
        mask = display_df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        display_df = display_df[mask]

    if sort_col != "—":
        display_df = display_df.sort_values(sort_col, ascending=False)

    st.dataframe(display_df, height=450, use_container_width=True)
    st.caption(f"{len(display_df):,} lignes · {len(display_df.columns)} colonnes")

    c1, c2 = st.columns(2)
    with c1:
        buf_xlsx = BytesIO()
        display_df.to_excel(buf_xlsx, index=False)
        st.download_button(
            label="📥 Exporter en Excel",
            data=buf_xlsx.getvalue(),
            file_name="export_dashboard.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with c2:
        buf_csv = display_df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            label="📥 Exporter en CSV",
            data=buf_csv,
            file_name="export_dashboard.csv",
            mime="text/csv"
        )

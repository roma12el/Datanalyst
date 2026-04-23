import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(
    page_title="Tableau de bord universel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {background:#1e2d3d;padding:20px 28px;border-radius:12px;margin-bottom:24px;}
    .main-header h1 {color:white;font-size:22px;margin:0;}
    .main-header p {color:#8899aa;font-size:13px;margin:4px 0 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📊 Tableau de bord universel</h1>
    <p>Financier · Opérationnel · RH · Stocks · Ventes · Informatique · ...</p>
</div>
""", unsafe_allow_html=True)

COLORS = ['#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad',
          '#16a085','#d35400','#2c3e50','#1abc9c','#e74c3c']

@st.cache_data
def load_excel(file_bytes, sheet_name):
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)

@st.cache_data
def load_csv(file_bytes):
    for sep in [',', ';', '\t']:
        try:
            df = pd.read_csv(BytesIO(file_bytes), sep=sep)
            if len(df.columns) > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(BytesIO(file_bytes))

def detect_col_types(df):
    num_cols, cat_cols, date_cols = [], [], []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            num_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        else:
            try:
                converted = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                if converted.notna().sum() / max(len(converted), 1) > 0.5:
                    date_cols.append(col)
                else:
                    cat_cols.append(col)
            except Exception:
                cat_cols.append(col)
    return num_cols, cat_cols, date_cols

def fmt_number(val):
    if abs(val) >= 1_000_000:
        return f"{val/1_000_000:.2f} M"
    elif abs(val) >= 1_000:
        return f"{val/1_000:.1f} K"
    return f"{val:,.2f}"

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 📁 Import fichier")
    uploaded = st.file_uploader(
        "Choisir un fichier Excel ou CSV",
        type=["xlsx", "xls", "csv"],
        help="Tout type de données : financières, RH, opérationnelles, stocks..."
    )

    df = None
    num_cols, cat_cols, date_cols = [], [], []
    max_cat = 10
    chart_type = "Barres"

    if uploaded:
        file_bytes = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()

        if ext in ['xlsx', 'xls']:
            xl = pd.ExcelFile(BytesIO(file_bytes))
            sheets = xl.sheet_names
            sheet = st.selectbox("Feuille Excel", sheets) if len(sheets) > 1 else sheets[0]
            df = load_excel(file_bytes, sheet)
        else:
            df = load_csv(file_bytes)

        if df is not None:
            st.success(f"{len(df):,} lignes · {len(df.columns)} colonnes")
            num_cols, cat_cols, date_cols = detect_col_types(df)

            st.divider()
            st.markdown("### 🔽 Filtres")
            filters = {}
            for col in cat_cols[:4]:
                vals = sorted(df[col].dropna().astype(str).unique().tolist())
                if 2 <= len(vals) <= 30:
                    sel = st.multiselect(f"Filtrer : {col}", vals, default=[], key=f"f_{col}")
                    if sel:
                        filters[col] = sel

            for col, vals in filters.items():
                df = df[df[col].astype(str).isin(vals)]

            st.divider()
            st.markdown("### ⚙️ Options")
            max_cat = st.slider("Max catégories", 5, 20, 10)
            chart_type = st.radio("Style graphique", ["Barres", "Donut"], horizontal=True)

# ── Main ──
if df is None:
    st.info("👈 Importez un fichier dans la barre latérale.")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown("**📈 Financier**\n\nCA, Charges, Budget, Marge...")
    with c2: st.markdown("**⚙️ Opérationnel**\n\nProduction, Qualité, KPIs...")
    with c3: st.markdown("**👥 RH · Stocks · Ventes**\n\nEffectifs, Inventaire...")
    st.stop()

st.markdown(f"**{len(df):,}** lignes affichées")

# KPIs
if num_cols:
    kpi_count = min(len(num_cols) + 1, 6)
    cols_kpi = st.columns(kpi_count)
    with cols_kpi[0]:
        st.metric("Total lignes", f"{len(df):,}")
    for i, col in enumerate(num_cols[:5]):
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) > 0:
            with cols_kpi[i + 1]:
                st.metric(col[:22], fmt_number(vals.sum()), f"Moy: {fmt_number(vals.mean())}")

st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Graphiques", "📈 Tendances", "🗂️ Données"])

with tab1:
    if cat_cols:
        pairs = [cat_cols[i:i+2] for i in range(0, min(len(cat_cols), 6), 2)]
        for pair in pairs:
            gcols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with gcols[ci]:
                    counts = df[col].astype(str).value_counts().head(max_cat).reset_index()
                    counts.columns = [col, 'count']
                    if chart_type == "Donut" and len(counts) <= 8:
                        fig = px.pie(counts, names=col, values='count',
                                     color_discrete_sequence=COLORS, hole=0.55, title=col)
                    else:
                        fig = px.bar(counts, x='count', y=col, orientation='h',
                                     title=col, color=col, color_discrete_sequence=COLORS)
                    fig.update_layout(margin=dict(t=40,b=0,l=0,r=0), height=280,
                                      showlegend=False,
                                      plot_bgcolor='rgba(0,0,0,0)',
                                      paper_bgcolor='rgba(0,0,0,0)', font_size=11)
                    st.plotly_chart(fig, use_container_width=True)

    if num_cols and cat_cols:
        st.markdown("#### Analyse croisée")
        h1, h2, h3 = st.columns(3)
        with h1: x_col = st.selectbox("Catégorie", cat_cols, key="x_col")
        with h2: y_col = st.selectbox("Valeur", num_cols, key="y_col")
        with h3: agg = st.selectbox("Agrégation", ["Somme","Moyenne","Compte","Max","Min"], key="agg")

        agg_map = {"Somme":"sum","Moyenne":"mean","Compte":"count","Max":"max","Min":"min"}
        grouped = df.groupby(x_col)[y_col].agg(agg_map[agg]).reset_index().sort_values(y_col, ascending=False).head(max_cat)
        fig2 = px.bar(grouped, x=x_col, y=y_col, color_discrete_sequence=[COLORS[0]],
                      title=f"{agg} de {y_col} par {x_col}")
        fig2.update_layout(margin=dict(t=40,b=0,l=0,r=0), height=320,
                           plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    all_time_cols = date_cols + num_cols
    if all_time_cols and num_cols:
        h1, h2 = st.columns(2)
        with h1: time_col = st.selectbox("Colonne temporelle", all_time_cols, key="time_col")
        with h2: val_col = st.selectbox("Valeur", num_cols, key="val_col")
        try:
            ts = df[[time_col, val_col]].copy()
            ts[time_col] = pd.to_datetime(ts[time_col], errors='coerce', dayfirst=True)
            ts = ts.dropna().sort_values(time_col)
            ts_g = ts.groupby(time_col)[val_col].sum().reset_index()
            fig3 = px.line(ts_g, x=time_col, y=val_col, title=f"Évolution de {val_col}",
                           color_discrete_sequence=[COLORS[0]])
            fig3.update_traces(fill='tozeroy', fillcolor='rgba(192,57,43,0.1)')
            fig3.update_layout(margin=dict(t=40,b=0,l=0,r=0), height=320,
                               plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossible de tracer la tendance : {e}")

        if len(num_cols) >= 2:
            st.markdown("#### Corrélations")
            corr = df[num_cols].corr()
            fig4 = px.imshow(corr, text_auto=".2f", color_continuous_scale='RdBu_r',
                             title="Matrice de corrélation")
            fig4.update_layout(margin=dict(t=40,b=0,l=0,r=0), height=350)
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Aucune colonne numérique ou de date détectée.")

with tab3:
    search = st.text_input("Rechercher dans les données", "", key="search_input")
    display_df = df.copy()
    if search:
        mask = display_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    st.dataframe(display_df, height=400, use_container_width=True)
    st.caption(f"{len(display_df):,} lignes affichées")

    buf = BytesIO()
    display_df.to_excel(buf, index=False)
    st.download_button(
        label="📥 Exporter les données filtrées (.xlsx)",
        data=buf.getvalue(),
        file_name="donnees_filtrees.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

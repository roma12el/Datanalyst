import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="Tableau de bord universel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: #1e2d3d;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .main-header h1 { color: white; font-size: 22px; margin: 0; }
    .main-header p { color: #8899aa; font-size: 13px; margin: 4px 0 0; }
    .badge {
        background: #c0392b;
        color: white;
        padding: 4px 14px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        display: inline-block;
        float: right;
        margin-top: -28px;
    }
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        border-left: 4px solid #c0392b;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
    div[data-testid="stMetric"] {
        background: var(--background-color);
        border-radius: 10px;
        padding: 12px 16px;
        border: 0.5px solid rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📊 Tableau de bord universel</h1>
    <p>Financier · Opérationnel · RH · Stocks · Ventes · Informatique · ...</p>
    <span class="badge">Import Excel</span>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_excel(file_bytes, sheet_name):
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)

def detect_col_types(df):
    num_cols, cat_cols, date_cols = [], [], []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            num_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        else:
            try:
                pd.to_datetime(df[col], errors='raise')
                date_cols.append(col)
            except:
                cat_cols.append(col)
    return num_cols, cat_cols, date_cols

def fmt_number(val):
    if abs(val) >= 1_000_000:
        return f"{val/1_000_000:.2f} M"
    elif abs(val) >= 1_000:
        return f"{val/1_000:.1f} K"
    return f"{val:,.2f}"

with st.sidebar:
    st.markdown("### 📁 Import fichier")
    uploaded = st.file_uploader(
        "Choisir un fichier Excel",
        type=["xlsx", "xls"],
        help="Tout type de données : financières, RH, opérationnelles, stocks..."
    )

    if uploaded:
        file_bytes = uploaded.read()
        xl = pd.ExcelFile(BytesIO(file_bytes))
        sheets = xl.sheet_names

        sheet = st.selectbox("📋 Feuille", sheets) if len(sheets) > 1 else sheets[0]
        df_raw = load_excel(file_bytes, sheet)

        st.markdown(f"**{len(df_raw):,}** lignes · **{len(df_raw.columns)}** colonnes")
        st.divider()

        num_cols, cat_cols, date_cols = detect_col_types(df_raw)

        st.markdown("### 🔽 Filtres")
        filters = {}
        for col in cat_cols[:4]:
            vals = sorted(df_raw[col].dropna().unique().tolist())
            if len(vals) <= 30:
                sel = st.multiselect(col, vals, default=[], key=f"f_{col}")
                if sel:
                    filters[col] = sel

        df = df_raw.copy()
        for col, vals in filters.items():
            df = df[df[col].isin(vals)]

        st.divider()
        st.markdown("### ⚙️ Options graphiques")
        max_cat = st.slider("Max catégories par graphique", 5, 20, 10)
        chart_type = st.radio("Type graphique catégories", ["Barres", "Donut"], horizontal=True)
    else:
        df = None
        num_cols, cat_cols, date_cols = [], [], []
        max_cat = 10
        chart_type = "Barres"

if df is None:
    st.info("👈 Importez un fichier Excel dans la barre latérale pour générer votre tableau de bord automatiquement.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📈 Données financières**\n\nCA, Charges, Marge, Budget, Écart...")
    with col2:
        st.markdown("**⚙️ Données opérationnelles**\n\nProduction, Qualité, Délais, KPIs...")
    with col3:
        st.markdown("**👥 RH / Stocks / Ventes**\n\nEffectifs, Inventaire, Commandes...")
    st.stop()

st.markdown(f"#### Données filtrées : **{len(df):,}** lignes sur {len(df_raw):,}")

if num_cols:
    kpi_cols = st.columns(min(len(num_cols) + 1, 6))
    with kpi_cols[0]:
        st.metric("Total lignes", f"{len(df):,}")
    for i, col in enumerate(num_cols[:5]):
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        with kpi_cols[i + 1]:
            st.metric(
                label=col[:20],
                value=fmt_number(vals.sum()),
                delta=f"Moy: {fmt_number(vals.mean())}"
            )

st.divider()

COLORS = ['#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad',
          '#16a085','#d35400','#2c3e50','#1abc9c','#e74c3c']

tab1, tab2, tab3 = st.tabs(["📊 Graphiques", "📈 Tendances", "🗂️ Données"])

with tab1:
    if cat_cols:
        cols_per_row = 2
        rows = [cat_cols[i:i+cols_per_row] for i in range(0, min(len(cat_cols), 6), cols_per_row)]
        for row in rows:
            gcols = st.columns(len(row))
            for ci, col in enumerate(row):
                with gcols[ci]:
                    counts = df[col].value_counts().head(max_cat).reset_index()
                    counts.columns = [col, 'count']
                    if chart_type == "Donut" and len(counts) <= 8:
                        fig = px.pie(counts, names=col, values='count',
                                     color_discrete_sequence=COLORS, hole=0.55,
                                     title=col)
                    else:
                        fig = px.bar(counts, x='count', y=col, orientation='h',
                                     color_discrete_sequence=[COLORS[0]],
                                     title=col)
                        fig.update_traces(marker_color=COLORS)
                    fig.update_layout(
                        margin=dict(t=40,b=0,l=0,r=0),
                        height=280,
                        showlegend=chart_type=="Donut",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_size=11
                    )
                    st.plotly_chart(fig, use_container_width=True)

    if num_cols and cat_cols:
        st.markdown("#### Analyse croisée")
        c1, c2, c3 = st.columns(3)
        with c1:
            x_col = st.selectbox("Catégorie (axe X)", cat_cols, key="x_col")
        with c2:
            y_col = st.selectbox("Valeur (axe Y)", num_cols, key="y_col")
        with c3:
            agg = st.selectbox("Agrégation", ["Somme", "Moyenne", "Compte", "Max", "Min"])

        agg_map = {"Somme": "sum", "Moyenne": "mean", "Compte": "count", "Max": "max", "Min": "min"}
        grouped = df.groupby(x_col)[y_col].agg(agg_map[agg]).reset_index().sort_values(y_col, ascending=False).head(max_cat)
        fig2 = px.bar(grouped, x=x_col, y=y_col,
                      color_discrete_sequence=[COLORS[0]],
                      title=f"{agg} de {y_col} par {x_col}")
        fig2.update_layout(
            margin=dict(t=40,b=0,l=0,r=0), height=320,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    if date_cols or num_cols:
        c1, c2 = st.columns(2)
        with c1:
            time_col = st.selectbox("Colonne temporelle / Index", date_cols + num_cols if date_cols else num_cols, key="time")
        with c2:
            val_col = st.selectbox("Valeur à suivre", num_cols, key="val")

        try:
            ts = df[[time_col, val_col]].copy()
            ts[time_col] = pd.to_datetime(ts[time_col], errors='coerce')
            ts = ts.dropna().sort_values(time_col)
            ts_grouped = ts.groupby(time_col)[val_col].sum().reset_index()
            fig3 = px.line(ts_grouped, x=time_col, y=val_col,
                           title=f"Évolution de {val_col} dans le temps",
                           color_discrete_sequence=[COLORS[0]])
            fig3.update_traces(fill='tozeroy', fillcolor='rgba(192,57,43,0.1)')
            fig3.update_layout(
                margin=dict(t=40,b=0,l=0,r=0), height=320,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossible de tracer la tendance : {e}")

        if len(num_cols) >= 2:
            st.markdown("#### Corrélations entre variables numériques")
            corr = df[num_cols].corr()
            fig4 = px.imshow(corr, text_auto=".2f", color_continuous_scale='RdBu_r',
                             title="Matrice de corrélation")
            fig4.update_layout(margin=dict(t=40,b=0,l=0,r=0), height=300)
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Aucune colonne numérique ou de date détectée pour les tendances.")

with tab3:
    search = st.text_input("🔍 Rechercher dans les données", "")
    display_df = df.copy()
    if search:
        mask = display_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    st.dataframe(display_df, use_container_width=True, height=400)
    st.caption(f"{len(display_df):,} lignes affichées")

    buf = BytesIO()
    display_df.to_excel(buf, index=False)
    st.download_button(
        "📥 Exporter les données filtrées (.xlsx)",
        data=buf.getvalue(),
        file_name="donnees_filtrees.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

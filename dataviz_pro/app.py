"""
DataViz Pro — Tableau de bord automatique style Power BI
Upload Excel/CSV → analyse complète automatique en un clic
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import io
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataViz Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

PALETTE = px.colors.qualitative.Set2
TEMPLATE = "plotly_white"

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-row > div { background:#f8f9ff; border-radius:10px; border-left:4px solid #667eea; padding:0.3rem 0.5rem; }
    h1 { font-size:1.8rem !important; }
    h2 { font-size:1.2rem !important; color:#444; border-bottom:2px solid #667eea; padding-bottom:4px; }
    .stTabs [data-baseweb="tab"] { font-weight:500; }
    div[data-testid="metric-container"] { background:#f8f9ff; border-radius:8px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_file(f):
    """Load Excel or CSV into DataFrame. Returns (df, error_str)."""
    name = f.name.lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            xl = pd.ExcelFile(f)
            sheet = xl.sheet_names[0]
            if len(xl.sheet_names) > 1:
                sheet = st.sidebar.selectbox("📋 Feuille Excel", xl.sheet_names)
            df = pd.read_excel(f, sheet_name=sheet)
        elif name.endswith(".csv"):
            raw = f.read(4096).decode("utf-8", errors="replace")
            f.seek(0)
            sep = ";" if raw.count(";") > raw.count(",") else ","
            df = pd.read_csv(f, sep=sep, on_bad_lines="skip")
        elif name.endswith(".tsv"):
            df = pd.read_csv(f, sep="\t", on_bad_lines="skip")
        else:
            return None, "Format non supporté. Utilisez .xlsx, .xls, .csv ou .tsv"
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        return df, None
    except Exception as e:
        return None, str(e)


def classify_columns(df):
    """Classify columns into numeric, categorical, date."""
    num_cols, cat_cols, date_cols = [], [], []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            num_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(s):
            date_cols.append(col)
        else:
            # Try parsing as date
            try:
                parsed = pd.to_datetime(s, infer_datetime_format=True, errors="coerce")
                if parsed.notna().mean() > 0.6:
                    date_cols.append(col)
                    continue
            except Exception:
                pass
            cat_cols.append(col)
    return num_cols, cat_cols, date_cols


def safe_fig(fig, height=420):
    fig.update_layout(height=height, template=TEMPLATE,
                      margin=dict(t=50, b=30, l=20, r=20))
    return fig


def fmt_number(v):
    if abs(v) >= 1e9:
        return f"{v/1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"{v/1e6:.2f}M"
    if abs(v) >= 1e3:
        return f"{v/1e3:.1f}K"
    return f"{v:.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DataViz Pro")
    st.caption("Tableau de bord automatique — style Power BI")
    st.divider()
    uploaded = st.file_uploader(
        "📂 Charger votre fichier",
        type=["xlsx", "xls", "csv", "tsv"],
        help="Excel ou CSV — l'analyse se fait automatiquement"
    )
    st.divider()
    st.caption("v2.0 — Analyse 100% automatique")

# ─────────────────────────────────────────────────────────────────────────────
# WELCOME SCREEN
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 📊 DataViz Pro — Tableau de bord automatique")

if not uploaded:
    st.info("👈 **Chargez un fichier Excel ou CSV** dans la barre latérale pour démarrer l'analyse automatique.")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("### 🔍\n**Profiling**\nQualité des données, valeurs manquantes, doublons")
    c2.markdown("### 📈\n**Distributions**\nHistogrammes, boxplots, violin pour chaque colonne")
    c3.markdown("### 🔗\n**Corrélations**\nMatrice, scatter plots, analyses bivariées")
    c4.markdown("### 📅\n**Temporel**\nSéries temporelles, saisonnalité, tendances")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
df, err = load_file(uploaded)
if err or df is None:
    st.error(f"❌ Erreur de lecture : {err}")
    st.stop()

num_cols, cat_cols, date_cols = classify_columns(df)

# ─────────────────────────────────────────────────────────────────────────────
# TOP KPI BAR
# ─────────────────────────────────────────────────────────────────────────────
missing_total = int(df.isnull().sum().sum())
missing_pct = round(100 * missing_total / max(df.shape[0] * df.shape[1], 1), 1)
dupes = int(df.duplicated().sum())
quality_score = max(0, 100 - missing_pct - (10 if dupes > 0 else 0))

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📋 Lignes", f"{len(df):,}")
k2.metric("📊 Colonnes", len(df.columns))
k3.metric("🔢 Numériques", len(num_cols))
k4.metric("🔤 Catégorielles", len(cat_cols))
k5.metric("❓ Manquants", f"{missing_pct}%",
          delta="⚠️ Attention" if missing_pct > 10 else "✅ OK",
          delta_color="inverse" if missing_pct > 10 else "normal")
k6.metric("🏆 Qualité", f"{quality_score:.0f}/100",
          delta="Bon" if quality_score >= 80 else "À améliorer",
          delta_color="normal" if quality_score >= 80 else "inverse")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🔍 Qualité des données",
    "📈 Distributions",
    "🔗 Corrélations",
    "🎯 KPI & Agrégations",
    "📅 Séries temporelles",
    "📤 Export"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — QUALITÉ
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown("## 🔍 Qualité des données")

    # Aperçu
    with st.expander("📋 Aperçu des données", expanded=True):
        n = st.slider("Lignes à afficher", 5, 50, 10, key="prev_n")
        st.dataframe(df.head(n), use_container_width=True)

    # Profil par colonne
    st.markdown("## 📋 Profil automatique des colonnes")
    profile_rows = []
    for col in df.columns:
        s = df[col]
        row = {
            "Colonne": col,
            "Type": "Numérique" if col in num_cols else ("Date" if col in date_cols else "Catégorielle"),
            "Manquants": int(s.isnull().sum()),
            "% Manquant": f"{100 * s.isnull().sum() / len(s):.1f}%",
            "Uniques": int(s.nunique()),
        }
        if col in num_cols:
            row["Min"] = f"{s.min():.3g}"
            row["Max"] = f"{s.max():.3g}"
            row["Moyenne"] = f"{s.mean():.3g}"
            row["Médiane"] = f"{s.median():.3g}"
            row["Écart-type"] = f"{s.std():.3g}"
        else:
            top = s.value_counts()
            row["Min"] = row["Max"] = row["Moyenne"] = row["Médiane"] = row["Écart-type"] = "—"
            if not top.empty:
                row["Valeur top"] = f"{top.index[0]} ({top.iloc[0]})"
            else:
                row["Valeur top"] = "—"
        profile_rows.append(row)

    profile_df = pd.DataFrame(profile_rows)
    st.dataframe(profile_df, use_container_width=True, height=400)

    # Valeurs manquantes
    st.markdown("## ❓ Valeurs manquantes")
    missing_series = df.isnull().sum()
    missing_series = missing_series[missing_series > 0].sort_values(ascending=False)

    if missing_series.empty:
        st.success("✅ Aucune valeur manquante — dataset propre !")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            miss_df = pd.DataFrame({
                "Colonne": missing_series.index,
                "Manquants": missing_series.values,
                "% Total": (100 * missing_series / len(df)).round(1)
            })
            colors = ["#c0392b" if p > 30 else "#e67e22" if p > 10 else "#f1c40f"
                      for p in miss_df["% Total"]]
            fig = go.Figure(go.Bar(
                x=miss_df["Colonne"], y=miss_df["% Total"],
                marker_color=colors,
                text=[f"{v:.1f}%" for v in miss_df["% Total"]],
                textposition="outside"
            ))
            fig.update_layout(
                title="% Valeurs manquantes par colonne",
                yaxis_title="% Manquant", height=380, template=TEMPLATE,
                yaxis_range=[0, min(110, miss_df["% Total"].max() * 1.2)]
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.dataframe(miss_df, use_container_width=True, height=380)

    # Doublons
    st.markdown("## 🔁 Doublons")
    if dupes == 0:
        st.success("✅ Aucun doublon détecté.")
    else:
        st.warning(f"⚠️ {dupes} lignes dupliquées ({100*dupes/len(df):.1f}% du dataset)")
        with st.expander("Voir les doublons"):
            st.dataframe(df[df.duplicated()].head(20), use_container_width=True)

    # Insights auto
    st.markdown("## 🤖 Insights automatiques")
    insights = []
    if missing_pct > 20:
        insights.append(("🔴", f"{missing_pct}% de valeurs manquantes — imputation recommandée."))
    elif missing_pct > 5:
        insights.append(("🟡", f"{missing_pct}% de valeurs manquantes — à surveiller."))
    else:
        insights.append(("🟢", "Taux de complétude excellent (> 95%)."))
    if dupes > 0:
        insights.append(("🟡", f"{dupes} doublons détectés — risque de biais."))
    for col in num_cols[:6]:
        skew = df[col].skew()
        if abs(skew) > 2:
            insights.append(("🟡", f"'{col}' : très asymétrique (skew={skew:.1f}) — transformation log conseillée."))
    for col in cat_cols:
        if df[col].nunique() > 50:
            insights.append(("🔵", f"'{col}' : haute cardinalité ({df[col].nunique()} valeurs uniques)."))

    for icon, msg in insights[:8]:
        st.markdown(f"{icon} {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DISTRIBUTIONS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("## 📈 Distributions automatiques")

    if num_cols:
        st.markdown("### 🔢 Colonnes numériques")

        # Grid automatique — histogramme pour chaque colonne num (max 12)
        show_cols = num_cols[:12]
        n_cols_grid = min(3, len(show_cols))
        rows_grid = (len(show_cols) + n_cols_grid - 1) // n_cols_grid

        for row_i in range(rows_grid):
            grid_cols = st.columns(n_cols_grid)
            for col_i in range(n_cols_grid):
                idx = row_i * n_cols_grid + col_i
                if idx >= len(show_cols):
                    break
                col_name = show_cols[idx]
                s = df[col_name].dropna()
                with grid_cols[col_i]:
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=s, nbinsx=25,
                        marker_color="#667eea", opacity=0.8,
                        histnorm="probability density", name=col_name
                    ))
                    # Courbe normale
                    if len(s) > 5 and s.std() > 0:
                        xr = np.linspace(s.min(), s.max(), 200)
                        fig.add_trace(go.Scatter(
                            x=xr, y=stats.norm.pdf(xr, s.mean(), s.std()),
                            mode="lines", line=dict(color="#e74c3c", width=2),
                            name="Normale", showlegend=False
                        ))
                    fig.update_layout(
                        title=dict(text=col_name, font=dict(size=13)),
                        height=240, template=TEMPLATE,
                        margin=dict(t=35, b=20, l=20, r=10),
                        showlegend=False,
                        xaxis=dict(title=None),
                        yaxis=dict(title=None)
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Boxplot comparatif
        st.markdown("### 📦 Boxplots comparatifs")
        sel_box = st.multiselect(
            "Colonnes à comparer (boxplot)",
            num_cols, default=num_cols[:min(5, len(num_cols))],
            key="box_sel"
        )
        if sel_box:
            fig_box = go.Figure()
            for i, col in enumerate(sel_box):
                s = df[col].dropna()
                fig_box.add_trace(go.Box(
                    y=s, name=col,
                    marker_color=PALETTE[i % len(PALETTE)],
                    boxpoints="outliers"
                ))
            fig_box.update_layout(
                title="Comparaison des distributions — Boxplot",
                height=450, template=TEMPLATE
            )
            st.plotly_chart(fig_box, use_container_width=True)

    if cat_cols:
        st.markdown("### 🔤 Colonnes catégorielles")
        show_cat = cat_cols[:9]
        n_cols_c = min(3, len(show_cat))

        for row_i in range((len(show_cat) + n_cols_c - 1) // n_cols_c):
            grid = st.columns(n_cols_c)
            for col_i in range(n_cols_c):
                idx = row_i * n_cols_c + col_i
                if idx >= len(show_cat):
                    break
                col_name = show_cat[idx]
                vc = df[col_name].value_counts().head(10)
                with grid[col_i]:
                    fig = px.bar(
                        x=vc.index.astype(str), y=vc.values,
                        color=vc.values,
                        color_continuous_scale="Blues",
                        labels={"x": "", "y": ""},
                        title=col_name
                    )
                    fig.update_layout(
                        height=240, template=TEMPLATE,
                        margin=dict(t=35, b=20, l=10, r=10),
                        coloraxis_showscale=False,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CORRÉLATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("## 🔗 Corrélations & Relations")

    if len(num_cols) < 2:
        st.info("Au moins 2 colonnes numériques sont nécessaires.")
    else:
        method = st.radio("Méthode de corrélation", ["pearson", "spearman"], horizontal=True)
        corr = df[num_cols].corr(method=method).round(3)

        col1, col2 = st.columns([3, 2])
        with col1:
            fig_corr = go.Figure(go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                text=corr.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 9},
                colorbar=dict(title="r")
            ))
            fig_corr.update_layout(
                title="Matrice de corrélation",
                height=max(420, 40 * len(num_cols)),
                template=TEMPLATE
            )
            st.plotly_chart(fig_corr, use_container_width=True)

        with col2:
            # Top corrélations
            st.markdown("#### Top corrélations")
            mask = np.triu(np.ones(corr.shape, dtype=bool), k=1)
            pairs = (
                corr.where(mask).stack()
                .reset_index()
            )
            pairs.columns = ["Var A", "Var B", "r"]
            pairs["|r|"] = pairs["r"].abs()
            pairs = pairs.sort_values("|r|", ascending=False).head(15)
            pairs["Paire"] = pairs["Var A"] + " × " + pairs["Var B"]

            fig_pairs = px.bar(
                pairs.head(10), x="r", y="Paire",
                orientation="h",
                color="r", color_continuous_scale="RdBu",
                range_color=[-1, 1],
                title="Top 10 corrélations"
            )
            fig_pairs.update_layout(height=420, template=TEMPLATE)
            st.plotly_chart(fig_pairs, use_container_width=True)

        # Scatter interactif
        st.markdown("### 🔵 Scatter plot interactif")
        c1, c2, c3 = st.columns(3)
        x_col = c1.selectbox("Axe X", num_cols, index=0, key="sc_x")
        y_col = c2.selectbox("Axe Y", num_cols, index=min(1, len(num_cols)-1), key="sc_y")
        col_c = c3.selectbox("Couleur", ["(aucune)"] + cat_cols + num_cols, key="sc_c")

        color_arg = None if col_c == "(aucune)" else col_c
        fig_sc = px.scatter(
            df, x=x_col, y=y_col, color=color_arg,
            trendline="ols",
            opacity=0.65,
            color_discrete_sequence=PALETTE,
            title=f"{x_col} vs {y_col}",
            hover_data=df.columns.tolist()[:4]
        )
        fig_sc.update_layout(height=450, template=TEMPLATE)
        st.plotly_chart(fig_sc, use_container_width=True)

        # Pearson stats
        valid = df[[x_col, y_col]].dropna()
        if len(valid) > 2:
            r, p = stats.pearsonr(valid[x_col], valid[y_col])
            rho, p2 = stats.spearmanr(valid[x_col], valid[y_col])
            m1, m2, m3 = st.columns(3)
            m1.metric("Pearson r", f"{r:.4f}", delta=f"p={p:.4f}")
            m2.metric("Spearman ρ", f"{rho:.4f}", delta=f"p={p2:.4f}")
            m3.metric("R²", f"{r**2:.4f}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — KPI & AGRÉGATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 🎯 KPI & Agrégations automatiques")

    if not num_cols:
        st.info("Aucune colonne numérique disponible.")
    else:
        # Auto KPIs
        st.markdown("### 📌 Métriques clés")
        kpi_cols = num_cols[:6]
        ks = st.columns(len(kpi_cols))
        for i, col in enumerate(kpi_cols):
            s = df[col].dropna()
            with ks[i]:
                st.metric(
                    label=col,
                    value=fmt_number(s.sum()),
                    delta=f"moy: {fmt_number(s.mean())}"
                )

        if cat_cols:
            st.markdown("### 📊 Analyse par catégorie")
            c1, c2, c3 = st.columns(3)
            cat_sel = c1.selectbox("Regrouper par", cat_cols, key="kpi_cat")
            val_sel = c2.selectbox("Valeur", num_cols, key="kpi_val")
            agg_sel = c3.selectbox("Agrégation", ["sum", "mean", "count", "median", "max", "min"], key="kpi_agg")
            top_n = st.slider("Top N catégories", 5, 30, 12, key="kpi_n")

            agg_df = (
                df.groupby(cat_sel)[val_sel]
                .agg(agg_sel)
                .sort_values(ascending=False)
                .head(top_n)
                .reset_index()
            )
            agg_df.columns = [cat_sel, "Valeur"]

            col1, col2 = st.columns(2)
            with col1:
                fig_bar = px.bar(
                    agg_df, x=cat_sel, y="Valeur",
                    color="Valeur", color_continuous_scale="Blues",
                    text=agg_df["Valeur"].apply(fmt_number),
                    title=f"{agg_sel.upper()} de {val_sel} par {cat_sel}"
                )
                fig_bar.update_traces(textposition="outside")
                fig_bar.update_layout(height=420, template=TEMPLATE, coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col2:
                fig_pie = px.pie(
                    agg_df, values="Valeur", names=cat_sel,
                    hole=0.45, title="Répartition",
                    color_discrete_sequence=PALETTE
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                fig_pie.update_layout(height=420, template=TEMPLATE)
                st.plotly_chart(fig_pie, use_container_width=True)

            # Treemap
            fig_tree = px.treemap(
                agg_df,
                path=[px.Constant("Total"), cat_sel],
                values="Valeur",
                color="Valeur",
                color_continuous_scale="RdYlGn",
                title=f"Treemap — {val_sel} par {cat_sel}"
            )
            fig_tree.update_traces(textinfo="label+value+percent root")
            fig_tree.update_layout(height=450, template=TEMPLATE)
            st.plotly_chart(fig_tree, use_container_width=True)

            # Waterfall top 8
            wf = agg_df.head(8).copy()
            fig_wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=["relative"] * len(wf) + ["total"],
                x=wf[cat_sel].astype(str).tolist() + ["TOTAL"],
                y=wf["Valeur"].tolist() + [wf["Valeur"].sum()],
                text=[fmt_number(v) for v in wf["Valeur"].tolist() + [wf["Valeur"].sum()]],
                textposition="outside",
                increasing={"marker": {"color": "#27ae60"}},
                decreasing={"marker": {"color": "#c0392b"}},
                totals={"marker": {"color": "#667eea"}}
            ))
            fig_wf.update_layout(
                title=f"Waterfall — {val_sel}",
                height=420, template=TEMPLATE, waterfallgap=0.3
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        # Jauges automatiques
        st.markdown("### 🎯 Jauges KPI")
        gauge_sel = st.multiselect("Colonnes à afficher en jauge", num_cols, default=num_cols[:3], key="gauge_sel")
        if gauge_sel:
            gcols = st.columns(len(gauge_sel))
            for i, col_name in enumerate(gauge_sel):
                s = df[col_name].dropna()
                if len(s) == 0:
                    continue
                mn, mx, mean_, med_ = float(s.min()), float(s.max()), float(s.mean()), float(s.median())
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=round(mean_, 2),
                    delta={"reference": round(med_, 2)},
                    title={"text": col_name, "font": {"size": 13}},
                    gauge={
                        "axis": {"range": [mn, mx]},
                        "bar": {"color": "#667eea"},
                        "steps": [
                            {"range": [mn, mn+(mx-mn)/3], "color": "#fadcdc"},
                            {"range": [mn+(mx-mn)/3, mn+2*(mx-mn)/3], "color": "#fff3cd"},
                            {"range": [mn+2*(mx-mn)/3, mx], "color": "#d4edda"},
                        ]
                    }
                ))
                fig_g.update_layout(height=270, template=TEMPLATE, margin=dict(t=50, b=0))
                with gcols[i]:
                    st.plotly_chart(fig_g, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SÉRIES TEMPORELLES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("## 📅 Séries temporelles")

    # Detect date columns
    detected_dates = []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            detected_dates.append((col, s))
        elif col in cat_cols:
            try:
                parsed = pd.to_datetime(s, infer_datetime_format=True, errors="coerce")
                if parsed.notna().mean() > 0.5:
                    detected_dates.append((col, parsed))
            except Exception:
                pass

    if not detected_dates:
        st.info("🔍 Aucune colonne de date détectée automatiquement.")
        st.markdown("**Conseil :** Assurez-vous que vos dates sont dans un format standard (ex: `2024-01-15`, `15/01/2024`).")
    elif not num_cols:
        st.info("Aucune colonne numérique pour l'axe Y.")
    else:
        date_names = [c for c, _ in detected_dates]
        date_dict = dict(detected_dates)

        c1, c2 = st.columns(2)
        date_col_sel = c1.selectbox("Colonne de date", date_names, key="ts_d")
        y_col_sel = c2.selectbox("Valeur", num_cols, key="ts_y")

        date_series = date_dict[date_col_sel]
        ts_df = pd.DataFrame({"date": date_series, "value": df[y_col_sel]}).dropna().sort_values("date")

        if len(ts_df) < 3:
            st.warning("Pas assez de données valides.")
        else:
            c3, c4 = st.columns(2)
            gran = c3.selectbox("Granularité", ["Original", "Jour", "Semaine", "Mois", "Trimestre", "Année"], key="ts_g")
            agg_t = c4.selectbox("Agrégation", ["sum", "mean", "median", "max", "min"], key="ts_a")

            gran_map = {"Jour": "D", "Semaine": "W", "Mois": "ME", "Trimestre": "QE", "Année": "YE"}
            if gran != "Original":
                ts_df = ts_df.set_index("date")["value"].resample(gran_map[gran]).agg(agg_t).reset_index()
                ts_df.columns = ["date", "value"]
                ts_df = ts_df.dropna()

            # MA
            ma_list = st.multiselect("Moyennes mobiles", [7, 14, 30, 90], default=[], key="ts_ma")

            # Ligne principale
            fig_ts = go.Figure()
            fig_ts.add_trace(go.Scatter(
                x=ts_df["date"], y=ts_df["value"],
                mode="lines", name=y_col_sel,
                line=dict(color="#667eea", width=1.8),
                fill="tozeroy", fillcolor="rgba(102,126,234,0.08)"
            ))
            for ma in ma_list:
                if len(ts_df) > ma:
                    fig_ts.add_trace(go.Scatter(
                        x=ts_df["date"],
                        y=ts_df["value"].rolling(ma).mean(),
                        mode="lines", name=f"MA {ma}",
                        line=dict(width=1.5, dash="dot")
                    ))
            fig_ts.update_layout(
                title=f"Évolution — {y_col_sel}",
                height=420, template=TEMPLATE,
                hovermode="x unified",
                xaxis=dict(
                    rangeslider=dict(visible=True),
                    rangeselector=dict(buttons=[
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1A", step="year", stepmode="backward"),
                        dict(step="all", label="Tout")
                    ])
                )
            )
            st.plotly_chart(fig_ts, use_container_width=True)

            # Stats rapides
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total", fmt_number(ts_df["value"].sum()))
            m2.metric("Moyenne", fmt_number(ts_df["value"].mean()))
            m3.metric("Max", fmt_number(ts_df["value"].max()))
            tendance = "↑ Hausse" if ts_df["value"].iloc[-1] > ts_df["value"].iloc[0] else "↓ Baisse"
            m4.metric("Tendance", tendance)

            # Saisonnalité
            st.markdown("### 📆 Saisonnalité")
            ts_work = ts_df.copy()
            ts_work["month"] = ts_work["date"].dt.month
            ts_work["month_name"] = ts_work["date"].dt.month_name()
            ts_work["weekday"] = ts_work["date"].dt.day_name()
            ts_work["year"] = ts_work["date"].dt.year

            months_order = ["January","February","March","April","May","June",
                            "July","August","September","October","November","December"]
            days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

            sc1, sc2 = st.columns(2)
            with sc1:
                monthly = (ts_work.groupby("month_name")["value"].mean()
                           .reindex(months_order).dropna())
                if not monthly.empty:
                    fig_m = px.bar(
                        x=monthly.index, y=monthly.values,
                        color=monthly.values, color_continuous_scale="Blues",
                        title="Moyenne par mois",
                        labels={"x": "", "y": ""}
                    )
                    fig_m.update_layout(height=320, template=TEMPLATE, coloraxis_showscale=False)
                    st.plotly_chart(fig_m, use_container_width=True)

            with sc2:
                daily = (ts_work.groupby("weekday")["value"].mean()
                         .reindex(days_order).dropna())
                if not daily.empty:
                    fig_d = px.bar(
                        x=daily.index, y=daily.values,
                        color=daily.values, color_continuous_scale="Purples",
                        title="Moyenne par jour de semaine",
                        labels={"x": "", "y": ""}
                    )
                    fig_d.update_layout(height=320, template=TEMPLATE, coloraxis_showscale=False)
                    st.plotly_chart(fig_d, use_container_width=True)

            # Heatmap année × mois
            pivot = ts_work.pivot_table(values="value", index="year", columns="month_name", aggfunc="sum")
            pivot = pivot.reindex(columns=[m for m in months_order if m in pivot.columns])
            if not pivot.empty and len(pivot) > 1:
                fig_heat = px.imshow(
                    pivot, title="Heatmap année × mois",
                    color_continuous_scale="RdYlGn", aspect="auto"
                )
                fig_heat.update_layout(height=max(300, 60*len(pivot)), template=TEMPLATE)
                st.plotly_chart(fig_heat, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — EXPORT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("## 📤 Export des données")

    # Rapport texte auto
    st.markdown("### 📋 Rapport exécutif")
    lines = [
        f"# Rapport d'analyse — {uploaded.name}",
        f"",
        f"## Vue d'ensemble",
        f"- Lignes : {len(df):,}",
        f"- Colonnes : {len(df.columns)}",
        f"- Numériques : {len(num_cols)} — {', '.join(num_cols[:5])}",
        f"- Catégorielles : {len(cat_cols)} — {', '.join(cat_cols[:5])}",
        f"- Valeurs manquantes : {missing_pct}%",
        f"- Doublons : {dupes}",
        f"- Score qualité : {quality_score:.0f}/100",
        f"",
        f"## Statistiques numériques",
        df[num_cols].describe().round(3).to_string() if num_cols else "—",
        f"",
        f"## Insights",
    ]
    for icon, msg in insights[:8]:
        lines.append(f"- {msg}")

    rapport = "\n".join(lines)
    st.text_area("Rapport", rapport, height=300)

    # Téléchargements
    st.markdown("### ⬇️ Téléchargements")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ CSV original", csv_bytes, f"{uploaded.name.split('.')[0]}.csv", "text/csv")

    with col2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="Data")
        st.download_button("⬇️ Excel original", buf.getvalue(),
                           f"{uploaded.name.split('.')[0]}_export.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with col3:
        st.download_button("⬇️ Rapport .md", rapport.encode("utf-8"),
                           f"rapport_{uploaded.name.split('.')[0]}.md", "text/markdown")

    # Nettoyage rapide
    st.markdown("### 🔧 Données nettoyées")
    clean = df.copy()
    c1, c2 = st.columns(2)
    if c1.checkbox("Supprimer doublons"):
        clean = clean.drop_duplicates()
        c1.caption(f"→ {len(df) - len(clean)} doublons supprimés")
    fill_strategy = c2.selectbox("Imputation numériques",
                                 ["Ne rien faire", "Moyenne", "Médiane", "0"])
    if fill_strategy != "Ne rien faire" and num_cols:
        nc = clean.select_dtypes(include=np.number).columns
        if fill_strategy == "Moyenne":
            clean[nc] = clean[nc].fillna(clean[nc].mean())
        elif fill_strategy == "Médiane":
            clean[nc] = clean[nc].fillna(clean[nc].median())
        else:
            clean[nc] = clean[nc].fillna(0)

    st.markdown(f"Dataset nettoyé : **{len(clean):,} lignes × {len(clean.columns)} colonnes**")
    buf2 = io.BytesIO()
    with pd.ExcelWriter(buf2, engine="openpyxl") as w:
        clean.to_excel(w, index=False)
    st.download_button("⬇️ Télécharger données nettoyées (Excel)", buf2.getvalue(),
                       "data_cleaned.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

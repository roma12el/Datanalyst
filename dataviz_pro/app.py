import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Dashboard Auto",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --red: #E8002D;
    --dark: #09090B;
    --gray-50: #FAFAFA;
    --gray-100: #F4F4F5;
    --gray-200: #E4E4E7;
    --gray-400: #A1A1AA;
    --gray-600: #52525B;
    --green: #16A34A;
    --orange: #EA580C;
}

*, body { font-family: 'Inter', sans-serif !important; }
[data-testid="stAppViewContainer"] { background: var(--gray-50) !important; }
.main .block-container { padding: 1.5rem 2rem 3rem !important; max-width: 1600px !important; }

/* Upload zone */
.upload-hero {
    background: white;
    border: 2px dashed var(--gray-200);
    border-radius: 16px;
    padding: 4rem 2rem;
    text-align: center;
    margin: 3rem auto;
    max-width: 600px;
    transition: border-color 0.2s;
}
.upload-hero:hover { border-color: var(--red); }

/* Cards */
.card {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    height: 100%;
}
.card-red { border-top: 3px solid var(--red); }
.card-green { border-top: 3px solid var(--green); }
.card-orange { border-top: 3px solid var(--orange); }

.kpi-val {
    font-size: 2rem;
    font-weight: 800;
    color: var(--dark);
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.kpi-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--gray-400);
    margin-bottom: 4px;
}
.kpi-sub { font-size: 0.72rem; color: var(--gray-400); margin-top: 3px; }

/* Section */
.sec {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--gray-400);
    margin: 2rem 0 1rem;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--gray-200);
}

/* Insight */
.insight {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    background: white;
    border: 1px solid var(--gray-200);
    border-left: 3px solid var(--red);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.82rem;
    color: var(--gray-600);
}
.insight-ok { border-left-color: var(--green); }
.insight-warn { border-left-color: var(--orange); }

/* Dashboard title */
.dash-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--dark);
    letter-spacing: -0.02em;
    margin: 0;
}
.dash-title span { color: var(--red); }
.dash-sub { font-size: 0.8rem; color: var(--gray-400); margin: 4px 0 1.5rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--gray-100) !important;
    border-radius: 8px !important;
    padding: 3px !important;
    border: none !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--gray-400) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 7px 14px !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: var(--red) !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08) !important;
}

[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }

hr { border: none !important; border-top: 1px solid var(--gray-200) !important; margin: 1rem 0 !important; }

.stDownloadButton > button {
    background: var(--dark) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--gray-200) !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fmt(val):
    if pd.isna(val): return "—"
    if abs(val) >= 1e9: return f"{val/1e9:.1f}B"
    if abs(val) >= 1e6: return f"{val/1e6:.1f}M"
    if abs(val) >= 1e3: return f"{val/1e3:.1f}K"
    if isinstance(val, float): return f"{val:.2f}"
    return str(val)


def chart_layout(fig, height=320):
    fig.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter", size=11, color="#52525B"),
        margin=dict(t=30, b=30, l=40, r=20),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E4E7", font_family="Inter", font_size=11),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#F4F4F5", linecolor="#E4E4E7", tickfont=dict(size=10))
    fig.update_yaxes(gridcolor="#F4F4F5", linecolor="#E4E4E7", tickfont=dict(size=10))
    return fig


RED = "#E8002D"
DARK = "#09090B"
GREEN = "#16A34A"
ORANGE = "#EA580C"
PALETTE = [RED, "#374151", "#6B7280", "#9CA3AF", "#D1D5DB"]


def auto_detect(df):
    """Auto-detect column roles from data."""
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Detect date columns
    date_cols = list(df.select_dtypes(include=["datetime"]).columns)
    for c in cat_cols:
        try:
            parsed = pd.to_datetime(df[c], infer_datetime_format=True, errors="coerce")
            if parsed.notna().sum() / len(df) > 0.7:
                date_cols.append(c)
        except: pass

    # Best numeric = highest variance (most interesting)
    best_num = None
    if num_cols:
        cvs = {c: df[c].std() / abs(df[c].mean()) if df[c].mean() != 0 else 0 for c in num_cols}
        best_num = max(cvs, key=cvs.get)

    # Best categorical = medium cardinality (most useful for grouping)
    best_cat = None
    if cat_cols:
        scored = {}
        for c in cat_cols:
            if c in date_cols: continue
            n = df[c].nunique()
            if 2 <= n <= 30:
                scored[c] = n
        if scored:
            best_cat = sorted(scored, key=lambda c: abs(scored[c] - 8))[0]
        elif cat_cols:
            best_cat = [c for c in cat_cols if c not in date_cols][0] if [c for c in cat_cols if c not in date_cols] else None

    # Best date
    best_date = date_cols[0] if date_cols else None

    return {
        "num_cols": num_cols,
        "cat_cols": [c for c in cat_cols if c not in date_cols],
        "date_cols": date_cols,
        "best_num": best_num,
        "best_cat": best_cat,
        "best_date": best_date,
    }


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD SCREEN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem">
    <div>
        <div class="dash-title">Dashboard <span>Auto</span></div>
        <div class="dash-sub">Chargez n'importe quelle base de données → tableau de bord instantané</div>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "📂 Charger votre fichier (Excel, CSV, TSV)",
    type=["xlsx", "xls", "csv", "tsv"],
    label_visibility="collapsed"
)

if not uploaded:
    st.markdown("""
    <div class="upload-hero">
        <div style="font-size:3rem;margin-bottom:1rem">📊</div>
        <div style="font-size:1.3rem;font-weight:700;color:#09090B;margin-bottom:8px">
            Déposez votre fichier ici
        </div>
        <div style="font-size:0.85rem;color:#A1A1AA;line-height:1.6">
            Excel (.xlsx / .xls) · CSV · TSV<br>
            Le tableau de bord se génère <strong>automatiquement</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load(file_bytes, name):
    try:
        n = name.lower()
        if n.endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(file_bytes)
            df = pd.read_excel(file_bytes, sheet_name=xls.sheet_names[0])
        elif n.endswith(".csv"):
            import io
            raw = file_bytes.read() if hasattr(file_bytes, 'read') else file_bytes
            sample = raw[:2048].decode("utf-8", errors="replace")
            sep = ";" if sample.count(";") > sample.count(",") else ","
            df = pd.read_csv(io.BytesIO(raw) if isinstance(raw, bytes) else file_bytes, sep=sep, on_bad_lines="skip")
        elif n.endswith(".tsv"):
            df = pd.read_csv(file_bytes, sep="\t", on_bad_lines="skip")
        else:
            return None
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return None


file_bytes = uploaded.read()
uploaded.seek(0)

df = load(uploaded, uploaded.name)

if df is None or df.empty:
    st.error("❌ Impossible de lire ce fichier.")
    st.stop()

meta = auto_detect(df)
num_cols = meta["num_cols"]
cat_cols = meta["cat_cols"]
date_cols = meta["date_cols"]
best_num = meta["best_num"]
best_cat = meta["best_cat"]
best_date = meta["best_date"]

n_rows, n_cols = df.shape
missing_pct = round(100 * df.isnull().sum().sum() / (n_rows * n_cols), 1)
duplicates = int(df.duplicated().sum())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — EN-TÊTE & KPIs
# ─────────────────────────────────────────────────────────────────────────────

fname = uploaded.name
st.markdown(f"""
<div style="background:white;border:1px solid #E4E4E7;border-radius:12px;
            padding:1.2rem 1.6rem;margin-bottom:1.5rem;
            display:flex;justify-content:space-between;align-items:center">
    <div>
        <div style="font-weight:700;font-size:1rem;color:#09090B">📁 {fname}</div>
        <div style="font-size:0.75rem;color:#A1A1AA;margin-top:2px">
            {n_rows:,} lignes · {n_cols} colonnes · {len(num_cols)} numériques · {len(cat_cols)} catégorielles
            {'· ' + str(len(date_cols)) + ' dates' if date_cols else ''}
        </div>
    </div>
    <div style="font-size:0.72rem;color:#A1A1AA">Dashboard généré automatiquement</div>
</div>
""", unsafe_allow_html=True)

# KPI strip — top numériques
if num_cols:
    cols_to_show = num_cols[:5]
    kpi_cols = st.columns(len(cols_to_show) + 1)

    for i, col in enumerate(cols_to_show):
        s = df[col].dropna()
        total = s.sum()
        mean = s.mean()
        with kpi_cols[i]:
            st.markdown(f"""
            <div class="card card-red">
                <div class="kpi-label">{col[:20]}</div>
                <div class="kpi-val">{fmt(total)}</div>
                <div class="kpi-sub">Moy. {fmt(mean)} · {len(s):,} valeurs</div>
            </div>""", unsafe_allow_html=True)

    # Qualité données
    health = max(0, 100 - missing_pct * 2 - (duplicates / n_rows * 20 if n_rows > 0 else 0))
    health_color = "green" if health >= 80 else ("orange" if health >= 50 else "red")
    with kpi_cols[-1]:
        st.markdown(f"""
        <div class="card card-{'green' if health >= 80 else 'orange' if health >= 50 else 'red'}">
            <div class="kpi-label">Qualité données</div>
            <div class="kpi-val" style="color:{'#16A34A' if health >= 80 else '#EA580C' if health >= 50 else '#E8002D'}">{round(health)}/100</div>
            <div class="kpi-sub">{missing_pct}% manquant · {duplicates} doublons</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — GRAPHIQUES AUTOMATIQUES
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="sec">Visualisations automatiques</div>', unsafe_allow_html=True)

# Row 1 : distribution principale + top catégories
col_a, col_b = st.columns(2)

with col_a:
    if best_num:
        s = df[best_num].dropna()
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=s, nbinsx=30,
            marker_color=RED, marker_line_color="white",
            marker_line_width=0.5, opacity=0.85,
        ))
        # médiane
        fig.add_vline(x=s.median(), line_dash="dash", line_color=DARK, line_width=1.5,
                      annotation_text=f"Médiane {fmt(s.median())}",
                      annotation_font=dict(size=10))
        chart_layout(fig, 300)
        fig.update_layout(title=dict(text=f"Distribution — {best_num}", font=dict(size=12, color=DARK)))
        st.plotly_chart(fig, use_container_width=True)
    elif cat_cols:
        vc = df[cat_cols[0]].value_counts().head(10)
        fig = go.Figure(go.Bar(
            x=vc.index.astype(str), y=vc.values,
            marker_color=[RED] + [PALETTE[2]] * (len(vc)-1),
            marker_line_width=0
        ))
        chart_layout(fig, 300)
        fig.update_layout(title=dict(text=f"Fréquences — {cat_cols[0]}", font=dict(size=12)))
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    if best_cat:
        vc = df[best_cat].value_counts().head(10)
        fig = go.Figure(go.Bar(
            y=vc.index.astype(str), x=vc.values,
            orientation="h",
            marker_color=[RED] + ["#E4E4E7"] * (len(vc)-1),
            marker_line_width=0,
            text=[f"{v:,}" for v in vc.values],
            textposition="outside",
            textfont=dict(size=10)
        ))
        chart_layout(fig, 300)
        fig.update_layout(
            title=dict(text=f"Top catégories — {best_cat}", font=dict(size=12)),
            xaxis=dict(visible=False)
        )
        st.plotly_chart(fig, use_container_width=True)
    elif len(num_cols) >= 2:
        fig = px.scatter(
            df.sample(min(500, len(df))),
            x=num_cols[0], y=num_cols[1],
            color_discrete_sequence=[RED], opacity=0.6
        )
        chart_layout(fig, 300)
        fig.update_layout(title=dict(text=f"{num_cols[0]} vs {num_cols[1]}", font=dict(size=12)))
        st.plotly_chart(fig, use_container_width=True)

# Row 2 : série temporelle OU corrélations + donut
col_c, col_d = st.columns([3, 2])

with col_c:
    if best_date and best_num:
        # Time series
        try:
            ts = df[[best_date, best_num]].copy()
            ts[best_date] = pd.to_datetime(ts[best_date], errors="coerce")
            ts = ts.dropna().sort_values(best_date)
            # Aggregate by month if many points
            if len(ts) > 200:
                ts = ts.set_index(best_date)[best_num].resample("ME").sum().reset_index()
                ts.columns = [best_date, best_num]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts[best_date], y=ts[best_num],
                mode="lines+markers",
                line=dict(color=RED, width=2),
                marker=dict(size=4, color=RED),
                fill="tozeroy", fillcolor="rgba(232,0,45,0.06)"
            ))
            chart_layout(fig, 280)
            fig.update_layout(title=dict(text=f"Évolution — {best_num}", font=dict(size=12)))
            st.plotly_chart(fig, use_container_width=True)
        except:
            pass
    elif len(num_cols) >= 3:
        # Correlation heatmap
        corr = df[num_cols[:8]].corr().round(2)
        fig = go.Figure(go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(), y=corr.index.tolist(),
            colorscale=[[0, "#1E40AF"], [0.5, "white"], [1, RED]],
            zmid=0, zmin=-1, zmax=1,
            text=corr.values, texttemplate="%{text:.2f}",
            textfont={"size": 9},
            colorbar=dict(thickness=8, len=0.8)
        ))
        chart_layout(fig, 280)
        fig.update_layout(title=dict(text="Corrélations", font=dict(size=12)))
        st.plotly_chart(fig, use_container_width=True)

with col_d:
    if best_cat and best_num:
        # Aggregation by best category
        top_cats = df[best_cat].value_counts().head(7).index
        agg = df[df[best_cat].isin(top_cats)].groupby(best_cat)[best_num].sum().sort_values(ascending=False).reset_index()
        n = len(agg)
        shades = [f"rgba(232,0,45,{max(0.15, 1 - i*0.7/max(n-1,1)):.2f})" for i in range(n)]

        fig = go.Figure(go.Pie(
            values=agg[best_num],
            labels=agg[best_cat].astype(str),
            hole=0.55,
            marker=dict(colors=shades, line=dict(color="white", width=2)),
            textfont=dict(family="Inter", size=10),
        ))
        total = agg[best_num].sum()
        fig.add_annotation(
            text=f"<b>{fmt(total)}</b>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, family="Inter", color=DARK)
        )
        chart_layout(fig, 280)
        fig.update_layout(
            title=dict(text=f"{best_num} par {best_cat}", font=dict(size=12)),
            showlegend=True,
            legend=dict(font=dict(size=9), x=1, y=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)
    elif best_cat:
        vc = df[best_cat].value_counts().head(6)
        n = len(vc)
        shades = [f"rgba(232,0,45,{max(0.15, 1 - i*0.7/max(n-1,1)):.2f})" for i in range(n)]
        fig = go.Figure(go.Pie(
            values=vc.values, labels=vc.index.astype(str), hole=0.5,
            marker=dict(colors=shades, line=dict(color="white", width=2)),
            textfont=dict(size=10)
        ))
        chart_layout(fig, 280)
        fig.update_layout(title=dict(text=f"Répartition — {best_cat}", font=dict(size=12)), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

# Row 3 : boxplots multi-colonnes si disponible
if len(num_cols) >= 2 and best_cat:
    st.markdown('<div class="sec">Comparaison par groupe</div>', unsafe_allow_html=True)
    top_cats = df[best_cat].value_counts().head(8).index
    filtered = df[df[best_cat].isin(top_cats)]

    show_cols = num_cols[:3]
    box_cols = st.columns(len(show_cols))
    for i, col in enumerate(show_cols):
        with box_cols[i]:
            fig = px.box(
                filtered, x=best_cat, y=col,
                color=best_cat,
                color_discrete_sequence=[RED, "#374151", "#6B7280", "#9CA3AF", "#D1D5DB", "#E5E7EB", "#F3F4F6", "#F9FAFB"],
                points=False
            )
            chart_layout(fig, 260)
            fig.update_layout(
                title=dict(text=col, font=dict(size=11)),
                xaxis=dict(tickangle=-30, tickfont=dict(size=9)),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

elif len(num_cols) >= 2:
    # Scatter matrix si pas de catégorielle
    st.markdown('<div class="sec">Relations entre variables numériques</div>', unsafe_allow_html=True)
    cols_sm = num_cols[:4]
    fig = px.scatter_matrix(df.sample(min(300, len(df))), dimensions=cols_sm,
                            color_discrete_sequence=[RED], opacity=0.5)
    fig.update_traces(diagonal_visible=False, showupperhalf=False, marker=dict(size=3))
    chart_layout(fig, 450)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — INSIGHTS AUTOMATIQUES
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="sec">Insights clés — ce que vos données révèlent</div>', unsafe_allow_html=True)

insights = []

# Manquants
if missing_pct == 0:
    insights.append(("ok", "✅ Données complètes — aucune valeur manquante."))
elif missing_pct > 20:
    insights.append(("bad", f"🚨 {missing_pct}% de valeurs manquantes — fiabilité compromise. Nettoyage requis avant toute décision."))
else:
    insights.append(("warn", f"⚠️ {missing_pct}% de valeurs manquantes — à traiter."))

# Doublons
if duplicates > 0:
    pct_dup = round(100 * duplicates / n_rows, 1)
    insights.append(("warn", f"⚠️ {duplicates} lignes dupliquées ({pct_dup}%) — risque de double comptage."))

# Outliers
for col in num_cols[:5]:
    s = df[col].dropna()
    if len(s) < 4: continue
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    out = s[(s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)]
    pct = round(100 * len(out) / len(s), 1)
    if pct > 5:
        insights.append(("warn", f"⚠️ <strong>{col}</strong> : {len(out)} valeurs aberrantes ({pct}%) — vérifier si erreurs de saisie."))

# Asymétrie
for col in num_cols[:5]:
    s = df[col].dropna()
    skew = s.skew()
    if abs(skew) > 2:
        insights.append(("warn", f"📐 <strong>{col}</strong> : distribution très asymétrique (skew={skew:.1f}) — préférez la médiane ({fmt(s.median())}) à la moyenne ({fmt(s.mean())})."))

# Corrélations fortes
if len(num_cols) >= 2:
    corr = df[num_cols].corr()
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    for (a, b), r in pairs[pairs.abs() >= 0.75].items():
        direction = "positivement" if r > 0 else "négativement"
        insights.append(("warn", f"🔗 <strong>{a}</strong> et <strong>{b}</strong> sont fortement liées {direction} (r={r:.2f})."))

# Concentration catégorielle
if best_cat:
    vc = df[best_cat].value_counts()
    top_pct = round(100 * vc.iloc[0] / df[best_cat].count(), 1)
    if top_pct > 60:
        insights.append(("warn", f"⚠️ <strong>{best_cat}</strong> : \"{vc.index[0]}\" concentre {top_pct}% des données."))

# Tendance temporelle
if best_date and best_num:
    try:
        ts = df[[best_date, best_num]].copy()
        ts[best_date] = pd.to_datetime(ts[best_date], errors="coerce")
        ts = ts.dropna().sort_values(best_date)
        if len(ts) > 3:
            first_half = ts["value"].mean() if "value" in ts else ts[best_num].head(len(ts)//2).mean()
            second_half = ts[best_num].tail(len(ts)//2).mean()
            change = round((second_half - first_half) / abs(first_half) * 100, 1) if first_half != 0 else 0
            if change > 10:
                insights.append(("ok", f"📈 <strong>{best_num}</strong> : tendance haussière (+{change}% entre première et deuxième moitié de période)."))
            elif change < -10:
                insights.append(("bad", f"📉 <strong>{best_num}</strong> : tendance baissière ({change}% entre première et deuxième moitié de période)."))
    except: pass

# Affichage en 2 colonnes
if insights:
    left, right = st.columns(2)
    for i, (kind, msg) in enumerate(insights[:10]):
        cls = "insight-ok" if kind == "ok" else ("insight-warn" if kind == "warn" else "")
        target = left if i % 2 == 0 else right
        target.markdown(f'<div class="insight {cls}">{msg}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — DONNÉES BRUTES & EXPORT
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="sec">Données & Export</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍  Aperçu des données", "⬇️  Télécharger"])

with tab1:
    st.dataframe(df.head(50), use_container_width=True, height=320)

with tab2:
    import io

    c1, c2 = st.columns(2)
    with c1:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False)
        st.download_button("⬇️  Excel complet", buf.getvalue(),
                           f"{uploaded.name.split('.')[0]}_export.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button("⬇️  CSV complet", df.to_csv(index=False).encode("utf-8"),
                           f"{uploaded.name.split('.')[0]}_export.csv", "text/csv")

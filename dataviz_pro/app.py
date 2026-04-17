import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io, warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Power BI Dashboard", page_icon="📊", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container{padding:0.6rem 1rem 1rem 1rem !important}
    .stApp > header{display:none}
    #MainMenu{visibility:hidden}
    footer{visibility:hidden}

    .pbi-header{
        background:#2B579A;color:#fff;
        padding:10px 18px;border-radius:6px;
        display:flex;align-items:center;justify-content:space-between;
        margin-bottom:12px;
    }
    .pbi-header h1{font-size:16px;font-weight:600;margin:0;color:#fff}
    .pbi-header span{font-size:12px;opacity:.8}

    .kpi-card{
        background:#fff;border:1px solid #e0e0e0;border-radius:4px;
        padding:12px 14px;text-align:left;
    }
    .kpi-label{font-size:11px;color:#666;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
    .kpi-value{font-size:28px;font-weight:700;color:#1a1a1a;line-height:1.1}
    .kpi-delta{font-size:11px;margin-top:3px}
    .delta-up{color:#107C10} .delta-down{color:#d13438}

    div[data-testid="column"]{gap:0 !important}
    .stSelectbox label{font-size:11px !important;color:#555 !important}
    .stSelectbox > div > div{font-size:12px !important}

    .chart-title{font-size:11px;font-weight:600;color:#333;text-transform:uppercase;
                 letter-spacing:.4px;margin-bottom:0px}
    .chart-sub{font-size:10px;color:#888;margin-bottom:4px}

    div[data-testid="stVerticalBlock"] > div{gap:0}
</style>
""", unsafe_allow_html=True)

STAGE_COLORS  = ["#2B579A","#1D9E75","#D4537E","#BA7517","#E24B4A"]
SIZE_COLORS   = ["#7F77DD","#1D9E75","#D85A30"]
REG_COLORS    = ["#2B579A","#1D9E75","#D4537E","#BA7517","#534AB7","#0F6E56"]
PARTNER_COLORS= ["#2B579A","#1D9E75"]
T = "plotly_white"
PLOT_CFG = dict(displayModeBar=False)

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# ── HELPERS ──────────────────────────────────────────────────────────────────
def fmt(v):
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.1f}M"
    if v >= 1e3:  return f"${v/1e3:.0f}K"
    return f"${v:.0f}"

def small_layout(fig, h=210):
    fig.update_layout(
        height=h, template=T, margin=dict(t=8,b=8,l=8,r=8),
        font=dict(size=10),
        legend=dict(font=dict(size=9), orientation="h",
                    yanchor="bottom", y=1.01, xanchor="left", x=0)
    )
    return fig

def load_file(f):
    name = f.name.lower()
    try:
        if name.endswith((".xlsx",".xls")):
            xl = pd.ExcelFile(f)
            sheet = xl.sheet_names[0]
            if len(xl.sheet_names) > 1:
                sheet = st.sidebar.selectbox("Feuille Excel", xl.sheet_names)
            df = pd.read_excel(f, sheet_name=sheet)
        elif name.endswith(".csv"):
            raw = f.read(4096).decode("utf-8", errors="replace"); f.seek(0)
            sep = ";" if raw.count(";") > raw.count(",") else ","
            df = pd.read_csv(f, sep=sep, on_bad_lines="skip")
        elif name.endswith(".tsv"):
            df = pd.read_csv(f, sep="\t", on_bad_lines="skip")
        else:
            return None, None, "Format non supporté"
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all").reset_index(drop=True)
        return df, xl.sheet_names if name.endswith((".xlsx",".xls")) else ["CSV"], None
    except Exception as e:
        return None, None, str(e)

def detect_col_types(df):
    num_cols, cat_cols, date_cols = [], [], []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            num_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(s):
            date_cols.append(col)
        else:
            try:
                p = pd.to_datetime(s, infer_datetime_format=True, errors="coerce")
                if p.notna().mean() > 0.6:
                    date_cols.append(col); continue
            except: pass
            cat_cols.append(col)
    return num_cols, cat_cols, date_cols

def demo_data():
    np.random.seed(42)
    STAGES   = ["Lead","Qualify","Solution","Proposal","Finalize"]
    REGIONS  = ["East","West","Central","North"]
    SIZES    = ["Small","Medium","Large"]
    PARTNERS = ["Yes","No"]
    rows = []
    for yr in [2022,2023,2024]:
        for m in range(12):
            for _ in range(np.random.randint(12,22)):
                stage   = np.random.choice(STAGES)
                size    = np.random.choice(SIZES)
                region  = np.random.choice(REGIONS)
                partner = np.random.choice(PARTNERS)
                base = {"Small":np.random.uniform(0.3,1.5),
                        "Medium":np.random.uniform(1.5,5),
                        "Large":np.random.uniform(5,15)}[size]
                fact = {"Lead":.10,"Qualify":.20,"Solution":.35,
                        "Proposal":.60,"Finalize":.90}[stage]
                rows.append(dict(
                    SalesStage=stage, OpportunitySize=size,
                    Region=region, PartnerDriven=partner,
                    Year=yr, Month=m,
                    Revenue=round(base,2),
                    FactoredRevenue=round(base*fact,2),
                    Count=1
                ))
    return pd.DataFrame(rows)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Power BI Dashboard")
    st.divider()
    uploaded = st.file_uploader("Charger votre fichier", type=["xlsx","xls","csv","tsv"])
    st.divider()

    if uploaded:
        df_raw, sheets, err = load_file(uploaded)
        if err:
            st.error(err); df_raw = None
        else:
            st.success(f"✅ {uploaded.name}\n{len(df_raw):,} lignes × {len(df_raw.columns)} colonnes")
    else:
        df_raw = None

    st.markdown("### ⚙️ Configuration des colonnes")
    if df_raw is not None:
        num_cols, cat_cols, date_cols = detect_col_types(df_raw)
        all_cols = df_raw.columns.tolist()

        st.markdown("**Dimensions (catégorielles)**")
        dim_stage   = st.selectbox("Étape / Stage",   ["(aucune)"]+cat_cols, key="d_stage")
        dim_region  = st.selectbox("Région / Zone",   ["(aucune)"]+cat_cols, key="d_region")
        dim_size    = st.selectbox("Taille / Segment",["(aucune)"]+cat_cols, key="d_size")
        dim_partner = st.selectbox("Partenaire / Axe",["(aucune)"]+cat_cols, key="d_partner")

        st.markdown("**Mesures (numériques)**")
        mes_revenue  = st.selectbox("Chiffre d'affaires", ["(aucune)"]+num_cols, key="m_rev")
        mes_factored = st.selectbox("CA Factorisé",       ["(aucune)"]+num_cols, key="m_fact")
        mes_count    = st.selectbox("Quantité / Comptage",["(auto)"]+num_cols, key="m_count")

        st.markdown("**Temporel**")
        dim_date = st.selectbox("Date / Période", ["(aucune)"]+date_cols+cat_cols+num_cols, key="d_date")

        use_demo = False
    else:
        use_demo = True
        num_cols, cat_cols, date_cols = [], [], []
        st.info("Aucun fichier chargé — données de démonstration actives.")
        dim_stage=dim_region=dim_size=dim_partner="(aucune)"
        mes_revenue=mes_factored=mes_count=dim_date="(aucune)"

    st.divider()
    st.caption("v3.0 — Power BI Style")

# ── PREPARE DATA ──────────────────────────────────────────────────────────────
if use_demo:
    df = demo_data()
    col_stage="SalesStage"; col_region="Region"; col_size="OpportunitySize"
    col_partner="PartnerDriven"; col_rev="Revenue"; col_fact="FactoredRevenue"
    col_count=None; col_date="Month"; col_year="Year"
    stages  = sorted(df[col_stage].dropna().unique())
    regions = sorted(df[col_region].dropna().unique())
    sizes   = sorted(df[col_size].dropna().unique())
    partners= sorted(df[col_partner].dropna().unique())
    years   = sorted(df[col_year].dropna().unique())
    has_date=True; has_year=True
else:
    df = df_raw.copy()
    col_stage   = dim_stage   if dim_stage   != "(aucune)" else None
    col_region  = dim_region  if dim_region  != "(aucune)" else None
    col_size    = dim_size    if dim_size    != "(aucune)" else None
    col_partner = dim_partner if dim_partner != "(aucune)" else None
    col_rev     = mes_revenue  if mes_revenue  != "(aucune)" else None
    col_fact    = mes_factored if mes_factored != "(aucune)" else None
    col_count   = mes_count    if mes_count    not in ("(auto)","(aucune)") else None
    col_date    = dim_date    if dim_date    != "(aucune)" else None
    col_year    = None

    def uniq(c): return sorted(df[c].dropna().unique().tolist()) if c else []
    stages=uniq(col_stage); regions=uniq(col_region)
    sizes=uniq(col_size);   partners=uniq(col_partner)
    years=[]
    has_date = col_date is not None
    has_year = False

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pbi-header">
  <h1>📊 Sales Performance Dashboard</h1>
  <span id="ts">Auto-actualisé à chaque filtre</span>
</div>
""", unsafe_allow_html=True)

# ── FILTERS ROW ───────────────────────────────────────────────────────────────
fc = st.columns([1,1,1,1,1,0.6])
f_stage   = fc[0].selectbox("Stage",   ["Tous"]+list(stages),   key="fs") if col_stage  else None
f_region  = fc[1].selectbox("Région",  ["Tous"]+list(regions),  key="fr") if col_region else None
f_size    = fc[2].selectbox("Taille",  ["Tous"]+list(sizes),    key="fz") if col_size   else None
f_partner = fc[3].selectbox("Partner", ["Tous"]+list(partners), key="fp") if col_partner else None
f_year    = fc[4].selectbox("Année",   ["Toutes"]+[str(y) for y in years], key="fy") if years else None
if fc[5].button("↺ Reset", use_container_width=True):
    for k in ["fs","fr","fz","fp","fy"]:
        if k in st.session_state: del st.session_state[k]
    st.rerun()

# ── APPLY FILTERS ─────────────────────────────────────────────────────────────
fdf = df.copy()
if col_stage  and f_stage  and f_stage  != "Tous":    fdf = fdf[fdf[col_stage]  == f_stage]
if col_region and f_region and f_region != "Tous":    fdf = fdf[fdf[col_region] == f_region]
if col_size   and f_size   and f_size   != "Tous":    fdf = fdf[fdf[col_size]   == f_size]
if col_partner and f_partner and f_partner != "Tous": fdf = fdf[fdf[col_partner]== f_partner]
if col_year and f_year and f_year != "Toutes":        fdf = fdf[fdf[col_year].astype(str) == f_year]

n = len(fdf)
total_rev  = fdf[col_rev].sum()   if col_rev   else 0
total_fact = fdf[col_fact].sum()  if col_fact  else 0
avg_rev    = total_rev / max(n,1)
win_count  = fdf[fdf[col_stage]=="Finalize"].shape[0] if col_stage else 0
win_rate   = round(100*win_count/max(n,1))

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5 = st.columns(5)
def kpi(col, label, val, delta, cls):
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{val}</div>
      <div class="kpi-delta {cls}">{delta}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1,"Opportunity count",f"{n:,}","Total enregistrements","delta-up")
kpi(k2,"Total revenue",    fmt(total_rev) if col_rev else "—","Chiffre d'affaires","delta-up")
kpi(k3,"Avg revenue / opp",fmt(avg_rev)  if col_rev else "—","Moyenne par opportunité","delta-up")
kpi(k4,"Factored revenue", fmt(total_fact)if col_fact else "—","CA pondéré par stage","delta-up")
kpi(k5,"Win rate",         f"{win_rate}%" if col_stage else "—","% Finalize / Total","delta-up" if win_rate>30 else "delta-down")

st.markdown("<div style='margin:6px 0'></div>", unsafe_allow_html=True)

# ── ROW 2 — 4 CHARTS ─────────────────────────────────────────────────────────
r2a, r2b, r2c, r2d = st.columns([2,2,1.5,1.5])

# Chart 1: Stacked % by period × stage
with r2a:
    st.markdown('<div class="chart-title">Opportunity count — par période & stage</div>', unsafe_allow_html=True)
    if col_stage and col_date and n > 0:
        if use_demo:
            fdf["_period"] = fdf["Month"].apply(lambda x: MONTHS[int(x)] if pd.notna(x) else "?")
            period_order = MONTHS
        else:
            try:
                fdf["_period"] = pd.to_datetime(fdf[col_date], infer_datetime_format=True, errors="coerce").dt.strftime("%b %Y")
            except:
                fdf["_period"] = fdf[col_date].astype(str)
            period_order = sorted(fdf["_period"].dropna().unique())[:24]

        piv = fdf.groupby(["_period", col_stage]).size().reset_index(name="cnt")
        totals = piv.groupby("_period")["cnt"].transform("sum")
        piv["pct"] = (100 * piv["cnt"] / totals.replace(0,1)).round(1)

        fig = go.Figure()
        for i, st_val in enumerate(stages[:8]):
            sub = piv[piv[col_stage]==st_val]
            sub = sub.set_index("_period").reindex(period_order).fillna(0).reset_index()
            fig.add_trace(go.Bar(
                name=st_val, x=sub["_period"], y=sub["pct"],
                marker_color=STAGE_COLORS[i % len(STAGE_COLORS)],
            ))
        fig.update_layout(
            barmode="stack",
            xaxis=dict(tickfont=dict(size=8), tickangle=-45),
            yaxis=dict(ticksuffix="%", tickfont=dict(size=9)),
            legend=dict(font=dict(size=8), orientation="h", y=1.08),
            **dict(height=220, template=T, margin=dict(t=25,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Stage + Date dans la sidebar")

# Chart 2: Region × size grouped horizontal
with r2b:
    st.markdown('<div class="chart-title">Opportunity count — région & taille</div>', unsafe_allow_html=True)
    if col_region and col_size and n > 0:
        grp = fdf.groupby([col_region, col_size]).size().reset_index(name="cnt")
        fig = go.Figure()
        for i, sz in enumerate(sizes[:6]):
            sub = grp[grp[col_size]==sz]
            fig.add_trace(go.Bar(
                name=sz, y=sub[col_region], x=sub["cnt"],
                orientation="h",
                marker_color=SIZE_COLORS[i % len(SIZE_COLORS)],
            ))
        fig.update_layout(
            barmode="group",
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            legend=dict(font=dict(size=8), orientation="h", y=1.08),
            **dict(height=220, template=T, margin=dict(t=25,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Région + Taille dans la sidebar")

# Chart 3: Stage × partner stacked %
with r2c:
    st.markdown('<div class="chart-title">Count par stage — partner</div>', unsafe_allow_html=True)
    if col_stage and col_partner and n > 0:
        grp = fdf.groupby([col_stage, col_partner]).size().reset_index(name="cnt")
        tot = grp.groupby(col_stage)["cnt"].transform("sum")
        grp["pct"] = (100 * grp["cnt"] / tot.replace(0,1)).round(1)
        fig = go.Figure()
        for i, pv in enumerate(partners[:4]):
            sub = grp[grp[col_partner]==pv]
            fig.add_trace(go.Bar(
                name=str(pv), x=sub[col_stage], y=sub["pct"],
                marker_color=PARTNER_COLORS[i % len(PARTNER_COLORS)],
            ))
        fig.update_layout(
            barmode="stack",
            xaxis=dict(tickfont=dict(size=8), tickangle=-30),
            yaxis=dict(ticksuffix="%", tickfont=dict(size=9)),
            legend=dict(font=dict(size=8), orientation="h", y=1.08),
            **dict(height=220, template=T, margin=dict(t=25,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Stage + Partner")

# Chart 4: Revenue pie by region
with r2d:
    st.markdown('<div class="chart-title">Revenue — par région</div>', unsafe_allow_html=True)
    if col_region and col_rev and n > 0:
        grp = fdf.groupby(col_region)[col_rev].sum().reset_index()
        fig = go.Figure(go.Pie(
            labels=grp[col_region], values=grp[col_rev].round(2),
            hole=0.4,
            marker=dict(colors=REG_COLORS[:len(grp)], line=dict(color="#fff",width=1)),
            textfont=dict(size=9),
        ))
        fig.update_layout(
            legend=dict(font=dict(size=8), orientation="v", x=1),
            **dict(height=220, template=T, margin=dict(t=10,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    elif not col_rev:
        # Pie by count
        grp = fdf.groupby(col_region).size().reset_index(name="cnt") if col_region else None
        if grp is not None:
            fig = go.Figure(go.Pie(
                labels=grp[col_region], values=grp["cnt"], hole=0.4,
                marker=dict(colors=REG_COLORS[:len(grp)], line=dict(color="#fff",width=1)),
                textfont=dict(size=9)
            ))
            fig.update_layout(height=220, template=T, margin=dict(t=10,b=5,l=5,r=5))
            st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Région dans la sidebar")

st.markdown("<div style='margin:4px 0'></div>", unsafe_allow_html=True)

# ── ROW 3 — 3 CHARTS ─────────────────────────────────────────────────────────
r3a, r3b, r3c = st.columns([1.5, 2, 1.5])

# Revenue by stage × partner
with r3a:
    st.markdown('<div class="chart-title">Revenue par stage — partner driven</div>', unsafe_allow_html=True)
    if col_stage and col_rev and n > 0:
        grp = fdf.groupby([col_stage]+([col_partner] if col_partner else []))[col_rev].sum().reset_index()
        fig = go.Figure()
        if col_partner:
            for i, pv in enumerate(partners[:4]):
                sub = grp[grp[col_partner]==pv]
                fig.add_trace(go.Bar(
                    name=str(pv), x=sub[col_stage], y=sub[col_rev].round(2),
                    marker_color=PARTNER_COLORS[i % len(PARTNER_COLORS)],
                ))
            bm = "group"
        else:
            fig.add_trace(go.Bar(x=grp[col_stage], y=grp[col_rev].round(2),
                                  marker_color=STAGE_COLORS))
            bm = "relative"
        fig.update_layout(
            barmode=bm,
            xaxis=dict(tickfont=dict(size=8), tickangle=-30),
            yaxis=dict(tickfont=dict(size=9)),
            legend=dict(font=dict(size=8), orientation="h", y=1.08),
            **dict(height=210, template=T, margin=dict(t=25,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Stage + Revenue")

# Avg revenue by region × size horizontal
with r3b:
    st.markdown('<div class="chart-title">Avg revenue — région & taille</div>', unsafe_allow_html=True)
    if col_region and col_rev and n > 0:
        if col_size:
            grp = fdf.groupby([col_region, col_size])[col_rev].mean().reset_index()
            fig = go.Figure()
            for i, sz in enumerate(sizes[:6]):
                sub = grp[grp[col_size]==sz]
                fig.add_trace(go.Bar(
                    name=sz, y=sub[col_region], x=sub[col_rev].round(2),
                    orientation="h",
                    marker_color=SIZE_COLORS[i % len(SIZE_COLORS)],
                ))
            bm = "group"
        else:
            grp = fdf.groupby(col_region)[col_rev].mean().reset_index()
            fig = go.Figure(go.Bar(
                y=grp[col_region], x=grp[col_rev].round(2),
                orientation="h", marker_color=REG_COLORS[:len(grp)]
            ))
            bm = "relative"
        fig.update_layout(
            barmode=bm,
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            legend=dict(font=dict(size=8), orientation="h", y=1.08),
            **dict(height=210, template=T, margin=dict(t=25,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Région + Revenue")

# Opportunity count by size donut
with r3c:
    st.markdown('<div class="chart-title">Count par taille — donut</div>', unsafe_allow_html=True)
    if col_size and n > 0:
        grp = fdf.groupby(col_size).size().reset_index(name="cnt")
        fig = go.Figure(go.Pie(
            labels=grp[col_size], values=grp["cnt"], hole=0.5,
            marker=dict(colors=SIZE_COLORS[:len(grp)], line=dict(color="#fff",width=1)),
            textfont=dict(size=9),
        ))
        fig.update_layout(
            legend=dict(font=dict(size=8), orientation="v"),
            **dict(height=210, template=T, margin=dict(t=10,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Taille dans la sidebar")

st.markdown("<div style='margin:4px 0'></div>", unsafe_allow_html=True)

# ── ROW 4 — 3 CHARTS ─────────────────────────────────────────────────────────
r4a, r4b, r4c = st.columns([2, 1.5, 1.5])

# Revenue trend line
with r4a:
    st.markdown('<div class="chart-title">Revenue trend — évolution mensuelle</div>', unsafe_allow_html=True)
    if col_date and col_rev and n > 0:
        if use_demo:
            grp = fdf.groupby("Month")[col_rev].sum().reset_index()
            grp["_lbl"] = grp["Month"].apply(lambda x: MONTHS[int(x)])
            x_vals = grp["_lbl"]; y_vals = grp[col_rev].round(2)
        else:
            try:
                fdf["_dt"] = pd.to_datetime(fdf[col_date], infer_datetime_format=True, errors="coerce")
                grp = fdf.dropna(subset=["_dt"]).groupby("_dt")[col_rev].sum().reset_index().sort_values("_dt")
                x_vals = grp["_dt"]; y_vals = grp[col_rev].round(2)
            except:
                grp = fdf.groupby(col_date)[col_rev].sum().reset_index()
                x_vals = grp[col_date]; y_vals = grp[col_rev].round(2)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals, mode="lines+markers",
            fill="tozeroy", fillcolor="rgba(43,87,154,0.08)",
            line=dict(color="#2B579A", width=2),
            marker=dict(size=4),
        ))
        fig.update_layout(
            xaxis=dict(tickfont=dict(size=8), tickangle=-30),
            yaxis=dict(tickfont=dict(size=9)),
            **dict(height=195, template=T, margin=dict(t=10,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Date + Revenue")

# Factored revenue by stage
with r4b:
    st.markdown('<div class="chart-title">Factored revenue par stage</div>', unsafe_allow_html=True)
    if col_stage and col_fact and n > 0:
        grp = fdf.groupby(col_stage)[col_fact].sum().reset_index().sort_values(col_fact, ascending=False)
        fig = go.Figure(go.Bar(
            x=grp[col_stage], y=grp[col_fact].round(2),
            marker_color=STAGE_COLORS[:len(grp)],
            text=grp[col_fact].apply(fmt), textposition="outside", textfont=dict(size=8)
        ))
        fig.update_layout(
            xaxis=dict(tickfont=dict(size=8), tickangle=-30),
            yaxis=dict(tickfont=dict(size=9)),
            **dict(height=195, template=T, margin=dict(t=10,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    elif col_stage and n > 0:
        grp = fdf.groupby(col_stage).size().reset_index(name="cnt")
        fig = go.Figure(go.Bar(
            x=grp[col_stage], y=grp["cnt"],
            marker_color=STAGE_COLORS[:len(grp)],
            text=grp["cnt"], textposition="outside", textfont=dict(size=8)
        ))
        fig.update_layout(height=195, template=T, margin=dict(t=10,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Stage + CA Factorisé")

# Factored revenue by size
with r4c:
    st.markdown('<div class="chart-title">Factored revenue par taille</div>', unsafe_allow_html=True)
    if col_size and col_fact and n > 0:
        grp = fdf.groupby(col_size)[col_fact].sum().reset_index()
        fig = go.Figure(go.Bar(
            x=grp[col_size], y=grp[col_fact].round(2),
            marker_color=SIZE_COLORS[:len(grp)],
            text=grp[col_fact].apply(fmt), textposition="outside", textfont=dict(size=8)
        ))
        fig.update_layout(
            xaxis=dict(tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            **dict(height=195, template=T, margin=dict(t=10,b=5,l=5,r=5))
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    elif col_size and n > 0:
        grp = fdf.groupby(col_size).size().reset_index(name="cnt")
        fig = go.Figure(go.Bar(
            x=grp[col_size], y=grp["cnt"],
            marker_color=SIZE_COLORS[:len(grp)],
            text=grp["cnt"], textposition="outside", textfont=dict(size=8)
        ))
        fig.update_layout(height=195, template=T, margin=dict(t=10,b=5,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CFG)
    else:
        st.info("Configurez Taille")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#2B579A;color:#fff;padding:6px 14px;border-radius:4px;
            margin-top:8px;display:flex;justify-content:space-between;align-items:center">
  <span style="font-size:11px">{n:,} enregistrements filtrés</span>
  <span style="font-size:11px">Revenue total : {fmt(total_rev) if col_rev else '—'}
    &nbsp;|&nbsp; Factorisé : {fmt(total_fact) if col_fact else '—'}
    &nbsp;|&nbsp; Win rate : {win_rate}%
  </span>
  <span style="font-size:11px;opacity:.7">Power BI Dashboard v3.0</span>
</div>
""", unsafe_allow_html=True)

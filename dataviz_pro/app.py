import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io, warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Torre de Controle", page_icon="🏭",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*,body,[class*="css"]{font-family:'Inter',sans-serif!important}
[data-testid="stAppViewContainer"]{background:#0f1117!important}
[data-testid="stHeader"],[data-testid="stToolbar"]{display:none!important}
[data-testid="stSidebar"]{display:none!important}
.block-container{padding:12px 16px 20px!important;max-width:100%!important}
footer,#MainMenu{display:none!important}
div[data-testid="column"]{padding:0 3px!important}
[data-testid="stFileUploadDropzone"]{background:#1a1d27!important;border-color:#2a2d3e!important}
[data-testid="stFileUploadDropzone"] label,[data-testid="stFileUploadDropzone"] p{color:#94a3b8!important}
.stSelectbox > div > div{background:#1a1d27!important;border-color:#3a3d4e!important;color:#fff!important}
.stSelectbox label{color:#64748b!important;font-size:10px!important}
.stSlider label{color:#64748b!important;font-size:10px!important}
.stSlider [data-testid="stThumbValue"]{color:#0ea5e9!important}
</style>
""", unsafe_allow_html=True)

DARK_BG  = "#0f1117"
CARD_BG  = "#1a1d27"
BORDER   = "#2a2d3e"
TEAL     = "#0d9488"
ORANGE   = "#f59e0b"
BLUE     = "#3b82f6"
CORAL    = "#e05a2b"
TEXT_SEC = "#94a3b8"
TEXT_DIM = "#64748b"
CFG      = dict(displayModeBar=False)

def fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    v = float(v)
    if abs(v) >= 1e9:  return f"{v/1e9:.1f} Bi"
    if abs(v) >= 1e6:  return f"{v/1e6:.1f} Mi"
    if abs(v) >= 1e3:  return f"{v/1e3:.1f} Mil"
    return f"{v:.2g}"

def card(content, extra_style=""):
    return f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px;{extra_style}">{content}</div>'

def sec(title):
    return f'<div style="font-size:10px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.7px;margin-bottom:8px">{title}</div>'

def rank_bars(labels, values, color=CORAL, max_n=10):
    labels  = [str(l)[:22] for l in labels[:max_n]]
    values  = [float(v)    for v in values[:max_n]]
    mx = max(values) if values else 1
    rows = ""
    for l, v in zip(labels, values):
        pct = 100 * v / mx if mx else 0
        rows += f"""<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">
          <div style="font-size:10px;color:{TEXT_SEC};width:120px;text-align:right;
               white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{l}">{l}</div>
          <div style="flex:1;background:{BORDER};border-radius:3px;height:13px;overflow:hidden">
            <div style="width:{pct:.0f}%;height:13px;border-radius:3px;background:{color}"></div></div>
          <div style="font-size:9px;color:#fff;font-weight:600;min-width:38px">{fmt(v)}</div>
        </div>"""
    return rows

def gauge_fig(value, color, max_val=100):
    try: val = float(value)
    except: val = 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(val, 1),
        number=dict(suffix="%" if max_val == 100 else "",
                    font=dict(size=26, color="#fff", family="Inter")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(color=TEXT_DIM, size=7),
                      tickwidth=0, nticks=3),
            bar=dict(color=color, thickness=0.72),
            bgcolor=BORDER, borderwidth=0,
            steps=[dict(range=[0, max_val], color=BORDER)],
        )
    ))
    fig.update_layout(height=150, margin=dict(t=8, b=4, l=18, r=18),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#fff"))
    return fig

def spark(series, color):
    s = pd.Series(series).dropna().reset_index(drop=True)
    if len(s) < 2: return None
    try:
        r, g, b = px.colors.hex_to_rgb(color)
        fill_c  = f"rgba({r},{g},{b},0.12)"
    except:
        fill_c  = "rgba(13,148,136,0.12)"
    fig = go.Figure(go.Scatter(
        y=s, mode="lines", fill="tozeroy",
        line=dict(color=color, width=1.5), fillcolor=fill_c, showlegend=False
    ))
    fig.update_layout(
        height=52, margin=dict(t=2, b=2, l=2, r=2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False)
    )
    return fig

def load_file(f):
    name = f.name.lower()
    try:
        if name.endswith((".xlsx", ".xls")):
            xl  = pd.ExcelFile(f)
            df  = pd.read_excel(f, sheet_name=xl.sheet_names[0])
            return df, xl.sheet_names, None
        elif name.endswith(".csv"):
            raw = f.read(4096).decode("utf-8", "replace"); f.seek(0)
            sep = ";" if raw.count(";") > raw.count(",") else ","
            return pd.read_csv(f, sep=sep, on_bad_lines="skip"), ["CSV"], None
        elif name.endswith(".tsv"):
            return pd.read_csv(f, sep="\t", on_bad_lines="skip"), ["TSV"], None
        return None, [], "Format non supporté (.xlsx .xls .csv .tsv)"
    except Exception as e:
        return None, [], str(e)

def classify(df):
    num, cat, dates = [], [], []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_numeric_dtype(s):
            num.append(c)
        elif pd.api.types.is_datetime64_any_dtype(s):
            dates.append(c)
        else:
            try:
                p = pd.to_datetime(s, infer_datetime_format=True, errors="coerce")
                if p.notna().mean() > 0.55:
                    dates.append(c); continue
            except: pass
            cat.append(c)
    return num, cat, dates

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;
     padding:10px 18px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between">
  <div>
    <div style="font-size:18px;font-weight:800;color:#fff">🏭 Torre de Controle</div>
    <div style="font-size:11px;color:{TEXT_DIM};margin-top:1px">Indicadores de Desempenho · Dashboard automatique</div>
  </div>
  <div style="font-size:11px;color:{TEXT_DIM}">Upload Excel / CSV → analyse instantanée · zéro configuration</div>
</div>
""", unsafe_allow_html=True)

# ── UPLOAD ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("", type=["xlsx", "xls", "csv", "tsv"],
                             label_visibility="collapsed")

if not uploaded:
    st.markdown(f"""
    <div style="background:{CARD_BG};border:2px dashed {BORDER};border-radius:14px;
         padding:70px 40px;text-align:center;margin:50px auto;max-width:540px">
      <div style="font-size:52px;margin-bottom:14px">📊</div>
      <div style="font-size:20px;font-weight:700;color:#fff;margin-bottom:8px">
        Glissez votre fichier ici</div>
      <div style="font-size:13px;color:{TEXT_DIM}">
        Excel (.xlsx .xls) · CSV · TSV<br>
        N'importe quelle structure — analyse 100% automatique</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df_raw, sheets, err = load_file(uploaded)
if err or df_raw is None:
    st.error(f"❌ Erreur : {err}"); st.stop()

df_raw.columns  = [str(c).strip() for c in df_raw.columns]
df_raw          = df_raw.dropna(how="all").reset_index(drop=True)

# Sheet picker
if len(sheets) > 1:
    s1, s2 = st.columns([1, 9])
    chosen = s1.selectbox("Feuille", sheets, key="sht")
    try:
        df_raw = pd.read_excel(uploaded, sheet_name=chosen)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        df_raw = df_raw.dropna(how="all").reset_index(drop=True)
    except: pass

num_cols, cat_cols, date_cols = classify(df_raw)

# Best cols
def nth(lst, n, fallback=None):
    return lst[n] if len(lst) > n else fallback

best_num  = nth(num_cols, 0)
best_num2 = nth(num_cols, 1, best_num)
best_num3 = nth(num_cols, 2, best_num)
best_cat  = nth(cat_cols, 0)
best_cat2 = nth(cat_cols, 1, best_cat)
best_date = nth(date_cols, 0)

# ── FILTER BAR ────────────────────────────────────────────────────────────────
fc = st.columns([1.1, 1.1, 1.1, 1.3, 0.45])

def safe_uniq(col, max_n=50):
    if col is None: return []
    return sorted(df_raw[col].dropna().astype(str).unique().tolist())[:max_n]

fv1 = fc[0].selectbox(
    best_cat or "—",
    ["Tous"] + safe_uniq(best_cat), key="f1"
) if best_cat else None

fv2 = fc[1].selectbox(
    best_cat2 if best_cat2 != best_cat else (nth(cat_cols, 2) or "—"),
    ["Tous"] + safe_uniq(best_cat2 if best_cat2 != best_cat else nth(cat_cols, 2)), key="f2"
) if (best_cat2 and best_cat2 != best_cat) or nth(cat_cols, 2) else None
_cat2_col = best_cat2 if best_cat2 != best_cat else nth(cat_cols, 2)

fv3 = fc[2].selectbox(
    best_date or "—",
    ["Toutes"] + safe_uniq(best_date, 80), key="f3"
) if best_date else None

if best_num:
    _mn = float(df_raw[best_num].min())
    _mx = float(df_raw[best_num].max())
    fv4 = fc[3].slider(best_num, _mn, _mx, (_mn, _mx), key="f4") if _mn < _mx else (_mn, _mx)
else:
    fv4 = None

if fc[4].button("↺", use_container_width=True, help="Réinitialiser les filtres"):
    for k in ["f1","f2","f3","f4","sht","gran"]: st.session_state.pop(k, None)
    st.rerun()

# Apply
df = df_raw.copy()
if best_cat and fv1 and fv1 != "Tous":       df = df[df[best_cat].astype(str) == fv1]
if _cat2_col and fv2 and fv2 != "Tous":      df = df[df[_cat2_col].astype(str) == fv2]
if best_date and fv3 and fv3 != "Toutes":    df = df[df[best_date].astype(str) == fv3]
if best_num and fv4:
    df = df[(df[best_num] >= fv4[0]) & (df[best_num] <= fv4[1])]

n = len(df)
if n == 0:
    st.warning("⚠️ Aucune donnée après filtrage. Réinitialisez les filtres."); st.stop()

# ── COMPUTED METRICS ─────────────────────────────────────────────────────────
missing_pct  = round(100 * df.isnull().sum().sum() / max(n * len(df.columns), 1), 1)
completeness = round(100 - missing_pct, 1)
dupes        = int(df.duplicated().sum())

def norm_pct(col):
    if col is None: return 50.0
    s = df[col].dropna()
    if len(s) == 0: return 0.0
    mn, mx = df_raw[col].min(), df_raw[col].max()
    if mx == mn: return 50.0
    return round(100 * (s.mean() - mn) / (mx - mn), 1)

r1v = norm_pct(best_num)
r2v = norm_pct(best_num2) if best_num2 != best_num else completeness
r3v = norm_pct(best_num3) if best_num3 not in (best_num, best_num2) else completeness
oee = round((r1v / 100) * (r2v / 100) * (r3v / 100) * 100, 2)

total1 = df[best_num].sum()  if best_num  else n
total2 = df[best_num2].sum() if best_num2 else 0
total3 = df[best_num3].sum() if best_num3 not in (best_num, best_num2) else 0

# ── ROW A — TOP KPIS ─────────────────────────────────────────────────────────
ra = st.columns([1.3, 1, 1, 1, 2.2])

ra[0].markdown(card(f"""
  <div style="font-size:10px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.5px">
    {uploaded.name[:26]}</div>
  <div style="margin-top:8px;font-size:11px;color:{TEXT_SEC}">
    <span style="font-size:22px;font-weight:800;color:#fff">{n:,}</span> lignes &nbsp;·&nbsp;
    <span style="color:#fff;font-weight:700">{len(df.columns)}</span> cols
  </div>
  <div style="margin-top:6px;font-size:10px;color:{TEXT_DIM}">
    {len(num_cols)} num &nbsp;·&nbsp; {len(cat_cols)} cat &nbsp;·&nbsp; {len(date_cols)} dates &nbsp;·&nbsp;
    <span style="color:{'#0d9488' if completeness>=95 else '#f59e0b'}">{completeness}% complet</span>
    {"&nbsp;·&nbsp;<span style='color:#ef4444'>⚠ "+str(dupes)+" dup</span>" if dupes>0 else ""}
  </div>
"""), unsafe_allow_html=True)

for i, (col_n, val, lbl) in enumerate([
    (best_num,  total1, "Total"),
    (best_num2 if best_num2 != best_num else None, total2 if best_num2 != best_num else df[best_num].mean() if best_num else 0,
     "Somme" if best_num2 != best_num else "Moyenne"),
    (best_num3 if best_num3 not in (best_num, best_num2) else None,
     total3 if best_num3 not in (best_num, best_num2) else df[best_num].median() if best_num else 0,
     "Somme" if best_num3 not in (best_num, best_num2) else "Médiane"),
]):
    nm = col_n or best_num or "—"
    ra[i+1].markdown(card(f"""
      <div style="font-size:10px;color:{TEXT_DIM}">{(nm or '')[:20]}</div>
      <div style="font-size:26px;font-weight:800;color:#fff;margin-top:4px">{fmt(val)}</div>
      <div style="font-size:10px;color:{TEXT_DIM};margin-top:4px">{lbl}</div>
    """), unsafe_allow_html=True)

# Teal KPI banner
ra[4].markdown(f"""
<div style="background:#0e7490;border-radius:10px;padding:12px 18px;
     display:flex;align-items:center;gap:0;height:100%">
  <div style="flex:1;text-align:center;padding:0 10px">
    <div style="font-size:24px;font-weight:800;color:#fff">{fmt(total1)}</div>
    <div style="font-size:10px;color:rgba(255,255,255,.75);margin-top:3px">
      {(best_num or 'Total')[:20]}</div>
  </div>
  <div style="width:1px;height:44px;background:rgba(255,255,255,.2)"></div>
  <div style="flex:1;text-align:center;padding:0 10px">
    <div style="font-size:24px;font-weight:800;color:#fff">{fmt(total2 if best_num2 and best_num2!=best_num else (df[best_num].mean() if best_num else 0))}</div>
    <div style="font-size:10px;color:rgba(255,255,255,.75);margin-top:3px">
      {(best_num2 if best_num2 and best_num2!=best_num else ('Moy. '+str(best_num or ''))[:20])[:20]}</div>
  </div>
  <div style="width:1px;height:44px;background:rgba(255,255,255,.2)"></div>
  <div style="flex:1;text-align:center;padding:0 10px">
    <div style="font-size:24px;font-weight:800;color:#fed7aa">{df[best_cat].nunique() if best_cat else len(cat_cols)}</div>
    <div style="font-size:10px;color:rgba(255,255,255,.75);margin-top:3px">
      {('Uniques '+str(best_cat or 'Cat'))[:20]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── ROW B — OEE + 3 GAUGES + RANKING ─────────────────────────────────────────
rb = st.columns([1.2, 1.8, 2.2])

# OEE Gauge
with rb[0]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:10px 12px">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.6px">Score global composite</div>', unsafe_allow_html=True)
    st.plotly_chart(gauge_fig(oee, TEAL), use_container_width=True, config=CFG)
    if best_num:
        sp = spark(df[best_num].reset_index(drop=True), TEAL)
        if sp: st.plotly_chart(sp, use_container_width=True, config=CFG)
    st.markdown("</div>", unsafe_allow_html=True)

# 3 mini gauges
with rb[1]:
    gauge_defs = [
        (best_num,  r1v, ORANGE, "⏱"),
        (best_num2 if best_num2 != best_num else "Complétude", r2v, BLUE,   "📈"),
        (best_num3 if best_num3 not in (best_num, best_num2) else "Qualité", r3v, CORAL, "👍"),
    ]
    src_num = [best_num,
               best_num2 if best_num2 != best_num else best_num,
               best_num3 if best_num3 not in (best_num, best_num2) else best_num]

    for (lbl, rate, col, icon), src in zip(gauge_defs, src_num):
        gc1, gc2 = st.columns([1, 1])
        with gc1:
            st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:6px 8px">'
                        f'<div style="font-size:10px;color:#fff;font-weight:600">{str(lbl)[:18]}</div>', unsafe_allow_html=True)
            st.plotly_chart(gauge_fig(rate, col), use_container_width=True, config=CFG)
            st.markdown("</div>", unsafe_allow_html=True)
        with gc2:
            if src and best_date:
                try:
                    ts = df.copy()
                    ts["_d"] = pd.to_datetime(ts[best_date], infer_datetime_format=True, errors="coerce")
                    ts2 = ts.dropna(subset=["_d"]).sort_values("_d").groupby("_d")[src].sum()
                    sp = spark(ts2, col)
                except:
                    sp = spark(df[src].reset_index(drop=True), col) if src else None
            elif src:
                sp = spark(df[src].reset_index(drop=True), col)
            else:
                sp = None

            st.markdown(f"<div style='margin-top:32px'></div>", unsafe_allow_html=True)
            if sp: st.plotly_chart(sp, use_container_width=True, config=CFG)
            st.markdown(f'<div style="background:{col};border-radius:7px;width:32px;height:32px;'
                        f'display:flex;align-items:center;justify-content:center;font-size:14px;margin:4px auto">{icon}</div>',
                        unsafe_allow_html=True)

# Ranking 1
with rb[2]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px;height:100%">', unsafe_allow_html=True)
    if best_cat and best_num:
        grp = df.groupby(best_cat)[best_num].sum().sort_values(ascending=False).head(10)
        title = f"Ranking <b style='color:#fff'>{best_cat}</b> — {best_num}"
        bars  = rank_bars(grp.index.tolist(), grp.values.tolist(), CORAL)
    elif best_cat:
        grp  = df[best_cat].value_counts().head(10)
        title = f"Ranking <b style='color:#fff'>{best_cat}</b>"
        bars  = rank_bars(grp.index.tolist(), grp.values.tolist(), CORAL)
    else:
        title, bars = "Ranking", ""
    st.markdown(f'<div style="font-size:11px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px">{title}</div>{bars}', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── ROW C — TIME SERIES + RANKING 2 ──────────────────────────────────────────
rc = st.columns([2.8, 1.2])

with rc[0]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px">', unsafe_allow_html=True)
    h1, h2 = st.columns([3, 1])
    h1.markdown(f'<div style="font-size:11px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.5px">'
                f'<b style="color:#fff">{best_num or "Valeur"}</b> — évolution & distribution</div>', unsafe_allow_html=True)
    gran = h2.selectbox("", ["Mois","Semaine","Jour","Trimestre","Année"],
                         index=0, key="gran", label_visibility="collapsed")

    GRAN = {"Jour":"D","Semaine":"W","Mois":"ME","Trimestre":"QE","Année":"YE"}

    fig_ts = go.Figure()
    if best_date and best_num:
        try:
            ts = df.copy()
            ts["_d"] = pd.to_datetime(ts[best_date], infer_datetime_format=True, errors="coerce")
            ts_c = ts.dropna(subset=["_d"]).sort_values("_d")
            PAL  = [TEAL, ORANGE, BLUE, CORAL, "#a855f7", "#ec4899", "#84cc16", "#14b8a6"]
            cats = df[best_cat].dropna().unique().tolist() if best_cat and df[best_cat].nunique() <= 8 else []

            if cats:
                for i, cv in enumerate(cats[:8]):
                    sub = ts_c[ts_c[best_cat] == cv]
                    agg = sub.set_index("_d")[best_num].resample(GRAN[gran]).sum().reset_index()
                    fig_ts.add_trace(go.Bar(x=agg["_d"], y=agg[best_num],
                                            name=str(cv)[:16], marker_color=PAL[i % len(PAL)], opacity=.85))
                fig_ts.update_layout(barmode="stack")
            else:
                agg = ts_c.set_index("_d")[best_num].resample(GRAN[gran]).sum().reset_index()
                fig_ts.add_trace(go.Bar(x=agg["_d"], y=agg[best_num],
                                        marker_color=TEAL, name=best_num, opacity=.85))
                fig_ts.add_trace(go.Scatter(x=agg["_d"], y=agg[best_num],
                                            mode="lines", line=dict(color="#fff", width=1.5),
                                            showlegend=False))
        except: pass
    elif best_num:
        fig_ts.add_trace(go.Histogram(x=df[best_num].dropna(), nbinsx=35,
                                       marker_color=TEAL, opacity=.85, name=best_num))

    fig_ts.update_layout(
        height=230, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=4, b=4, l=4, r=4), font=dict(color=TEXT_SEC, size=9),
        xaxis=dict(gridcolor=BORDER, showgrid=True, tickfont=dict(color=TEXT_DIM, size=8), tickangle=-30),
        yaxis=dict(gridcolor=BORDER, showgrid=True, tickfont=dict(color=TEXT_DIM, size=9)),
        legend=dict(font=dict(size=8, color=TEXT_SEC), bgcolor="rgba(0,0,0,0)",
                    orientation="h", y=-0.18),
        bargap=0.12
    )
    st.plotly_chart(fig_ts, use_container_width=True, config=CFG)
    st.markdown("</div>", unsafe_allow_html=True)

with rc[1]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px;height:100%">', unsafe_allow_html=True)
    cat2_col = _cat2_col if _cat2_col and _cat2_col != best_cat else best_cat
    if cat2_col:
        if best_num:
            grp2 = df.groupby(cat2_col)[best_num].count().sort_values(ascending=False).head(8)
        else:
            grp2 = df[cat2_col].value_counts().head(8)
        t2   = f"Occurrences <b style='color:#fff'>{cat2_col}</b>"
        b2   = rank_bars(grp2.index.tolist(), grp2.values.tolist(), ORANGE)
    else:
        t2, b2 = "Ranking", ""
    st.markdown(f'<div style="font-size:11px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px">{t2}</div>{b2}',
                unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── ROW D — CORRELATION + BOXPLOTS + PIE ─────────────────────────────────────
rd = st.columns([1.5, 1.5, 1])

with rd[0]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">Matrice de corrélation</div>', unsafe_allow_html=True)
    if len(num_cols) >= 2:
        corr = df[num_cols[:8]].corr().round(2)
        fig_cr = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
            colorscale=[[0,"#1e3a5f"],[0.5,CARD_BG],[1,TEAL]],
            zmid=0, zmin=-1, zmax=1,
            text=corr.values, texttemplate="%{text}", textfont=dict(size=8, color="#fff"),
            colorbar=dict(tickfont=dict(color=TEXT_DIM, size=7), len=0.8, thickness=10)
        ))
        fig_cr.update_layout(
            height=210, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=4, b=4, l=4, r=4),
            xaxis=dict(tickfont=dict(color=TEXT_DIM, size=8), tickangle=-30),
            yaxis=dict(tickfont=dict(color=TEXT_DIM, size=8))
        )
        st.plotly_chart(fig_cr, use_container_width=True, config=CFG)
    else:
        st.info("2+ colonnes numériques requises pour la corrélation.")
    st.markdown("</div>", unsafe_allow_html=True)

with rd[1]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">Distributions (Boxplots)</div>', unsafe_allow_html=True)
    if num_cols:
        PAL_B = [ORANGE, TEAL, BLUE, CORAL]
        fig_bx = go.Figure()
        for i, c in enumerate(num_cols[:4]):
            try:
                r, g, b = px.colors.hex_to_rgb(PAL_B[i % 4])
                fill_c  = f"rgba({r},{g},{b},0.2)"
            except:
                fill_c  = "rgba(13,148,136,0.2)"
            fig_bx.add_trace(go.Box(
                y=df[c].dropna(), name=c[:14], boxpoints=False,
                marker_color=PAL_B[i % 4],
                line=dict(color=PAL_B[i % 4], width=1.5),
                fillcolor=fill_c
            ))
        fig_bx.update_layout(
            height=210, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=4, b=4, l=4, r=4), font=dict(color=TEXT_SEC, size=9),
            xaxis=dict(tickfont=dict(color=TEXT_DIM, size=8)),
            yaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT_DIM, size=8)),
            legend=dict(font=dict(size=8, color=TEXT_SEC), bgcolor="rgba(0,0,0,0)",
                        orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_bx, use_container_width=True, config=CFG)
    else:
        st.info("Aucune colonne numérique.")
    st.markdown("</div>", unsafe_allow_html=True)

with rd[2]:
    st.markdown(f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:10px;padding:12px 14px">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:{TEXT_DIM};font-weight:600;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">Répartition</div>', unsafe_allow_html=True)
    if best_cat:
        vc = df[best_cat].value_counts().head(7)
        PAL_P = [TEAL, ORANGE, BLUE, CORAL, "#a855f7", "#ec4899", "#84cc16"]
        fig_p = go.Figure(go.Pie(
            labels=[str(l)[:15] for l in vc.index], values=vc.values, hole=0.5,
            marker=dict(colors=PAL_P[:len(vc)], line=dict(color=CARD_BG, width=2)),
            textfont=dict(size=8, color="#fff"), textposition="inside"
        ))
        fig_p.update_layout(
            height=210, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=4, b=4, l=4, r=30),
            legend=dict(font=dict(size=8, color=TEXT_SEC), bgcolor="rgba(0,0,0,0)", x=1.02)
        )
        st.plotly_chart(fig_p, use_container_width=True, config=CFG)
    else:
        st.info("Aucune colonne catégorielle.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
miss_info = " · ".join([f"{c}: {v}" for c, v in
    [(c, int(df[c].isnull().sum())) for c in df.columns if df[c].isnull().sum() > 0][:4]]
) or "✅ Aucune valeur manquante"

st.markdown(f"""
<div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;
     padding:7px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
  <span style="font-size:10px;color:{TEXT_DIM}">
    <b style="color:#0ea5e9">{n:,}</b> / <b style="color:#fff">{len(df_raw):,}</b> lignes affichées
  </span>
  <span style="font-size:10px;color:{TEXT_DIM}">Manquants : <b style="color:{ORANGE}">{miss_info[:70]}</b></span>
  <span style="font-size:10px;color:{TEXT_DIM}">Score composite : <b style="color:{TEAL}">{oee}%</b></span>
  <span style="font-size:10px;color:#334155">Torre de Controle · v4.0</span>
</div>
""", unsafe_allow_html=True)

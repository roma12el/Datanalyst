import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
import json, os, re, unicodedata

st.set_page_config(page_title="Tableau de bord", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f0f2f6; }
[data-testid="stSidebar"] { background: #1e2d3d; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] h3 { color: #e0e8f0 !important; border-bottom: 1px solid #2e4a63; padding-bottom: 6px; }
.block-container { padding: 1.2rem 2rem; }
div[data-testid="stMetric"] { background: white; border-radius: 12px; padding: 16px 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); border-top: 4px solid #c0392b; }
div[data-testid="stMetric"] label { font-size: 11px !important; color: #888 !important; text-transform: uppercase; letter-spacing: .5px; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700 !important; color: #1e2d3d !important; }
div[data-testid="stMetric"] [data-testid="stMetricDelta"] svg { display: none; }
.section-title { font-size: 15px; font-weight: 600; color: #1e2d3d; margin: 18px 0 10px; border-left: 4px solid #c0392b; padding-left: 10px; }
.insight-good  { background: #f0fff4; border-left: 4px solid #27ae60; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 5px 0; font-size: 13px; color: #1a5c2a; }
.insight-alert { background: #fff0f0; border-left: 4px solid #c0392b; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 5px 0; font-size: 13px; color: #7b1a1a; }
.insight-warn  { background: #fff8f0; border-left: 4px solid #f39c12; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 5px 0; font-size: 13px; color: #7a4f00; }
.insight-info  { background: #f0f4ff; border-left: 4px solid #2980b9; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 5px 0; font-size: 13px; color: #1a3a5c; }
</style>
""", unsafe_allow_html=True)

COLORS = ['#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad','#16a085','#d35400','#e74c3c','#3498db','#2ecc71']
CONFIG_FILE = "dashboard_config.json"

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

NULL_VALUES = {
    'na','n/a','n.a','n.a.','na.','nan','none','null','nil','void',
    'nd','n.d','n.d.','-','--','---','—','–','_','__','?',
    'vide','manquant','missing','empty','inconnu','unknown','nr','ns','nc'
}

def normalize_text(s):
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn').lower().strip()
    except Exception:
        return str(s).lower().strip()

def parse_number(val):
    if pd.isna(val): return None
    if isinstance(val, (int, float, np.integer, np.floating)):
        return float(val) if not np.isnan(float(val)) else None
    s = str(val).strip()
    if not s or normalize_text(s) in NULL_VALUES: return None
    s = re.sub(r'[€$£¥₹\u00a0\u202f]', '', s).strip()
    if re.match(r'^\([\d\s.,]+\)$', s): s = '-' + s[1:-1]
    is_pct = s.endswith('%')
    if is_pct: s = s[:-1].strip()
    s = re.sub(r'\s+', '', s)
    if ',' in s and '.' in s:
        s = s.replace('.','').replace(',','.') if s.rfind(',') > s.rfind('.') else s.replace(',','')
    elif ',' in s:
        after = s[s.rfind(',')+1:]
        s = s.replace(',','.') if len(after) <= 2 else (s.replace(',','') if len(s[:s.rfind(',')]) <= 3 else s.replace(',','.'))
    try:
        return float(s)
    except ValueError:
        return None

def try_parse_date(series):
    s = series.dropna().astype(str)
    if len(s) == 0: return None, False
    if pd.to_numeric(s, errors='coerce').notna().all(): return None, False
    if s.str.match(r'^\d{8}$').mean() > 0.7:
        try:
            p = pd.to_datetime(s, format='%Y%m%d', errors='coerce')
            if p.notna().sum()/len(s) > 0.7: return p, True
        except Exception: pass
    if s.str.match(r'^\d{4}[/\-]\d{1,2}$').mean() > 0.7:
        try:
            p = pd.to_datetime(s + '-01', errors='coerce')
            if p.notna().sum()/len(s) > 0.7: return p, True
        except Exception: pass
    for fmt in ['%d/%m/%Y','%d/%m/%y','%Y-%m-%d','%d-%m-%Y','%d.%m.%Y','%m/%d/%Y','%Y/%m/%d']:
        try:
            p = pd.to_datetime(s, format=fmt, errors='coerce')
            if p.notna().sum()/len(s) > 0.7 and p.dropna().dt.year.between(1950,2100).mean() > 0.8:
                return pd.to_datetime(series.astype(str), format=fmt, errors='coerce'), True
        except Exception: pass
    try:
        p = pd.to_datetime(s, dayfirst=True, errors='coerce')
        if p.notna().sum()/len(s) > 0.7 and p.dropna().dt.year.between(1950,2100).mean() > 0.8:
            return pd.to_datetime(series.astype(str), dayfirst=True, errors='coerce'), True
    except Exception: pass
    return None, False

def clean_dataframe(df_in):
    df = df_in.copy()
    rapport = []
    new_cols = []
    for i, c in enumerate(df.columns):
        cs = str(c).strip()
        new_cols.append(f'Colonne_{i+1}' if cs.startswith('Unnamed') or cs in ('','nan') else cs)
    df.columns = new_cols
    before = len(df)
    df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
    if len(df) < before: rapport.append(f"{before-len(df)} lignes vides supprimées.")
    def replace_nulls(val):
        if pd.isna(val): return np.nan
        return np.nan if normalize_text(str(val)) in NULL_VALUES or str(val).strip()=='' else val
    df = df.map(replace_nulls)
    conv_num, conv_date = 0, 0
    for col in df.columns:
        s = df[col]
        non_null = s.dropna()
        if len(non_null)==0 or pd.api.types.is_datetime64_any_dtype(s) or pd.api.types.is_numeric_dtype(s): continue
        parsed = non_null.apply(parse_number)
        if parsed.notna().sum()/len(non_null) >= 0.80:
            df[col] = s.apply(parse_number); conv_num += 1; continue
        pd_dates, ok = try_parse_date(non_null)
        if ok and pd_dates is not None:
            ds = pd.Series(index=df.index, dtype='datetime64[ns]')
            ds[non_null.index] = pd_dates.values
            df[col] = ds; conv_date += 1
    if conv_num > 0: rapport.append(f"{conv_num} colonne(s) convertie(s) en nombres.")
    if conv_date > 0: rapport.append(f"{conv_date} colonne(s) convertie(s) en dates.")
    return df, rapport

@st.cache_data
def load_excel_sheet(fb, sheet):
    try:
        return pd.read_excel(BytesIO(fb), sheet_name=sheet, header=0)
    except Exception:
        df = pd.read_excel(BytesIO(fb), sheet_name=sheet, header=None)
        if df.iloc[0].apply(lambda x: isinstance(x, str)).any():
            df.columns = df.iloc[0].astype(str); df = df.iloc[1:].reset_index(drop=True)
        return df

@st.cache_data
def load_csv_smart(fb):
    best_df, best_score = None, 0
    for enc in ['utf-8-sig','utf-8','latin-1','cp1252']:
        for sep in [';',',','\t','|']:
            try:
                df = pd.read_csv(BytesIO(fb), sep=sep, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df.empty or len(df.columns) <= 1: continue
                score = len(df.columns)*10 + min(len(df),100)
                if score > best_score: best_score, best_df = score, df
            except Exception: pass
    return best_df

ID_KW   = ['id','n°','no','num','numero','numéro','code','ref','reference','matricule',
            'identifiant','contrat','client','compte','dossier','facture','commande',
            'ticket','order','invoice','key','serial','siren','siret']
MEAS_KW = ['montant','somme','total','chiffre','revenu','ca','budget','charge','salaire',
           'prix','cout','coût','marge','consommation','quantite','volume','poids',
           'duree','durée','heure','taux','valeur','amount','sales','revenue','cost',
           'profit','depense','recette','solde','stock','energie','puissance','score',
           'kpi','indicateur','kwh','effectif','nombre','count','qte','qty']

def normalize_col(c): return normalize_text(c).replace(' ','').replace('_','').replace('-','').replace('°','')

def is_year_col(vals, name):
    nm = normalize_col(name)
    if any(k in nm for k in ['annee','année','year']): return True
    v = pd.to_numeric(vals, errors='coerce').dropna()
    return len(v) > 0 and v.between(1900,2100).all() and v.nunique() <= 50

def is_period_col(vals, name):
    nm = normalize_col(name)
    if any(k in nm for k in ['trimestre','semestre','quarter','mois','month']): return True
    v = pd.to_numeric(vals, errors='coerce').dropna()
    return len(v) > 0 and v.between(1,12).all() and v.nunique() <= 12

def auto_classify(df):
    measures, categories, dates, periods, ignored = [], [], [], [], []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0: ignored.append(col); continue
        nm = normalize_col(col)
        if pd.api.types.is_datetime64_any_dtype(df[col]): dates.append(col); continue
        if not pd.api.types.is_numeric_dtype(df[col]): categories.append(col); continue
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) == 0: ignored.append(col); continue
        if any(k in nm for k in ID_KW): categories.append(col); continue
        if is_year_col(vals, col): periods.append(col); continue
        if is_period_col(vals, col): periods.append(col); continue
        uniq = vals.nunique() / len(vals)
        if uniq > 0.9 and not any(k in nm for k in MEAS_KW): ignored.append(col); continue
        if vals.nunique() <= 10 and not any(k in nm for k in MEAS_KW): categories.append(col); continue
        if any(k in nm for k in MEAS_KW): measures.append(col); continue
        if uniq < 0.05: categories.append(col); continue
        measures.append(col)
    return measures, categories, dates, periods, ignored

def detect_domain(df):
    txt = ' '.join(normalize_text(str(c)) for c in df.columns)
    scores = {
        'Financier':    sum(1 for k in ['montant','revenu','budget','charge','salaire','marge','prix','facture'] if k in txt),
        'Commercial':   sum(1 for k in ['client','contrat','commande','vente','region','zone','agence','ca'] if k in txt),
        'RH':           sum(1 for k in ['employe','effectif','absence','conge','departement','agent','matricule'] if k in txt),
        'Stocks':       sum(1 for k in ['stock','produit','quantite','inventaire','article','entrepot'] if k in txt),
        'Opérationnel': sum(1 for k in ['production','qualite','delai','incident','maintenance','panne','consommation'] if k in txt),
        'Énergie':      sum(1 for k in ['energie','kwh','electricite','gaz','puissance','compteur'] if k in txt),
        'Informatique': sum(1 for k in ['pc','ordinateur','imprimante','bureau','portable','processeur'] if k in txt),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Général'

def fmt(val):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)): return "N/A"
        v = float(val)
        if abs(v) >= 1e9: return f"{v/1e9:.2f} Md"
        if abs(v) >= 1e6: return f"{v/1e6:.2f} M"
        if abs(v) >= 1e3: return f"{v/1e3:.1f} K"
        if v == int(v):   return f"{int(v):,}"
        return f"{v:,.2f}"
    except Exception: return str(val)

def pct_change(new, old):
    return None if old == 0 else (new - old) / abs(old) * 100

def chart_style(fig, h=300):
    fig.update_layout(margin=dict(t=45,b=10,l=10,r=10), height=h, showlegend=False,
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(size=11,color='#333'), title_font_size=14, title_font_color='#1e2d3d')
    return fig

def build_time_series(df, col_d, col_m, col_group=None, is_period=False):
    cols = [col_d, col_m] + ([col_group] if col_group and col_group != "Aucun" and col_group in df.columns else [])
    ts = df[[c for c in cols if c in df.columns]].copy()
    ts[col_m] = pd.to_numeric(ts[col_m], errors='coerce')
    if is_period:
        ts[col_d] = pd.to_numeric(ts[col_d], errors='coerce')
        ts = ts.dropna(subset=[col_d, col_m]).sort_values(col_d)
        ts[col_d] = ts[col_d].astype(int).astype(str)
        grp_cols = [col_d] + ([col_group] if col_group and col_group != "Aucun" and col_group in ts.columns else [])
        return ts.groupby(grp_cols)[col_m].sum().reset_index()
    else:
        ts[col_d] = pd.to_datetime(ts[col_d], errors='coerce')
        ts = ts.dropna(subset=[col_d, col_m]).sort_values(col_d)
        if col_group and col_group != "Aucun" and col_group in ts.columns:
            return ts.groupby([pd.Grouper(key=col_d, freq='ME'), col_group])[col_m].sum().reset_index()
        return ts.groupby(pd.Grouper(key=col_d, freq='ME'))[col_m].sum().reset_index()

def analyse_business(df, measures, categories, dates, periods, domain):
    insights = []
    total = len(df)
    missing_pct = df.isna().mean()
    bad = missing_pct[missing_pct > 0.05]
    if bad.empty:
        insights.append(('good', f"Qualité parfaite : aucune valeur manquante sur {total:,} enregistrements."))
    else:
        w = bad.idxmax()
        insights.append(('alert', f"Données incomplètes : **{w}** — {round(bad[w]*100,1)}% manquants."))
    for col in measures[:2]:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) < 2: continue
        mean_v, max_v, total_v = vals.mean(), vals.max(), vals.sum()
        top_pct = (max_v - mean_v) / abs(mean_v) * 100 if mean_v != 0 else 0
        if top_pct > 300:
            insights.append(('alert', f"**{col}** : max ({fmt(max_v)}) anormalement élevé vs moyenne ({fmt(mean_v)})."))
        elif top_pct > 100:
            insights.append(('warn', f"**{col}** : forte dispersion — max {fmt(max_v)}, moy {fmt(mean_v)}."))
        else:
            insights.append(('good', f"**{col}** : total {fmt(total_v)}, moyenne {fmt(mean_v)}."))
    for col in categories[:2]:
        vc = df[col].value_counts()
        if len(vc) < 2: continue
        top_share = vc.iloc[0] / total * 100
        top2 = (vc.iloc[0] + vc.iloc[1]) / total * 100 if len(vc) >= 2 else top_share
        if top_share > 60:
            insights.append(('warn', f"**{col}** : « {vc.index[0]} » = {round(top_share)}% — forte concentration."))
        elif top2 > 80:
            insights.append(('info', f"**{col}** : 2 valeurs = {round(top2)}% des données."))
        else:
            insights.append(('good', f"**{col}** : {len(vc)} catégories bien réparties."))
    if dates and measures:
        try:
            ts = df[[dates[0], measures[0]]].copy()
            ts[dates[0]] = pd.to_datetime(ts[dates[0]], errors='coerce')
            ts = ts.dropna().sort_values(dates[0])
            ts[measures[0]] = pd.to_numeric(ts[measures[0]], errors='coerce')
            if len(ts) > 3:
                mid = len(ts) // 2
                chg = pct_change(ts.iloc[mid:][measures[0]].mean(), ts.iloc[:mid][measures[0]].mean())
                if chg is not None:
                    d = "en hausse" if chg > 0 else "en baisse"
                    insights.append(('good' if chg > 0 else 'alert', f"Tendance **{measures[0]}** : {d} de {abs(round(chg,1))}%."))
        except Exception: pass
    insights.append(('info', f"Domaine : **{domain}** · {total:,} lignes · {len(measures)} mesure(s) · {len(categories)} catégorie(s) · {len(dates)+len(periods)} colonne(s) temporelle(s)."))
    return insights

# ══ SIDEBAR ══════════════════════════════════════════════════════

saved_cfg = load_config()

with st.sidebar:
    st.markdown("### 📁 Importer les données")
    uploaded = st.file_uploader("Fichier Excel ou CSV", type=["xlsx","xls","csv"])
    df_raw, clean_rapport = None, []

    if uploaded:
        fb = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()
        try:
            if ext in ['xlsx','xls']:
                xl = pd.ExcelFile(BytesIO(fb))
                sheet = st.selectbox("Feuille", xl.sheet_names) if len(xl.sheet_names) > 1 else xl.sheet_names[0]
                df_loaded = load_excel_sheet(fb, sheet)
            else:
                df_loaded = load_csv_smart(fb)
            if df_loaded is not None:
                df_raw, clean_rapport = clean_dataframe(df_loaded)
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

    if df_raw is not None:
        auto_meas, auto_cat, auto_dates, auto_periods, auto_ign = auto_classify(df_raw.copy())
        file_key = uploaded.name
        cfg = saved_cfg.get(file_key, {})
        all_cols = list(df_raw.columns)
        def valid(lst): return [c for c in lst if c in all_cols]
        init_meas    = valid(cfg.get("measures",   auto_meas))
        init_cat     = valid(cfg.get("categories", auto_cat))
        init_dates   = valid(cfg.get("dates",      auto_dates))
        init_periods = valid(cfg.get("periods",    auto_periods))
        st.success(f"✅ {len(df_raw):,} lignes · {len(df_raw.columns)} colonnes")
        if clean_rapport:
            with st.expander("🔧 Nettoyage appliqué"):
                for r in clean_rapport: st.caption(f"• {r}")
        if auto_ign: st.caption(f"Ignorées : {', '.join(auto_ign[:4])}{'…' if len(auto_ign)>4 else ''}")
        st.divider()
        st.markdown("### ⚙️ Configuration des colonnes")
        measures_sel   = st.multiselect("📊 Mesures",    all_cols, default=init_meas,    key="sel_meas")
        categories_sel = st.multiselect("🏷️ Catégories", all_cols, default=init_cat,     key="sel_cat")
        dates_sel      = st.multiselect("📅 Dates",      all_cols, default=init_dates,   key="sel_dates")
        periods_sel    = st.multiselect("📆 Périodes",   all_cols, default=init_periods, key="sel_periods")
        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("💾 Sauvegarder", use_container_width=True):
                saved_cfg[file_key] = {"measures":measures_sel,"categories":categories_sel,"dates":dates_sel,"periods":periods_sel}
                save_config(saved_cfg); st.success("✅ Sauvegardé !")
        with col_reset:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                if file_key in saved_cfg: del saved_cfg[file_key]; save_config(saved_cfg)
                st.rerun()
        st.divider()
        st.markdown("### 🔽 Filtres")
        filters = {}
        for col in categories_sel[:4]:
            if col not in df_raw.columns: continue
            vals = sorted(df_raw[col].dropna().astype(str).unique().tolist())
            if 2 <= len(vals) <= 80:
                sel = st.multiselect(col, vals, default=[], key=f"f_{col}")
                if sel: filters[col] = sel

# ══ MAIN ══════════════════════════════════════════════════════════

if df_raw is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px">
      <div style="font-size:56px">📊</div>
      <h2 style="color:#1e2d3d;margin:16px 0 8px">Tableau de bord</h2>
      <p style="color:#666;font-size:15px;max-width:480px;margin:0 auto">
        Importez votre fichier Excel ou CSV dans la barre latérale.
      </p>
    </div>""", unsafe_allow_html=True)
    for col, icon, lbl in zip(st.columns(4),["📈","⚙️","👥","📦"],["Financier","Opérationnel","RH","Stocks & Ventes"]):
        with col:
            st.markdown(f"""<div style="background:white;border-radius:12px;padding:20px;text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.06)"><div style="font-size:28px">{icon}</div>
            <p style="font-size:13px;color:#555;margin:8px 0 0;font-weight:500">{lbl}</p></div>""",
            unsafe_allow_html=True)
    st.stop()

df = df_raw.copy()
for col, vals in filters.items():
    if col in df.columns: df = df[df[col].astype(str).isin(vals)]

measures   = [c for c in measures_sel   if c in df.columns]
categories = [c for c in categories_sel if c in df.columns]
dates      = [c for c in dates_sel      if c in df.columns]
periods    = [c for c in periods_sel    if c in df.columns]
domain     = detect_domain(df)

DOMAIN_ICONS = {'Financier':'💰','Commercial':'🤝','RH':'👥','Stocks':'📦','Opérationnel':'⚙️','Énergie':'⚡','Informatique':'💻','Général':'📊'}
d_icon = DOMAIN_ICONS.get(domain, '📊')

# ── EN-TÊTE — VERSION CORRIGÉE SANS F-STRING HTML IMBRIQUÉ ──────────────────

file_name_safe = uploaded.name.replace('<','').replace('>','').replace('"','').replace("'",'')
filtre_info    = f" · {len(df_raw)-len(df):,} exclus par filtres" if filters else ""

header_html = (
    '<div style="background:#1e2d3d;padding:18px 24px;border-radius:14px;margin-bottom:20px;'
    'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">'
    '<div>'
    f'<div style="color:white;font-size:19px;font-weight:700">{d_icon} Tableau de bord — {file_name_safe}</div>'
    f'<div style="color:#8899aa;font-size:12px;margin-top:3px">'
    f'{len(df):,} enregistrements · {len(df.columns)} colonnes · Domaine : {domain}{filtre_info}'
    '</div></div>'
    '<div style="background:#c0392b;color:white;padding:7px 16px;border-radius:8px;font-size:12px;font-weight:600">'
    'Tableau de bord</div></div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────────────────────────

kpi_meas = measures[:4]
kpi_grid = st.columns(len(kpi_meas) + 1)
with kpi_grid[0]:
    st.metric("Enregistrements", f"{len(df):,}", delta=f"{len(df_raw)-len(df):,} filtrés" if filters else None)
for i, col in enumerate(kpi_meas):
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals) == 0: continue
    total_v, mean_v = vals.sum(), vals.mean()
    if filters:
        vals_all = pd.to_numeric(df_raw[col], errors='coerce').dropna()
        chg = pct_change(total_v, vals_all.sum())
        delta_str = f"{round(chg,1)}% vs total" if chg is not None else None
    else:
        delta_str = f"Moy : {fmt(mean_v)}"
    with kpi_grid[i+1]:
        st.metric(col[:22], fmt(total_v), delta=delta_str)

st.markdown("<div style='margin:6px 0'></div>", unsafe_allow_html=True)

# ── ANALYSE BUSINESS ─────────────────────────────────────────────────────────

insights = analyse_business(df, measures, categories, dates, periods, domain)
with st.expander("💡 Analyse automatique", expanded=True):
    css_map = {'good':'insight-good','alert':'insight-alert','warn':'insight-warn','info':'insight-info'}
    for kind, msg in insights:
        st.markdown(f'<div class="{css_map.get(kind,"insight-info")}">{msg}</div>', unsafe_allow_html=True)

st.divider()

# ── ONGLETS ──────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "🔍 Analyse détaillée", "🗂️ Données"])

with tab1:
    show_cats = [c for c in categories if 2 <= df[c].nunique() <= 30][:6]
    if show_cats:
        st.markdown('<div class="section-title">Répartitions</div>', unsafe_allow_html=True)
        for pair in [show_cats[i:i+2] for i in range(0,len(show_cats),2)]:
            gcols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with gcols[ci]:
                    try:
                        counts = df[col].astype(str).value_counts().head(10).reset_index()
                        counts.columns = [col,'Nombre']
                        counts['%'] = (counts['Nombre']/counts['Nombre'].sum()*100).round(1)
                        if len(counts) <= 6:
                            fig = px.pie(counts, names=col, values='Nombre', color_discrete_sequence=COLORS, hole=0.5, title=col)
                            fig.update_traces(textinfo='percent+label', textposition='inside')
                        else:
                            fig = px.bar(counts, x='Nombre', y=col, orientation='h', color=col,
                                         color_discrete_sequence=COLORS, title=col, text='%')
                            fig.update_traces(texttemplate='%{text}%', textposition='outside')
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        chart_style(fig)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception: st.caption(f"Impossible d'afficher {col}")

    time_shown = False
    if dates and measures:
        st.markdown('<div class="section-title">Évolution dans le temps</div>', unsafe_allow_html=True)
        try:
            ts_g = build_time_series(df, dates[0], measures[0])
            if len(ts_g) > 1:
                fig_t = px.area(ts_g, x=dates[0], y=measures[0], color_discrete_sequence=[COLORS[0]], title=f"Évolution — {measures[0]}")
                fig_t.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
                chart_style(fig_t, h=280)
                st.plotly_chart(fig_t, use_container_width=True)
                time_shown = True
        except Exception as e: st.warning(f"Graphique temporel : {e}")

    if not time_shown and periods and measures:
        st.markdown('<div class="section-title">Évolution par période</div>', unsafe_allow_html=True)
        try:
            ts_g = build_time_series(df, periods[0], measures[0], is_period=True)
            if len(ts_g) > 1:
                fig_t = px.bar(ts_g, x=periods[0], y=measures[0], color_discrete_sequence=[COLORS[0]],
                               title=f"{measures[0]} par {periods[0]}", text=measures[0])
                fig_t.update_traces(texttemplate='%{text:.3s}', textposition='outside', marker_line_width=0)
                chart_style(fig_t, h=280)
                st.plotly_chart(fig_t, use_container_width=True)
        except Exception as e: st.warning(f"Graphique période : {e}")

    if show_cats and measures:
        st.markdown('<div class="section-title">Classement</div>', unsafe_allow_html=True)
        try:
            grp = df.groupby(show_cats[0])[measures[0]].sum().reset_index().sort_values(measures[0], ascending=False)
            grp[measures[0]] = pd.to_numeric(grp[measures[0]], errors='coerce')
            tot = grp[measures[0]].sum()
            grp['%'] = (grp[measures[0]]/tot*100).round(1) if tot != 0 else 0
            c1, c2 = st.columns(2)
            for col_out, data, title, ascending in [
                (c1, grp.head(8), f"Top — {show_cats[0]}", False),
                (c2, grp.tail(8).sort_values(measures[0]), f"Bas — {show_cats[0]}", True)
            ]:
                with col_out:
                    fig = px.bar(data, x=measures[0], y=show_cats[0], orientation='h',
                                 color=show_cats[0], color_discrete_sequence=COLORS if not ascending else COLORS[::-1],
                                 title=title, text='%')
                    fig.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    chart_style(fig, h=320)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.warning(f"Classement : {e}")

with tab2:
    good_cats = [c for c in categories if 2 <= df[c].nunique() <= 50]
    if good_cats and measures:
        st.markdown('<div class="section-title">Analyse croisée</div>', unsafe_allow_html=True)
        h1,h2,h3,h4 = st.columns(4)
        with h1: x_col = st.selectbox("Catégorie", good_cats, key="xc")
        with h2: y_col = st.selectbox("Mesure", measures, key="yc")
        with h3: agg   = st.selectbox("Calcul", ["Somme","Moyenne","Nombre","Maximum","Minimum"], key="ag")
        with h4: top_n = st.slider("Top N", 5, 25, 10, key="topn")
        try:
            agg_map = {"Somme":"sum","Moyenne":"mean","Nombre":"count","Maximum":"max","Minimum":"min"}
            grp2 = df.groupby(x_col)[y_col].agg(agg_map[agg]).reset_index().sort_values(y_col, ascending=False).head(top_n)
            fig2 = px.bar(grp2, x=x_col, y=y_col, color=x_col, color_discrete_sequence=COLORS,
                          title=f"{agg} de {y_col} par {x_col}", text=y_col)
            fig2.update_traces(texttemplate='%{text:.3s}', textposition='outside')
            chart_style(fig2, h=360)
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e: st.warning(f"Analyse croisée : {e}")

    all_time = dates + periods
    if all_time and measures:
        st.markdown('<div class="section-title">Évolution personnalisée</div>', unsafe_allow_html=True)
        h1,h2,h3 = st.columns(3)
        with h1: tc  = st.selectbox("Axe temporel", all_time, key="tc2")
        with h2: vc  = st.selectbox("Mesure", measures, key="vc2")
        with h3: cc  = st.selectbox("Découper par", ["Aucun"] + good_cats, key="cc2") if good_cats else "Aucun"
        try:
            is_p = tc in periods
            ts_g = build_time_series(df, tc, vc, col_group=cc if cc != "Aucun" else None, is_period=is_p)
            if cc != "Aucun" and cc in ts_g.columns:
                fig3 = px.line(ts_g, x=tc, y=vc, color=cc, color_discrete_sequence=COLORS, title=f"{vc} par {cc}")
                fig3.update_layout(showlegend=True)
            else:
                fig3 = px.area(ts_g, x=tc, y=vc, color_discrete_sequence=[COLORS[0]], title=f"{vc}")
                fig3.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig3, h=320)
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e: st.warning(f"Évolution : {e}")

    if len(good_cats) >= 2 and measures:
        st.markdown('<div class="section-title">Comparaison croisée</div>', unsafe_allow_html=True)
        h1,h2,h3 = st.columns(3)
        with h1: c1s = st.selectbox("Catégorie 1", good_cats, key="c1s")
        with h2:
            rem = [c for c in good_cats if c != c1s]
            c2s = st.selectbox("Catégorie 2", rem, key="c2s") if rem else None
        with h3: vs = st.selectbox("Mesure", measures, key="vs2")
        if c2s:
            try:
                grp4 = df.groupby([c1s, c2s])[vs].sum().reset_index()
                fig4 = px.bar(grp4, x=c1s, y=vs, color=c2s, color_discrete_sequence=COLORS,
                              barmode='group', title=f"{vs} — {c1s} × {c2s}")
                chart_style(fig4, h=360).update_layout(showlegend=True)
                st.plotly_chart(fig4, use_container_width=True)
            except Exception as e: st.warning(f"Comparaison : {e}")

with tab3:
    c1, c2 = st.columns([3,1])
    with c1: search = st.text_input("Rechercher", "", key="search", placeholder="Mot-clé…")
    with c2: sort_col = st.selectbox("Trier par", ["—"] + list(df.columns), key="sort_col")
    disp = df.copy()
    if search:
        try:
            mask = disp.astype(str).apply(lambda c: c.str.contains(search, case=False, na=False)).any(axis=1)
            disp = disp[mask]
        except Exception: pass
    if sort_col != "—":
        try: disp = disp.sort_values(sort_col, ascending=False)
        except Exception: pass
    st.dataframe(disp, height=440, use_container_width=True)
    st.caption(f"{len(disp):,} lignes affichées sur {len(df):,}")
    c1, c2 = st.columns(2)
    with c1:
        try:
            buf = BytesIO(); disp.to_excel(buf, index=False)
            st.download_button("📥 Exporter Excel", buf.getvalue(), "tableau_de_bord.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception: st.warning("Export Excel indisponible.")
    with c2:
        try:
            st.download_button("📥 Exporter CSV",
                               disp.to_csv(index=False, sep=';').encode('utf-8-sig'),
                               "tableau_de_bord.csv", "text/csv")
        except Exception: st.warning("Export CSV indisponible.")

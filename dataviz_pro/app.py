import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import json, os, re, unicodedata

# ══════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Analytix Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — ROUGE & BLANC PREMIUM
# ══════════════════════════════════════════════════════════════════
CRIMSON      = "#C0392B"
CRIMSON_DEEP = "#922B21"
CRIMSON_SOFT = "#E8DEDC"
CRIMSON_PALE = "#FDF5F4"
SLATE        = "#1A1F2C"
SLATE_MID    = "#3D4560"
MUTED        = "#8A94A6"
SNOW         = "#FAF9F8"
WHITE        = "#FFFFFF"

CHART_COLORS = [CRIMSON, "#185FA5", "#1D9E75", "#BA7517", "#8e44ad", "#0F6E56", "#d35400"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── GLOBAL ── */
html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
    color: {SLATE};
}}
[data-testid="stAppViewContainer"] {{
    background: {SNOW};
}}
[data-testid="stMain"] {{
    background: {SNOW};
}}
.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {{
    background: {WHITE} !important;
    border-right: 1px solid rgba(0,0,0,0.06) !important;
}}
[data-testid="stSidebar"] * {{
    color: {SLATE} !important;
}}
[data-testid="stSidebar"] .stMarkdown h3 {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: {MUTED} !important;
    padding: 16px 0 6px !important;
    border: none !important;
}}
[data-testid="stSidebar"] .stFileUploader {{
    background: {CRIMSON_PALE};
    border: 2px dashed rgba(192,57,43,0.3);
    border-radius: 12px;
    padding: 4px;
}}
[data-testid="stSidebar"] .stFileUploader label {{
    color: {CRIMSON} !important;
    font-weight: 500 !important;
}}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background: {CRIMSON_PALE} !important;
    color: {CRIMSON} !important;
    border: none !important;
}}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span {{
    color: {CRIMSON} !important;
}}
[data-testid="stSidebar"] .stButton button {{
    background: {WHITE};
    border: 1px solid rgba(0,0,0,0.1);
    color: {SLATE};
    border-radius: 8px;
    font-size: 12px;
    transition: all .18s;
}}
[data-testid="stSidebar"] .stButton button:hover {{
    border-color: {CRIMSON};
    color: {CRIMSON};
}}
[data-testid="stSidebar"] .stSelectbox select,
[data-testid="stSidebar"] [data-baseweb="select"] {{
    background: {WHITE} !important;
    border-color: rgba(0,0,0,0.08) !important;
    border-radius: 8px !important;
}}
[data-testid="stSidebar"] .stSuccess {{
    background: #E1F5EE !important;
    border: 1px solid #9FE1CB !important;
    color: #0F6E56 !important;
    border-radius: 10px !important;
}}
[data-testid="stSidebar"] .stSuccess p {{
    color: #0F6E56 !important;
}}

/* ── MAIN CONTENT ── */
.main-wrapper {{
    padding: 32px 40px 40px;
}}

/* ── PAGE HEADER ── */
.page-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28px;
}}
.page-title {{
    font-family: 'DM Serif Display', Georgia, serif;
    font-size: 30px;
    color: {SLATE};
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin: 0 0 5px;
}}
.page-sub {{
    font-size: 13.5px;
    color: {MUTED};
    font-weight: 400;
    margin: 0;
}}
.domain-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: {CRIMSON};
    color: white;
    padding: 6px 16px;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 500;
    letter-spacing: 0.2px;
}}

/* ── DROP ZONE ── */
.dropzone {{
    border: 2px dashed rgba(192,57,43,0.3);
    border-radius: 16px;
    background: {CRIMSON_PALE};
    padding: 52px 40px;
    text-align: center;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    transition: all .25s;
}}
.dropzone::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(192,57,43,0.06) 0%, transparent 70%);
    pointer-events: none;
}}
.dz-icon-wrap {{
    width: 58px;
    height: 58px;
    background: white;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 18px;
    box-shadow: 0 4px 20px rgba(192,57,43,0.14);
    font-size: 26px;
}}
.dz-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: {SLATE};
    margin-bottom: 8px;
}}
.dz-sub {{
    font-size: 13px;
    color: {MUTED};
    line-height: 1.65;
    max-width: 460px;
    margin: 0 auto;
}}
.dz-formats {{
    display: flex;
    gap: 8px;
    justify-content: center;
    margin-top: 16px;
    flex-wrap: wrap;
}}
.dz-fmt {{
    font-size: 11px;
    font-weight: 500;
    padding: 4px 11px;
    border-radius: 20px;
    border: 1px solid rgba(192,57,43,0.2);
    color: {CRIMSON};
    background: white;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.3px;
}}

/* ── KPI CARDS ── */
.kpi-outer {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}}
.kpi-card {{
    background: {WHITE};
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 14px;
    padding: 22px 24px 20px;
    position: relative;
    overflow: hidden;
    transition: all .22s;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 2px 2px 0 0;
}}
.kpi-card.c-red::before   {{ background: {CRIMSON}; }}
.kpi-card.c-teal::before  {{ background: #1D9E75; }}
.kpi-card.c-amber::before {{ background: #BA7517; }}
.kpi-card.c-blue::before  {{ background: #185FA5; }}
.kpi-label {{
    font-size: 10.5px;
    font-weight: 600;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin-bottom: 10px;
}}
.kpi-value {{
    font-family: 'DM Serif Display', serif;
    font-size: 32px;
    color: {SLATE};
    letter-spacing: -1px;
    line-height: 1;
    margin-bottom: 10px;
}}
.kpi-delta {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 500;
    padding: 3px 9px;
    border-radius: 20px;
}}
.kpi-delta.up   {{ color: #0F6E56; background: #E1F5EE; }}
.kpi-delta.down {{ color: {CRIMSON}; background: {CRIMSON_PALE}; }}
.kpi-delta.neu  {{ color: {MUTED}; background: rgba(0,0,0,0.05); }}
.kpi-sub {{
    font-size: 11px;
    color: {MUTED};
    margin-top: 5px;
}}

/* ── SECTION TITLE ── */
.section-title {{
    font-family: 'DM Serif Display', serif;
    font-size: 16px;
    color: {SLATE};
    margin: 24px 0 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.section-title::before {{
    content: '';
    display: inline-block;
    width: 4px;
    height: 18px;
    background: {CRIMSON};
    border-radius: 2px;
}}

/* ── INSIGHT CARDS ── */
.insight-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 24px;
}}
.insight-card {{
    background: {WHITE};
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 14px;
    padding: 18px 20px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}}
.insight-icon {{
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 18px;
}}
.insight-icon.red   {{ background: {CRIMSON_PALE}; }}
.insight-icon.green {{ background: #E1F5EE; }}
.insight-icon.amber {{ background: #FAEEDA; }}
.insight-icon.blue  {{ background: #E6F1FB; }}
.insight-body {{ flex: 1; }}
.insight-title {{
    font-size: 13px;
    font-weight: 600;
    color: {SLATE};
    margin-bottom: 4px;
}}
.insight-text {{
    font-size: 12px;
    color: {MUTED};
    line-height: 1.6;
}}

/* ── CHART CARDS ── */
.chart-card {{
    background: {WHITE};
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 20px;
}}

/* ── STATUS BAR ── */
.status-bar {{
    background: {WHITE};
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 14px;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 16px;
}}
.status-items {{
    display: flex;
    gap: 20px;
    align-items: center;
}}
.status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
}}
.dot-green {{ background: #1D9E75; }}
.dot-amber {{ background: #BA7517; }}
.status-item {{
    font-size: 12px;
    color: {MUTED};
    display: flex;
    align-items: center;
}}

/* ── TABS ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: rgba(0,0,0,0.03);
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {MUTED} !important;
    border: none !important;
    padding: 8px 18px !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background: {WHITE} !important;
    color: {SLATE} !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-border"] {{
    display: none !important;
}}

/* ── METRICS override ── */
div[data-testid="stMetric"] {{
    background: {WHITE};
    border-radius: 14px;
    padding: 20px 22px;
    border: 1px solid rgba(0,0,0,0.06);
    border-top: 3px solid {CRIMSON};
}}
div[data-testid="stMetric"] label {{
    font-size: 10.5px !important;
    color: {MUTED} !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'DM Sans', sans-serif !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-family: 'DM Serif Display', serif !important;
    font-size: 28px !important;
    color: {SLATE} !important;
    letter-spacing: -0.8px !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
    font-size: 12px !important;
}}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{
    background: {WHITE};
    border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 14px !important;
    margin-bottom: 20px;
}}
[data-testid="stExpander"] summary {{
    font-family: 'DM Serif Display', serif;
    font-size: 15px;
    color: {SLATE};
}}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {{
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.06) !important;
}}

/* ── DOWNLOAD BUTTONS ── */
.stDownloadButton button {{
    background: {CRIMSON} !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    transition: all .18s !important;
}}
.stDownloadButton button:hover {{
    background: {CRIMSON_DEEP} !important;
    box-shadow: 0 4px 14px rgba(192,57,43,0.3) !important;
    transform: translateY(-1px);
}}

/* ── SELECT / INPUT styling ── */
[data-baseweb="select"] > div {{
    border-color: rgba(0,0,0,0.1) !important;
    border-radius: 9px !important;
    background: {WHITE} !important;
}}
[data-baseweb="select"] > div:focus-within {{
    border-color: {CRIMSON} !important;
    box-shadow: 0 0 0 2px rgba(192,57,43,0.12) !important;
}}
[data-testid="stTextInput"] input {{
    border-color: rgba(0,0,0,0.1) !important;
    border-radius: 9px !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: {CRIMSON} !important;
    box-shadow: 0 0 0 2px rgba(192,57,43,0.12) !important;
}}

/* ── SLIDERS ── */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stThumbValue"] {{
    background: {CRIMSON} !important;
    color: white !important;
}}
[data-testid="stSlider"] [role="slider"] {{
    background: {CRIMSON} !important;
    border-color: {CRIMSON} !important;
}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  CONSTANTS & CONFIG
# ══════════════════════════════════════════════════════════════════
CONFIG_FILE = "analytix_config.json"

NULL_VALUES = {
    'na','n/a','n.a','n.a.','na.','nan','none','null','nil','void',
    'nd','n.d','n.d.','-','--','---','—','–','_','__','?',
    'vide','manquant','missing','empty','inconnu','unknown','nr','ns','nc'
}

DOMAIN_META = {
    'Financier':    {'icon': '💰', 'color': CRIMSON,   'keys': ['montant','revenu','budget','charge','salaire','marge','prix','facture']},
    'Commercial':   {'icon': '🤝', 'color': '#185FA5', 'keys': ['client','contrat','commande','vente','region','zone','agence','ca']},
    'RH':           {'icon': '👥', 'color': '#1D9E75', 'keys': ['employe','effectif','absence','conge','departement','agent','matricule']},
    'Stocks':       {'icon': '📦', 'color': '#BA7517', 'keys': ['stock','produit','quantite','inventaire','article','entrepot']},
    'Opérationnel': {'icon': '⚙️', 'color': '#8e44ad', 'keys': ['production','qualite','delai','incident','maintenance','panne','consommation']},
    'Énergie':      {'icon': '⚡', 'color': '#d35400', 'keys': ['energie','kwh','electricite','gaz','puissance','compteur']},
    'Informatique': {'icon': '💻', 'color': '#16a085', 'keys': ['pc','ordinateur','imprimante','bureau','portable','processeur']},
}

ID_KW   = ['id','n°','no','num','numero','numéro','code','ref','reference','matricule',
            'identifiant','contrat','client','compte','dossier','facture','commande',
            'ticket','order','invoice','key','serial','siren','siret']
MEAS_KW = ['montant','somme','total','chiffre','revenu','ca','budget','charge','salaire',
           'prix','cout','coût','marge','consommation','quantite','volume','poids',
           'duree','durée','heure','taux','valeur','amount','sales','revenue','cost',
           'profit','depense','recette','solde','stock','energie','puissance','score',
           'kpi','indicateur','kwh','effectif','nombre','count','qte','qty']

# ══════════════════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════════════════
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

def normalize_text(s):
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                       if unicodedata.category(c) != 'Mn').lower().strip()
    except Exception:
        return str(s).lower().strip()

def normalize_col(c):
    return normalize_text(c).replace(' ','').replace('_','').replace('-','').replace('°','')

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

# ══════════════════════════════════════════════════════════════════
#  DATA PROCESSING
# ══════════════════════════════════════════════════════════════════
@st.cache_data
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
    if len(df) < before:
        rapport.append(f"🗑️ {before - len(df)} lignes vides supprimées.")

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
    if conv_num > 0:  rapport.append(f"🔢 {conv_num} colonne(s) convertie(s) en nombres.")
    if conv_date > 0: rapport.append(f"📅 {conv_date} colonne(s) convertie(s) en dates.")
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
    scores = {d: sum(1 for k in meta['keys'] if k in txt) for d, meta in DOMAIN_META.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Général'

def quality_score(df):
    completeness = (1 - df.isna().mean().mean()) * 100
    if completeness >= 98: return "A+", completeness
    if completeness >= 95: return "A",  completeness
    if completeness >= 90: return "B+", completeness
    if completeness >= 80: return "B",  completeness
    return "C", completeness

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

def analyse_insights(df, measures, categories, dates, periods, domain):
    insights = []
    total = len(df)
    missing_pct = df.isna().mean()
    bad = missing_pct[missing_pct > 0.05]
    if bad.empty:
        insights.append(('green', '✓', 'Qualité parfaite', f"Aucune valeur manquante sur {total:,} enregistrements."))
    else:
        w = bad.idxmax()
        insights.append(('red', '⚠', 'Données incomplètes', f"{w} — {round(bad[w]*100,1)}% de valeurs manquantes."))
    for col in measures[:1]:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) < 2: continue
        mean_v, max_v, total_v = vals.mean(), vals.max(), vals.sum()
        top_pct = (max_v - mean_v) / abs(mean_v) * 100 if mean_v != 0 else 0
        if top_pct > 300:
            insights.append(('red', '⚠', 'Anomalie détectée', f"Max de {col} ({fmt(max_v)}) anormalement élevé vs moyenne ({fmt(mean_v)})."))
        else:
            insights.append(('green', '↑', 'Mesure principale', f"{col} — total {fmt(total_v)}, moyenne {fmt(mean_v)}."))
    for col in categories[:1]:
        vc = df[col].value_counts()
        if len(vc) < 2: continue
        top_share = vc.iloc[0] / total * 100
        if top_share > 60:
            insights.append(('amber', '◉', 'Concentration', f"{col} : « {vc.index[0]} » représente {round(top_share)}% des données."))
        else:
            insights.append(('blue', '≡', 'Distribution', f"{col} : {len(vc)} catégories bien réparties."))
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
                    icon = "↑" if chg > 0 else "↓"
                    kind = "green" if chg > 0 else "red"
                    insights.append((kind, icon, 'Tendance', f"{measures[0]} {d} de {abs(round(chg,1))}% sur la période."))
        except Exception: pass
    return insights[:4]

# ══════════════════════════════════════════════════════════════════
#  CHART HELPERS
# ══════════════════════════════════════════════════════════════════
def apply_chart_style(fig, h=320, legend=False):
    fig.update_layout(
        margin=dict(t=20, b=20, l=10, r=10),
        height=h,
        showlegend=legend,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans, sans-serif', size=11, color=MUTED),
        title=None,
        xaxis=dict(showgrid=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', showline=False, zeroline=False),
    )
    return fig

def make_area_chart(ts_g, x_col, y_col):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts_g[x_col], y=ts_g[y_col],
        mode='lines+markers',
        line=dict(color=CRIMSON, width=2.5, shape='spline'),
        fill='tozeroy',
        fillcolor='rgba(192,57,43,0.08)',
        marker=dict(size=5, color=CRIMSON, line=dict(width=2, color='white')),
        hovertemplate='<b>%{y:,.0f}</b><extra></extra>',
    ))
    return apply_chart_style(fig, h=260)

def make_bar_chart(grp, x_col, y_col, color=None, h=300, text_col=None):
    fig = px.bar(
        grp, x=x_col, y=y_col,
        color=color if color else x_col,
        color_discrete_sequence=CHART_COLORS,
        text=text_col if text_col else y_col,
    )
    if text_col:
        fig.update_traces(texttemplate='%{text}%', textposition='outside', textfont_size=11)
    else:
        fig.update_traces(texttemplate='%{text:.3s}', textposition='outside', textfont_size=11)
    fig.update_traces(marker_line_width=0)
    return apply_chart_style(fig, h=h)

def make_hbar_chart(grp, x_col, y_col, ascending=False, h=320):
    fig = px.bar(
        grp, x=y_col, y=x_col, orientation='h',
        color=x_col,
        color_discrete_sequence=CHART_COLORS if not ascending else CHART_COLORS[::-1],
        text=grp[y_col].apply(fmt),
    )
    fig.update_traces(textposition='outside', textfont_size=11, marker_line_width=0)
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return apply_chart_style(fig, h=h)

def make_donut(df_cat, col, measures):
    counts = df_cat[col].astype(str).value_counts().head(8).reset_index()
    counts.columns = [col, 'Nombre']
    if measures:
        try:
            mv = df_cat.groupby(col)[measures[0]].sum().reset_index()
            mv.columns = [col, 'Valeur']
            fig = px.pie(mv.head(8), names=col, values='Valeur',
                         color_discrete_sequence=CHART_COLORS, hole=0.55)
        except Exception:
            fig = px.pie(counts, names=col, values='Nombre',
                         color_discrete_sequence=CHART_COLORS, hole=0.55)
    else:
        fig = px.pie(counts, names=col, values='Nombre',
                     color_discrete_sequence=CHART_COLORS, hole=0.55)
    fig.update_traces(textinfo='percent', textposition='inside',
                      marker=dict(line=dict(color='white', width=2)))
    return apply_chart_style(fig, h=280, legend=True)

# ══════════════════════════════════════════════════════════════════
#  HTML COMPONENTS
# ══════════════════════════════════════════════════════════════════
def render_header(file_name, n_rows, n_cols, domain, filters):
    meta = DOMAIN_META.get(domain, {'icon': '📊', 'color': CRIMSON})
    icon = meta['icon']
    filtre_info = f" · {sum(len(v) for v in filters.values())} filtre(s) actif(s)" if filters else ""
    safe_name = file_name.replace('<','').replace('>','').replace('"','')
    st.markdown(f"""
    <div style="background:{SLATE};padding:20px 28px;border-radius:16px;
         display:flex;justify-content:space-between;align-items:center;
         flex-wrap:wrap;gap:12px;margin-bottom:24px;">
      <div>
        <div style="color:white;font-family:'DM Serif Display',serif;
             font-size:20px;letter-spacing:-0.3px;">{icon} {safe_name}</div>
        <div style="color:{MUTED};font-size:12px;margin-top:4px;font-family:'DM Sans',sans-serif;">
          {n_rows:,} enregistrements · {n_cols} colonnes · Domaine : {domain}{filtre_info}
        </div>
      </div>
      <div style="background:{CRIMSON};color:white;padding:8px 18px;
           border-radius:9px;font-size:12.5px;font-weight:500;
           font-family:'DM Sans',sans-serif;letter-spacing:0.2px;">
        {domain}
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi(label, value, delta_str, delta_type="neu", color_class="c-red", sub=""):
    delta_html = ""
    if delta_str:
        arrow = "▲" if delta_type == "up" else ("▼" if delta_type == "down" else "—")
        delta_html = f'<div class="kpi-delta {delta_type}">{arrow} {delta_str}</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card {color_class}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
      {sub_html}
    </div>"""

def render_insights(insights):
    icon_map = {'green': '✓', 'red': '⚠', 'amber': '◉', 'blue': '≡'}
    cards = ""
    for kind, icon, title, text in insights:
        cards += f"""
        <div class="insight-card">
          <div class="insight-icon {kind}">{icon}</div>
          <div class="insight-body">
            <div class="insight-title">{title}</div>
            <div class="insight-text">{text}</div>
          </div>
        </div>"""
    st.markdown(f'<div class="insight-grid">{cards}</div>', unsafe_allow_html=True)

def render_section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def render_status(domain, n_rows, measures):
    q_label, q_pct = quality_score(st.session_state.get('df', pd.DataFrame()))
    bar_w = int(q_pct)
    st.markdown(f"""
    <div class="status-bar">
      <div class="status-items">
        <div class="status-item"><span class="status-dot dot-green"></span>Moteur analytique actif</div>
        <div class="status-item"><span class="status-dot dot-green"></span>Nettoyage automatique</div>
        <div class="status-item"><span class="status-dot dot-green"></span>{len(measures)} mesure(s) détectée(s)</div>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <div style="font-size:12px;color:{MUTED};font-family:'DM Sans',sans-serif;">Qualité données</div>
        <div style="width:90px;height:5px;background:{CRIMSON_SOFT};border-radius:3px;overflow:hidden;">
          <div style="width:{bar_w}%;height:100%;background:{CRIMSON};border-radius:3px;"></div>
        </div>
        <div style="font-size:13px;font-weight:600;color:{CRIMSON};
             font-family:'DM Mono',monospace;">{q_label} · {q_pct:.0f}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
saved_cfg = load_config()

with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0 20px;">
      <div style="width:34px;height:34px;background:#C0392B;border-radius:8px;
           display:flex;align-items:center;justify-content:center;">
        <span style="font-size:16px;">📊</span>
      </div>
      <div>
        <div style="font-family:'DM Serif Display',serif;font-size:17px;
             color:#1A1F2C;letter-spacing:-0.3px;">Analytix</div>
        <div style="font-size:10px;font-weight:600;color:#C0392B;
             letter-spacing:0.5px;text-transform:uppercase;">Pro Edition</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📁 Importer les données")
    uploaded = st.file_uploader(
        "Fichier Excel ou CSV",
        type=["xlsx","xls","csv"],
        label_visibility="collapsed",
        help="Supporte .xlsx, .xls, .csv — détection automatique du format"
    )

    df_raw, clean_rapport = None, []

    if uploaded:
        fb = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()
        try:
            if ext in ['xlsx','xls']:
                xl = pd.ExcelFile(BytesIO(fb))
                if len(xl.sheet_names) > 1:
                    sheet = st.selectbox("📋 Feuille", xl.sheet_names)
                else:
                    sheet = xl.sheet_names[0]
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

        st.success(f"✅ {len(df_raw):,} lignes · {len(df_raw.columns)} colonnes chargées")

        if clean_rapport:
            with st.expander("🔧 Transformations appliquées"):
                for r in clean_rapport:
                    st.caption(r)
        if auto_ign:
            st.caption(f"Colonnes ignorées : {', '.join(auto_ign[:5])}{'…' if len(auto_ign)>5 else ''}")

        st.divider()
        st.markdown("### ⚙️ Configuration")
        measures_sel   = st.multiselect("📊 Mesures (numériques)",  all_cols, default=init_meas,    key="sel_meas")
        categories_sel = st.multiselect("🏷️ Catégories (texte)",    all_cols, default=init_cat,     key="sel_cat")
        dates_sel      = st.multiselect("📅 Dates",                 all_cols, default=init_dates,   key="sel_dates")
        periods_sel    = st.multiselect("📆 Périodes (num/text)",   all_cols, default=init_periods, key="sel_periods")

        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("💾 Sauvegarder", use_container_width=True):
                saved_cfg[file_key] = {
                    "measures": measures_sel, "categories": categories_sel,
                    "dates": dates_sel, "periods": periods_sel
                }
                save_config(saved_cfg)
                st.success("✅ Config sauvegardée !")
        with col_reset:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                if file_key in saved_cfg:
                    del saved_cfg[file_key]; save_config(saved_cfg)
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

# ══════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════════
if df_raw is None:
    st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px;">
      <div style="font-family:'DM Serif Display',serif;font-size:42px;
           color:#1A1F2C;letter-spacing:-1px;line-height:1.1;margin-bottom:12px;">
        Analysez <span style="color:#C0392B;">n'importe quel</span> fichier
      </div>
      <div style="font-size:16px;color:#8A94A6;max-width:520px;
           margin:0 auto;line-height:1.65;">
        Déposez un CSV ou Excel — le modèle détecte automatiquement le domaine,
        nettoie les données et génère les visualisations adaptées.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="dropzone">
      <div class="dz-icon-wrap">📁</div>
      <div class="dz-title">Glissez votre fichier ici</div>
      <div class="dz-sub">
        Détection automatique du domaine métier (Financier, RH, Commercial, Stocks…)<br>
        Nettoyage intelligent · Classification · Visualisations adaptées · Insights IA
      </div>
      <div class="dz-formats">
        <span class="dz-fmt">.xlsx</span>
        <span class="dz-fmt">.xls</span>
        <span class="dz-fmt">.csv</span>
        <span class="dz-fmt">.tsv</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    features = [
        ("💰", "Financier", "Montants, marges, budgets, CA, charges"),
        ("🤝", "Commercial", "Clients, contrats, régions, ventes"),
        ("👥", "Ressources humaines", "Effectifs, absences, départements"),
        ("📦", "Stocks & Opérationnel", "Inventaires, production, qualité"),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div style="background:white;border:1px solid rgba(0,0,0,0.06);
                 border-radius:14px;padding:20px;text-align:center;
                 border-top:3px solid {CRIMSON};">
              <div style="font-size:28px;margin-bottom:10px;">{icon}</div>
              <div style="font-family:'DM Serif Display',serif;font-size:14px;
                   color:{SLATE};margin-bottom:6px;">{title}</div>
              <div style="font-size:12px;color:{MUTED};line-height:1.5;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════
#  APPLY FILTERS
# ══════════════════════════════════════════════════════════════════
df = df_raw.copy()
for col, vals in filters.items():
    if col in df.columns:
        df = df[df[col].astype(str).isin(vals)]

measures   = [c for c in measures_sel   if c in df.columns]
categories = [c for c in categories_sel if c in df.columns]
dates      = [c for c in dates_sel      if c in df.columns]
periods    = [c for c in periods_sel    if c in df.columns]
domain     = detect_domain(df)

st.session_state['df'] = df

# ══════════════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)
render_header(uploaded.name, len(df), len(df.columns), domain, filters)

# ── KPI CARDS ────────────────────────────────────────────────────
kpi_meas = measures[:3]
kpi_colors = ["c-red", "c-teal", "c-amber", "c-blue"]

kpi_html = '<div class="kpi-outer">'
# Records card
n_filtered = len(df_raw) - len(df)
kpi_html += render_kpi(
    "Enregistrements", f"{len(df):,}",
    f"{n_filtered:,} filtrés" if filters else None,
    "neu" if not filters else "down",
    "c-red",
    f"sur {len(df_raw):,} total"
)
# Measure cards
for i, col in enumerate(kpi_meas):
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals) == 0: continue
    total_v, mean_v = vals.sum(), vals.mean()
    if filters:
        vals_all = pd.to_numeric(df_raw[col], errors='coerce').dropna()
        chg = pct_change(total_v, vals_all.sum())
        delta_str  = f"{round(abs(chg),1)}% vs total" if chg is not None else None
        delta_type = "up" if (chg or 0) > 0 else "down"
    else:
        delta_str  = None
        delta_type = "neu"
    kpi_html += render_kpi(
        col[:22], fmt(total_v),
        delta_str, delta_type,
        kpi_colors[(i+1) % len(kpi_colors)],
        f"Moy : {fmt(mean_v)}"
    )
# Quality card
q_label, q_pct = quality_score(df)
kpi_html += render_kpi(
    "Score qualité", q_label,
    f"{q_pct:.0f}% complet",
    "up" if q_pct >= 95 else ("neu" if q_pct >= 80 else "down"),
    "c-blue",
    "analyse automatique"
)
kpi_html += '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)

# ── INSIGHTS ─────────────────────────────────────────────────────
insights = analyse_insights(df, measures, categories, dates, periods, domain)
if insights:
    render_section("Insights automatiques")
    render_insights(insights)

# ══════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📊  Vue d'ensemble", "🔍  Analyse détaillée", "🗂️  Données brutes"])

# ── TAB 1 : VUE D'ENSEMBLE ───────────────────────────────────────
with tab1:
    show_cats = [c for c in categories if 2 <= df[c].nunique() <= 30][:4]

    # Time series
    time_shown = False
    if dates and measures:
        render_section("Évolution temporelle")
        try:
            ts_g = build_time_series(df, dates[0], measures[0])
            if len(ts_g) > 1:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                fig_t = make_area_chart(ts_g, dates[0], measures[0])
                st.plotly_chart(fig_t, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
                time_shown = True
        except Exception as e:
            st.warning(f"Graphique temporel : {e}")

    if not time_shown and periods and measures:
        render_section("Évolution par période")
        try:
            ts_g = build_time_series(df, periods[0], measures[0], is_period=True)
            if len(ts_g) > 1:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                fig_t = make_bar_chart(ts_g, periods[0], measures[0], h=280)
                st.plotly_chart(fig_t, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Graphique période : {e}")

    # Distributions
    if show_cats:
        render_section("Répartitions par catégorie")
        for pair in [show_cats[i:i+2] for i in range(0, len(show_cats), 2)]:
            gcols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with gcols[ci]:
                    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                    st.markdown(f"<div style='font-family:DM Serif Display,serif;font-size:14px;color:{SLATE};margin-bottom:12px;'>{col}</div>", unsafe_allow_html=True)
                    try:
                        if measures:
                            fig_d = make_donut(df, col, measures)
                        else:
                            counts = df[col].astype(str).value_counts().head(8).reset_index()
                            counts.columns = [col, 'Nombre']
                            fig_d = px.pie(counts, names=col, values='Nombre',
                                          color_discrete_sequence=CHART_COLORS, hole=0.5)
                            fig_d.update_traces(textinfo='percent', textposition='inside',
                                                marker=dict(line=dict(color='white', width=2)))
                            apply_chart_style(fig_d, h=280, legend=True)
                        st.plotly_chart(fig_d, use_container_width=True, config={'displayModeBar': False})
                    except Exception:
                        st.caption(f"Impossible d'afficher {col}")
                    st.markdown('</div>', unsafe_allow_html=True)

    # Ranking
    if show_cats and measures:
        render_section("Classement")
        try:
            grp = df.groupby(show_cats[0])[measures[0]].sum().reset_index()
            grp[measures[0]] = pd.to_numeric(grp[measures[0]], errors='coerce')
            tot = grp[measures[0]].sum()
            grp['%'] = (grp[measures[0]] / tot * 100).round(1) if tot != 0 else 0
            grp = grp.sort_values(measures[0], ascending=False)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown(f"<div style='font-family:DM Serif Display,serif;font-size:14px;color:{SLATE};margin-bottom:12px;'>Top — {show_cats[0]}</div>", unsafe_allow_html=True)
                top_grp = grp.head(8).copy()
                fig_top = make_hbar_chart(top_grp, show_cats[0], measures[0], h=340)
                st.plotly_chart(fig_top, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown(f"<div style='font-family:DM Serif Display,serif;font-size:14px;color:{SLATE};margin-bottom:12px;'>Bas — {show_cats[0]}</div>", unsafe_allow_html=True)
                bot_grp = grp.tail(8).sort_values(measures[0]).copy()
                fig_bot = px.bar(
                    bot_grp, x=measures[0], y=show_cats[0], orientation='h',
                    color=show_cats[0], color_discrete_sequence=CHART_COLORS[::-1],
                    text=bot_grp[measures[0]].apply(fmt),
                )
                fig_bot.update_traces(textposition='outside', marker_line_width=0)
                fig_bot.update_layout(yaxis={'categoryorder': 'total ascending'})
                apply_chart_style(fig_bot, h=340)
                st.plotly_chart(fig_bot, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Classement : {e}")

    if not show_cats and not measures and not dates and not periods:
        st.markdown(f"""
        <div style="text-align:center;padding:60px 20px;">
          <div style="font-size:40px;margin-bottom:14px;">⚙️</div>
          <div style="font-family:'DM Serif Display',serif;font-size:18px;color:{SLATE};margin-bottom:8px;">
            Configurez vos colonnes
          </div>
          <div style="font-size:13px;color:{MUTED};">
            Sélectionnez des mesures et catégories dans la barre latérale.
          </div>
        </div>""", unsafe_allow_html=True)

# ── TAB 2 : ANALYSE DÉTAILLÉE ────────────────────────────────────
with tab2:
    good_cats = [c for c in categories if 2 <= df[c].nunique() <= 50]
    all_time  = dates + periods

    if good_cats and measures:
        render_section("Analyse croisée")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        h1, h2, h3, h4 = st.columns(4)
        with h1: x_col = st.selectbox("Catégorie", good_cats, key="xc2")
        with h2: y_col = st.selectbox("Mesure",    measures,  key="yc2")
        with h3: agg   = st.selectbox("Calcul", ["Somme","Moyenne","Nombre","Maximum","Minimum"], key="ag2")
        with h4: top_n = st.slider("Top N", 5, 30, 12, key="topn2")
        try:
            agg_map = {"Somme":"sum","Moyenne":"mean","Nombre":"count","Maximum":"max","Minimum":"min"}
            grp2 = df.groupby(x_col)[y_col].agg(agg_map[agg]).reset_index()
            grp2 = grp2.sort_values(y_col, ascending=False).head(top_n)
            fig2 = px.bar(grp2, x=x_col, y=y_col, color=x_col,
                          color_discrete_sequence=CHART_COLORS, text=y_col)
            fig2.update_traces(texttemplate='%{text:.3s}', textposition='outside', marker_line_width=0)
            apply_chart_style(fig2, h=380)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            st.warning(f"Analyse croisée : {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    if all_time and measures:
        render_section("Évolution personnalisée")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: tc = st.selectbox("Axe temporel", all_time, key="tc2")
        with h2: vc = st.selectbox("Mesure",       measures, key="vc2")
        with h3: cc = st.selectbox("Découper par", ["Aucun"] + good_cats, key="cc2") if good_cats else "Aucun"
        try:
            is_p = tc in periods
            ts_g = build_time_series(df, tc, vc, col_group=cc if cc != "Aucun" else None, is_period=is_p)
            if cc != "Aucun" and cc in ts_g.columns:
                fig3 = px.line(ts_g, x=tc, y=vc, color=cc, color_discrete_sequence=CHART_COLORS)
                fig3.update_traces(line_width=2.5)
                apply_chart_style(fig3, h=340, legend=True)
            else:
                fig3 = make_area_chart(ts_g, tc, vc)
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            st.warning(f"Évolution : {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    if len(good_cats) >= 2 and measures:
        render_section("Comparaison croisée")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: c1s = st.selectbox("Catégorie 1", good_cats, key="c1s")
        with h2:
            rem = [c for c in good_cats if c != c1s]
            c2s = st.selectbox("Catégorie 2", rem, key="c2s") if rem else None
        with h3: vs = st.selectbox("Mesure", measures, key="vs2")
        if c2s:
            try:
                grp4 = df.groupby([c1s, c2s])[vs].sum().reset_index()
                fig4 = px.bar(grp4, x=c1s, y=vs, color=c2s, barmode='group',
                              color_discrete_sequence=CHART_COLORS)
                fig4.update_traces(marker_line_width=0)
                apply_chart_style(fig4, h=360, legend=True)
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})
            except Exception as e:
                st.warning(f"Comparaison : {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    if len(measures) >= 2:
        render_section("Corrélation entre mesures")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        h1, h2 = st.columns(2)
        with h1: mx = st.selectbox("Mesure X", measures, key="mx")
        with h2: my = st.selectbox("Mesure Y", [m for m in measures if m != mx], key="my")
        try:
            scatter_df = df[[mx, my]].dropna()
            scatter_df[mx] = pd.to_numeric(scatter_df[mx], errors='coerce')
            scatter_df[my] = pd.to_numeric(scatter_df[my], errors='coerce')
            scatter_df = scatter_df.dropna()
            color_col = good_cats[0] if good_cats else None
            if color_col:
                scatter_df2 = df[[mx, my, color_col]].dropna()
                fig5 = px.scatter(scatter_df2, x=mx, y=my, color=color_col,
                                  color_discrete_sequence=CHART_COLORS, opacity=0.7)
            else:
                fig5 = px.scatter(scatter_df, x=mx, y=my,
                                  color_discrete_sequence=[CRIMSON], opacity=0.6)
            fig5.update_traces(marker_size=7)
            apply_chart_style(fig5, h=360, legend=bool(color_col))
            st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})
            corr = scatter_df[mx].corr(scatter_df[my])
            if not np.isnan(corr):
                kind = "forte" if abs(corr) > 0.7 else ("modérée" if abs(corr) > 0.4 else "faible")
                direction = "positive" if corr > 0 else "négative"
                st.markdown(f"""
                <div style="padding:10px 14px;background:{CRIMSON_PALE};border-left:3px solid {CRIMSON};
                     border-radius:0 8px 8px 0;font-size:13px;color:{CRIMSON_DEEP};margin-top:8px;">
                  Corrélation {direction} {kind} : r = {corr:.3f}
                </div>""", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Corrélation : {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 3 : DONNÉES BRUTES ───────────────────────────────────────
with tab3:
    c1, c2 = st.columns([3, 1])
    with c1: search = st.text_input("🔍 Rechercher", "", placeholder="Mot-clé dans les données…")
    with c2: sort_col = st.selectbox("Trier par", ["—"] + list(df.columns))

    disp = df.copy()
    if search:
        try:
            mask = disp.astype(str).apply(lambda c: c.str.contains(search, case=False, na=False)).any(axis=1)
            disp = disp[mask]
        except Exception: pass
    if sort_col != "—":
        try: disp = disp.sort_values(sort_col, ascending=False)
        except Exception: pass

    st.dataframe(disp, height=460, use_container_width=True)
    st.markdown(f"<div style='font-size:12px;color:{MUTED};margin:8px 0;'>{len(disp):,} lignes affichées sur {len(df):,}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        try:
            buf = BytesIO(); disp.to_excel(buf, index=False)
            st.download_button("📥 Exporter en Excel", buf.getvalue(),
                               "export_analytix.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        except Exception: st.warning("Export Excel indisponible.")
    with c2:
        try:
            st.download_button("📥 Exporter en CSV",
                               disp.to_csv(index=False, sep=';').encode('utf-8-sig'),
                               "export_analytix.csv", "text/csv",
                               use_container_width=True)
        except Exception: st.warning("Export CSV indisponible.")

# ── STATUS BAR ───────────────────────────────────────────────────
render_status(domain, len(df), measures)
st.markdown('</div>', unsafe_allow_html=True)

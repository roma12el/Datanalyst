import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import json, os, re, unicodedata

st.set_page_config(
    page_title="Tableau de bord",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f0f2f6; }
[data-testid="stSidebar"] { background: #1e2d3d; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] h3 { color: #e0e8f0 !important; border-bottom: 1px solid #2e4a63; padding-bottom: 6px; }
.block-container { padding: 1.2rem 2rem; }
div[data-testid="stMetric"] {
    background: white; border-radius: 12px; padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); border-top: 4px solid #c0392b;
}
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

COLORS = ['#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad',
          '#16a085','#d35400','#e74c3c','#3498db','#2ecc71']

CONFIG_FILE = "dashboard_config.json"

# ══════════════════════════════════════════════════════════
# PERSISTANCE CONFIG
# ══════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════
# MOTEUR DE NETTOYAGE UNIVERSEL
# ══════════════════════════════════════════════════════════

# Valeurs textuelles qui signifient "manquant"
NULL_VALUES = {
    'na','n/a','n.a','n.a.','na.','nan','none','null','nil','void',
    'nd','n.d','n.d.','#n/a','#na','#div/0!','#ref!','#value!','#num!','#name?','#null!',
    '-','--','---','—','–','_','__','?','??',
    'vide','manquant','missing','empty','inconnu','unknown','non renseigné',
    'nr','ns','nc','nd','np'
}

def normalize_text(s):
    """Retire accents, met en minuscule."""
    try:
        return ''.join(
            c for c in unicodedata.normalize('NFD', str(s))
            if unicodedata.category(c) != 'Mn'
        ).lower().strip()
    except Exception:
        return str(s).lower().strip()

def parse_number(val):
    """
    Convertit n'importe quelle représentation textuelle de nombre en float.
    Gère : '1 234,56' '1.234,56' '1,234.56' '(500)' '-1 000' '50%' '€ 1 200'
    Retourne None si non convertible.
    """
    if pd.isna(val):
        return None
    s = str(val).strip()

    # Vide ou valeur nulle connue
    if s == '' or normalize_text(s) in NULL_VALUES:
        return None

    # Déjà un nombre Python
    if isinstance(val, (int, float, np.integer, np.floating)):
        return float(val) if not np.isnan(float(val)) else None

    # Retirer symboles monétaires et espaces insécables
    s = re.sub(r'[€$£¥₹\u00a0\u202f]', '', s).strip()

    # Négatif entre parenthèses : (500) → -500
    if re.match(r'^\([\d\s.,]+\)$', s):
        s = '-' + s[1:-1]

    # Pourcentage : '50%' → 0.5  (optionnel : garder comme 50)
    is_pct = s.endswith('%')
    if is_pct:
        s = s[:-1].strip()

    # Supprimer espaces internes (séparateurs de milliers)
    s = re.sub(r'\s+', '', s)

    # Détecter format : virgule = décimale ou séparateur ?
    # Règle : si dernier séparateur est ',' et avant il y a '.' → '.' séparateur de milliers
    # Ex: 1.234,56 → 1234.56  |  1,234.56 → 1234.56  |  1234,56 → 1234.56  |  1,5 → 1.5
    if ',' in s and '.' in s:
        # Les deux présents : le dernier est le décimal
        if s.rfind(',') > s.rfind('.'):
            # Format européen: 1.234,56
            s = s.replace('.', '').replace(',', '.')
        else:
            # Format anglo: 1,234.56
            s = s.replace(',', '')
    elif ',' in s:
        # Juste une virgule
        comma_pos = s.rfind(',')
        after_comma = s[comma_pos+1:]
        if len(after_comma) in (1, 2, 3) and after_comma.isdigit():
            if len(after_comma) <= 2:
                # Sûrement décimal : 1234,56 ou 1,5
                s = s.replace(',', '.')
            else:
                # 3 chiffres après virgule = peut être milliers (1,234) ou décimal (1,234)
                before_comma = s[:comma_pos]
                if len(before_comma) <= 3:
                    # 1,234 → probablement milliers en anglais
                    s = s.replace(',', '')
                else:
                    # 1234,123 → décimal
                    s = s.replace(',', '.')
        else:
            s = s.replace(',', '.')

    try:
        result = float(s)
        if is_pct:
            # Garder la valeur en % (50% → 50, pas 0.5)
            pass
        return result
    except ValueError:
        return None

def try_parse_date(series):
    """
    Essaie de parser une série texte comme dates.
    Gère : dates standard, 'janv-24', 'T1 2023', 'S2 2022', '2024/01', '20240115',
           'Jan 2024', '2024-01', noms de mois en FR/EN.
    Retourne (parsed_series, True) si succès, (None, False) sinon.
    """
    s = series.dropna().astype(str)
    if len(s) == 0:
        return None, False

    # Exclure si purement numérique (années seules)
    if pd.to_numeric(s, errors='coerce').notna().all():
        return None, False

    # Format YYYYMMDD (20240115)
    if s.str.match(r'^\d{8}$').mean() > 0.7:
        try:
            parsed = pd.to_datetime(s, format='%Y%m%d', errors='coerce')
            if parsed.notna().sum() / len(s) > 0.7:
                return parsed, True
        except Exception:
            pass

    # Format YYYY/MM ou YYYY-MM
    if s.str.match(r'^\d{4}[/\-]\d{1,2}$').mean() > 0.7:
        try:
            parsed = pd.to_datetime(s + '-01', errors='coerce')
            if parsed.notna().sum() / len(s) > 0.7:
                return parsed, True
        except Exception:
            pass

    # Trimestre : T1 2023, Q1 2023, 1T2023
    def parse_quarter(v):
        v = str(v).strip()
        m = re.match(r'[TtQq](\d)\s*(\d{4})', v) or re.match(r'(\d{4})\s*[TtQq](\d)', v)
        if m:
            groups = m.groups()
            q, y = (int(groups[0]), int(groups[1])) if len(groups[0]) == 1 else (int(groups[1]), int(groups[0]))
            month = (q - 1) * 3 + 1
            try:
                return pd.Timestamp(year=y, month=month, day=1)
            except Exception:
                return pd.NaT
        return pd.NaT

    if s.str.contains(r'[TtQq]\d', regex=True).mean() > 0.5:
        parsed = series.apply(parse_quarter)
        if parsed.notna().sum() / max(len(series.dropna()), 1) > 0.6:
            return parsed, True

    # Semestre : S1 2023, S2 2022
    def parse_semester(v):
        v = str(v).strip()
        m = re.match(r'[Ss](\d)\s*(\d{4})', v)
        if m:
            s_n, y = int(m.group(1)), int(m.group(2))
            month = 1 if s_n == 1 else 7
            try:
                return pd.Timestamp(year=y, month=month, day=1)
            except Exception:
                return pd.NaT
        return pd.NaT

    if s.str.contains(r'[Ss]\d', regex=True).mean() > 0.5:
        parsed = series.apply(parse_semester)
        if parsed.notna().sum() / max(len(series.dropna()), 1) > 0.6:
            return parsed, True

    # Mois abrégés FR/EN : janv-24, Jan-2024, janvier 2024, January 2024
    MONTHS_FR = {'jan':1,'fév':2,'fev':2,'mar':3,'avr':4,'mai':5,'jui':6,
                 'jul':7,'aoû':8,'aou':8,'sep':9,'oct':10,'nov':11,'déc':12,'dec':12,
                 'janvier':1,'février':2,'fevrier':2,'mars':3,'avril':4,'juin':6,
                 'juillet':7,'août':8,'aout':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12,'decembre':12}
    MONTHS_EN = {'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,
                 'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12,
                 'january':1,'february':2,'march':3,'april':4,'june':6,
                 'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}
    ALL_MONTHS = {**MONTHS_FR, **MONTHS_EN}

    def parse_month_name(v):
        v2 = normalize_text(str(v)).replace('-',' ').replace('/',' ')
        parts = v2.split()
        month, year = None, None
        for p in parts:
            p_clean = re.sub(r'[^a-z]','',p)
            if p_clean in ALL_MONTHS:
                month = ALL_MONTHS[p_clean]
            elif re.match(r'^\d{2,4}$', p):
                y = int(p)
                year = y + 2000 if y < 100 else y
        if month and year:
            try:
                return pd.Timestamp(year=year, month=month, day=1)
            except Exception:
                return pd.NaT
        return pd.NaT

    # Test si la série ressemble à des noms de mois
    sample = s.head(20)
    has_alpha = sample.str.contains(r'[a-zA-ZÀ-ÿ]', regex=True).mean() > 0.5
    if has_alpha:
        parsed = series.apply(parse_month_name)
        if parsed.notna().sum() / max(len(series.dropna()), 1) > 0.6:
            return parsed, True

    # Dates standard avec séparateurs
    has_sep = s.str.contains(r'[/\-\.]', regex=True).mean() > 0.5
    if not has_sep:
        return None, False

    for fmt in ['%d/%m/%Y','%d/%m/%y','%Y-%m-%d','%d-%m-%Y','%d-%m-%y',
                '%d.%m.%Y','%d.%m.%y','%m/%d/%Y','%Y/%m/%d']:
        try:
            parsed = pd.to_datetime(s, format=fmt, errors='coerce')
            ratio = parsed.notna().sum() / len(s)
            if ratio > 0.7:
                valid = parsed.dropna()
                if len(valid) > 0 and valid.dt.year.between(1950, 2100).mean() > 0.8:
                    return pd.to_datetime(series.astype(str), format=fmt, errors='coerce'), True
        except Exception:
            pass

    # Fallback générique
    try:
        parsed = pd.to_datetime(s, infer_datetime_format=True, dayfirst=True, errors='coerce')
        ratio = parsed.notna().sum() / len(s)
        if ratio > 0.7:
            valid = parsed.dropna()
            if len(valid) > 0 and valid.dt.year.between(1950, 2100).mean() > 0.8:
                return pd.to_datetime(series.astype(str), infer_datetime_format=True,
                                      dayfirst=True, errors='coerce'), True
    except Exception:
        pass

    return None, False

def clean_dataframe(df_in):
    """
    Nettoyage complet d'un DataFrame :
    - Gère cellules fusionnées (forward fill sur en-têtes)
    - Renomme colonnes Unnamed
    - Supprime lignes/colonnes vides
    - Remplace toutes les valeurs nulles textuelles par NaN
    - Convertit les nombres stockés comme texte
    - Détecte les vraies dates
    Retourne (df_clean, rapport_string)
    """
    df = df_in.copy()
    rapport = []

    # 1. Nommer les colonnes Unnamed
    new_cols = []
    for i, c in enumerate(df.columns):
        c_str = str(c).strip()
        if c_str.startswith('Unnamed') or c_str == '' or c_str == 'nan':
            new_cols.append(f'Colonne_{i+1}')
            rapport.append(f"Colonne renommée : Unnamed → Colonne_{i+1}")
        else:
            new_cols.append(c_str)
    df.columns = new_cols

    # 2. Supprimer lignes et colonnes entièrement vides
    before_rows = len(df)
    df = df.dropna(how='all').dropna(axis=1, how='all')
    df = df.reset_index(drop=True)
    if len(df) < before_rows:
        rapport.append(f"{before_rows - len(df)} lignes vides supprimées.")

    # 3. Détecter si la 1ère ligne est une vraie en-tête ou des données
    # (si toutes les valeurs de la 1ère ligne ressemblent à des données numériques, promouvoir l'index)
    if len(df) > 1:
        first_row = df.iloc[0]
        all_numeric_header = all(
            parse_number(v) is not None
            for v in first_row if pd.notna(v) and str(v).strip() not in ('', 'nan')
        )
        if all_numeric_header and not any(
            any(kw in normalize_text(str(c)) for kw in ['col','colonne','unnamed']) 
            for c in df.columns
        ):
            # La vraie en-tête est probablement perdue — on garde tel quel
            pass

    # 4. Remplacer les valeurs nulles textuelles par NaN
    null_set = NULL_VALUES
    def replace_nulls(val):
        if pd.isna(val):
            return np.nan
        s = normalize_text(str(val))
        if s in null_set or s == '':
            return np.nan
        return val

    df = df.map(replace_nulls)

    # 5. Pour chaque colonne : essayer de convertir en nombre puis en date
    conversions = {'num': 0, 'date': 0}

    for col in df.columns:
        s = df[col]
        non_null = s.dropna()
        if len(non_null) == 0:
            continue

        # Déjà datetime
        if pd.api.types.is_datetime64_any_dtype(s):
            continue

        # Déjà numérique propre
        if pd.api.types.is_numeric_dtype(s):
            continue

        # Essayer conversion numérique
        parsed_nums = non_null.apply(parse_number)
        num_ratio = parsed_nums.notna().sum() / len(non_null)

        if num_ratio >= 0.80:
            # Convertir toute la colonne
            df[col] = s.apply(parse_number)
            conversions['num'] += 1
            continue

        # Essayer conversion date
        parsed_dates, ok = try_parse_date(non_null)
        if ok and parsed_dates is not None:
            # Aligner avec l'index original
            date_series = pd.Series(index=df.index, dtype='datetime64[ns]')
            date_series[non_null.index] = parsed_dates.values
            df[col] = date_series
            conversions['date'] += 1
            continue

    if conversions['num'] > 0:
        rapport.append(f"{conversions['num']} colonne(s) convertie(s) en nombres.")
    if conversions['date'] > 0:
        rapport.append(f"{conversions['date']} colonne(s) convertie(s) en dates.")

    return df, rapport

# ══════════════════════════════════════════════════════════
# CHARGEMENT FICHIER — TOLÉRANT AUX ERREURS
# ══════════════════════════════════════════════════════════

@st.cache_data
def load_excel_sheet(fb, sheet):
    """Charge une feuille Excel avec gestion des cellules fusionnées."""
    try:
        # Lecture standard
        df = pd.read_excel(BytesIO(fb), sheet_name=sheet, header=0)
        return df
    except Exception:
        pass
    try:
        # Sans en-tête supposée
        df = pd.read_excel(BytesIO(fb), sheet_name=sheet, header=None)
        # Promouvoir 1ère ligne comme en-tête si elle contient du texte
        if df.iloc[0].apply(lambda x: isinstance(x, str)).any():
            df.columns = df.iloc[0].astype(str)
            df = df.iloc[1:].reset_index(drop=True)
        return df
    except Exception as e:
        raise e

@st.cache_data
def load_csv_smart(fb):
    """Charge un CSV en testant tous les encodages et séparateurs."""
    ENCODINGS = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'cp1250']
    SEPARATORS = [';', ',', '\t', '|', ':']

    best_df = None
    best_score = 0

    for enc in ENCODINGS:
        for sep in SEPARATORS:
            try:
                df = pd.read_csv(
                    BytesIO(fb), sep=sep, encoding=enc,
                    on_bad_lines='skip', low_memory=False
                )
                if df.empty or len(df.columns) <= 1:
                    continue
                # Score : plus de colonnes et de lignes = mieux
                score = len(df.columns) * 10 + min(len(df), 100)
                if score > best_score:
                    best_score = score
                    best_df = df
            except Exception:
                pass

    return best_df

# ══════════════════════════════════════════════════════════
# CLASSIFICATION AUTOMATIQUE DES COLONNES
# ══════════════════════════════════════════════════════════

ID_KW = ['id','n°','no','num','numero','numéro','code','ref','reference',
         'matricule','identifiant','contrat','client','compte','dossier',
         'facture','commande','ticket','order','invoice','key','serial','siren','siret']

MEAS_KW = ['montant','somme','total','chiffre','revenu','ca','budget','charge',
           'salaire','prix','cout','coût','marge','consommation','quantite',
           'volume','poids','duree','durée','heure','taux','valeur','amount',
           'sales','revenue','cost','profit','depense','recette','solde',
           'stock','energie','puissance','score','kpi','indicateur','kwh',
           'euro','eur','dollar','usd','effectif','nombre','count','qte','qty']

def is_year_col(vals, name):
    nm = normalize_text(name).replace(' ','').replace('_','')
    if any(k in nm for k in ['annee','année','year','an']):
        return True
    v = pd.to_numeric(vals, errors='coerce').dropna()
    return len(v) > 0 and v.between(1900, 2100).all() and v.nunique() <= 50

def is_period_col(vals, name):
    """Trimestre, Semestre, Mois numérique."""
    nm = normalize_text(name).replace(' ','').replace('_','')
    if any(k in nm for k in ['trimestre','semestre','quarter','mois','month','periode','periode']):
        return True
    v = pd.to_numeric(vals, errors='coerce').dropna()
    return len(v) > 0 and v.between(1, 12).all() and v.nunique() <= 12

def auto_classify(df):
    measures, categories, dates, periods, ignored = [], [], [], [], []

    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0:
            ignored.append(col); continue

        nm = normalize_text(col).replace(' ','').replace('_','').replace('-','').replace('°','')

        # Datetime natif
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            dates.append(col); continue

        is_num = pd.api.types.is_numeric_dtype(df[col])

        # Colonne texte
        if not is_num:
            categories.append(col); continue

        # Colonne numérique
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) == 0:
            ignored.append(col); continue

        # Identifiant par nom
        if any(k in nm for k in ID_KW):
            categories.append(col); continue

        # Année
        if is_year_col(vals, col):
            periods.append(col); continue

        # Trimestre/Mois/Semestre numérique
        if is_period_col(vals, col):
            periods.append(col); continue

        uniqueness = vals.nunique() / len(vals)

        # Quasi-unique sans mot-clé mesure → identifiant
        if uniqueness > 0.9 and not any(k in nm for k in MEAS_KW):
            ignored.append(col); continue

        # Peu de valeurs sans mot-clé mesure → catégorie
        if vals.nunique() <= 10 and not any(k in nm for k in MEAS_KW):
            categories.append(col); continue

        # Mot-clé mesure
        if any(k in nm for k in MEAS_KW):
            measures.append(col); continue

        # Très peu de valeurs uniques → catégorie
        if uniqueness < 0.05:
            categories.append(col); continue

        # Par défaut → mesure
        measures.append(col)

    return measures, categories, dates, periods, ignored

def detect_domain(df):
    txt = ' '.join(normalize_text(str(c)) for c in df.columns)
    scores = {
        'Financier':    sum(1 for k in ['montant','revenu','budget','charge','salaire','marge','prix','facture','comptable'] if k in txt),
        'Commercial':   sum(1 for k in ['client','contrat','commande','vente','region','zone','agence','ca','prospect'] if k in txt),
        'RH':           sum(1 for k in ['employe','effectif','absence','conge','departement','agent','matricule','formation'] if k in txt),
        'Stocks':       sum(1 for k in ['stock','produit','quantite','inventaire','article','entrepot','reference'] if k in txt),
        'Opérationnel': sum(1 for k in ['production','qualite','delai','incident','maintenance','panne','consommation'] if k in txt),
        'Énergie':      sum(1 for k in ['energie','kwh','electricite','gaz','puissance','compteur','releve'] if k in txt),
        'Informatique': sum(1 for k in ['pc','ordinateur','imprimante','bureau','portable','processeur','materiel'] if k in txt),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Général'

# ══════════════════════════════════════════════════════════
# FORMATAGE ET UTILITAIRES
# ══════════════════════════════════════════════════════════

def fmt(val):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)): return "N/A"
        v = float(val)
        if abs(v) >= 1e9:  return f"{v/1e9:.2f} Md"
        if abs(v) >= 1e6:  return f"{v/1e6:.2f} M"
        if abs(v) >= 1e3:  return f"{v/1e3:.1f} K"
        if v == int(v):    return f"{int(v):,}"
        return f"{v:,.2f}"
    except Exception:
        return str(val)

def pct_change(new, old):
    if old == 0: return None
    return (new - old) / abs(old) * 100

def chart_style(fig, h=300):
    fig.update_layout(
        margin=dict(t=45, b=10, l=10, r=10), height=h,
        showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11, color='#333'),
        title_font_size=14, title_font_color='#1e2d3d'
    )
    return fig

def safe_sum(series):
    try:
        return pd.to_numeric(series, errors='coerce').sum()
    except Exception:
        return 0

def safe_mean(series):
    try:
        return pd.to_numeric(series, errors='coerce').mean()
    except Exception:
        return 0

# ══════════════════════════════════════════════════════════
# ANALYSE BUSINESS
# ══════════════════════════════════════════════════════════

def analyse_business(df, measures, categories, dates, periods, domain):
    insights = []
    total = len(df)

    # Qualité données
    missing_pct = df.isna().mean()
    bad_cols = missing_pct[missing_pct > 0.05]
    if bad_cols.empty:
        insights.append(('good', f"Qualité parfaite : aucune valeur manquante sur {total:,} enregistrements."))
    else:
        worst = bad_cols.idxmax()
        insights.append(('alert', f"Données incomplètes : **{worst}** — {round(bad_cols[worst]*100,1)}% manquants."))

    # Mesures
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

    # Catégories
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

    # Tendance dates réelles
    if dates and measures:
        try:
            col_d, col_m = dates[0], measures[0]
            ts = df[[col_d, col_m]].copy()
            ts[col_d] = pd.to_datetime(ts[col_d], errors='coerce')
            ts = ts.dropna(subset=[col_d]).sort_values(col_d)
            ts[col_m] = pd.to_numeric(ts[col_m], errors='coerce')
            if len(ts) > 3:
                mid = len(ts) // 2
                h1 = ts.iloc[:mid][col_m].mean()
                h2 = ts.iloc[mid:][col_m].mean()
                chg = pct_change(h2, h1)
                if chg is not None:
                    dir_ = "en hausse" if chg > 0 else "en baisse"
                    insights.append(('good' if chg > 0 else 'alert',
                                     f"Tendance **{col_m}** : {dir_} de {abs(round(chg,1))}%."))
        except Exception:
            pass

    # Tendance périodes
    if periods and measures:
        try:
            col_p, col_m = periods[0], measures[0]
            grp = df.groupby(col_p)[col_m].sum().reset_index().sort_values(col_p)
            if len(grp) > 1:
                f_val = float(pd.to_numeric(grp[col_m].iloc[0], errors='coerce'))
                l_val = float(pd.to_numeric(grp[col_m].iloc[-1], errors='coerce'))
                chg = pct_change(l_val, f_val)
                if chg is not None and abs(chg) > 1:
                    dir_ = "en hausse" if chg > 0 else "en baisse"
                    insights.append(('good' if chg > 0 else 'alert',
                                     f"**{col_m}** par {col_p} : {dir_} de {abs(round(chg,1))}% ({fmt(f_val)} → {fmt(l_val)})."))
        except Exception:
            pass

    insights.append(('info', f"Domaine : **{domain}** · {total:,} lignes · {len(measures)} mesure(s) · {len(categories)} catégorie(s) · {len(dates)} date(s) · {len(periods)} période(s)."))
    return insights

# ══════════════════════════════════════════════════════════
# SÉRIE TEMPORELLE ROBUSTE
# ══════════════════════════════════════════════════════════

def build_time_series(df, col_d, col_m, col_group=None, is_period=False):
    cols = [col_d, col_m] + ([col_group] if col_group and col_group != "Aucun" else [])
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
        else:
            return ts.groupby(pd.Grouper(key=col_d, freq='ME'))[col_m].sum().reset_index()

# ══════════════════════════════════════════════════════════
# BARRE LATÉRALE
# ══════════════════════════════════════════════════════════

saved_cfg = load_config()

with st.sidebar:
    st.markdown("### 📁 Importer les données")
    uploaded = st.file_uploader(
        "Fichier Excel ou CSV",
        type=["xlsx", "xls", "csv"],
        help="Tous formats acceptés — encodages et séparateurs auto-détectés"
    )

    df_raw = None
    clean_rapport = []

    if uploaded:
        fb = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()
        try:
            if ext in ['xlsx', 'xls']:
                xl = pd.ExcelFile(BytesIO(fb))
                sheets = xl.sheet_names
                sheet = st.selectbox("Feuille", sheets) if len(sheets) > 1 else sheets[0]
                df_loaded = load_excel_sheet(fb, sheet)
            else:
                df_loaded = load_csv_smart(fb)
                if df_loaded is None:
                    st.error("❌ Impossible de lire ce CSV. Vérifiez le format.")
                    df_loaded = None

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
                for r in clean_rapport:
                    st.caption(f"• {r}")

        if auto_ign:
            st.caption(f"Ignorées : {', '.join(auto_ign[:4])}{'…' if len(auto_ign)>4 else ''}")

        st.divider()
        st.markdown("### ⚙️ Configuration des colonnes")

        measures_sel   = st.multiselect("📊 Mesures",    all_cols, default=init_meas,    key="sel_meas")
        categories_sel = st.multiselect("🏷️ Catégories", all_cols, default=init_cat,     key="sel_cat")
        dates_sel      = st.multiselect("📅 Dates",      all_cols, default=init_dates,   key="sel_dates")
        periods_sel    = st.multiselect("📆 Périodes",   all_cols, default=init_periods, key="sel_periods")

        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("💾 Sauvegarder", use_container_width=True):
                saved_cfg[file_key] = {
                    "measures": measures_sel, "categories": categories_sel,
                    "dates": dates_sel, "periods": periods_sel,
                }
                save_config(saved_cfg)
                st.success("✅ Sauvegardé !")
        with col_reset:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                if file_key in saved_cfg:
                    del saved_cfg[file_key]
                    save_config(saved_cfg)
                st.rerun()

        st.divider()
        st.markdown("### 🔽 Filtres")
        filters = {}
        for col in categories_sel[:4]:
            if col not in df_raw.columns: continue
            vals = sorted(df_raw[col].dropna().astype(str).unique().tolist())
            if 2 <= len(vals) <= 80:
                sel = st.multiselect(col, vals, default=[], key=f"f_{col}")
                if sel:
                    filters[col] = sel

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

if df_raw is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px">
      <div style="font-size:56px">📊</div>
      <h2 style="color:#1e2d3d;margin:16px 0 8px">Tableau de bord</h2>
      <p style="color:#666;font-size:15px;max-width:480px;margin:0 auto">
        Importez votre fichier Excel ou CSV dans la barre latérale.<br>
        Le tableau de bord s'adapte automatiquement à vos données.
      </p>
    </div>
    """, unsafe_allow_html=True)
    for col, icon, lbl in zip(st.columns(4),
        ["📈","⚙️","👥","📦"],
        ["Financier","Opérationnel","RH","Stocks & Ventes"]):
        with col:
            st.markdown(f"""<div style="background:white;border-radius:12px;padding:20px;
            text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
            <div style="font-size:28px">{icon}</div>
            <p style="font-size:13px;color:#555;margin:8px 0 0;font-weight:500">{lbl}</p>
            </div>""", unsafe_allow_html=True)
    st.stop()

# Appliquer filtres
df = df_raw.copy()
for col, vals in filters.items():
    if col in df.columns:
        df = df[df[col].astype(str).isin(vals)]

measures   = [c for c in measures_sel   if c in df.columns]
categories = [c for c in categories_sel if c in df.columns]
dates      = [c for c in dates_sel      if c in df.columns]
periods    = [c for c in periods_sel    if c in df.columns]
domain     = detect_domain(df)

DOMAIN_ICONS = {'Financier':'💰','Commercial':'🤝','RH':'👥','Stocks':'📦',
                'Opérationnel':'⚙️','Énergie':'⚡','Informatique':'💻','Général':'📊'}
d_icon = DOMAIN_ICONS.get(domain, '📊')

# ── EN-TÊTE ───────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="background:#1e2d3d;padding:18px 24px;border-radius:14px;margin-bottom:20px;
     display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
  <div>
    <div style="color:white;font-size:19px;font-weight:700">{d_icon} Tableau de bord — {uploaded.name}</div>
    <div style="color:#8899aa;font-size:12px;margin-top:3px">
      {len(df):,} enregistrements · {len(df.columns)} colonnes · Domaine : {domain}
      {f" · {len(df_raw)-len(df):,} exclus par filtres" if filters else ""}
    </div>
  </div>
  <div style="background:#c0392b;color:white;padding:7px 16px;border-radius:8px;font-size:12px;font-weight:600">Tableau de bord</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────

kpi_meas = measures[:4]
kpi_grid = st.columns(len(kpi_meas) + 1)

with kpi_grid[0]:
    st.metric("Enregistrements", f"{len(df):,}",
              delta=f"{len(df_raw)-len(df):,} filtrés" if filters else None)

for i, col in enumerate(kpi_meas):
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals) == 0: continue
    total_v = vals.sum()
    mean_v  = vals.mean()
    if filters:
        vals_all = pd.to_numeric(df_raw[col], errors='coerce').dropna()
        chg = pct_change(total_v, vals_all.sum())
        delta_str = f"{round(chg,1)}% vs total" if chg is not None else None
    else:
        delta_str = f"Moy : {fmt(mean_v)}"
    with kpi_grid[i + 1]:
        st.metric(col[:22], fmt(total_v), delta=delta_str)

st.markdown("<div style='margin:6px 0'></div>", unsafe_allow_html=True)

# ── ANALYSE BUSINESS ──────────────────────────────────────────────────────────

insights = analyse_business(df, measures, categories, dates, periods, domain)
with st.expander("💡 Analyse automatique", expanded=True):
    for kind, msg in insights:
        css = {'good':'insight-good','alert':'insight-alert','warn':'insight-warn','info':'insight-info'}
        st.markdown(f'<div class="{css.get(kind,"insight-info")}">{msg}</div>', unsafe_allow_html=True)

st.divider()

# ── ONGLETS ───────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "🔍 Analyse détaillée", "🗂️ Données"])

# ══════════════════════════════════════════════════════════
# ONGLET 1
# ══════════════════════════════════════════════════════════
with tab1:

    show_cats = [c for c in categories if 2 <= df[c].nunique() <= 30][:6]

    if show_cats:
        st.markdown('<div class="section-title">Répartitions</div>', unsafe_allow_html=True)
        pairs = [show_cats[i:i+2] for i in range(0, len(show_cats), 2)]
        for pair in pairs:
            gcols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with gcols[ci]:
                    try:
                        counts = df[col].astype(str).value_counts().head(10).reset_index()
                        counts.columns = [col, 'Nombre']
                        counts['%'] = (counts['Nombre'] / counts['Nombre'].sum() * 100).round(1)
                        if len(counts) <= 6:
                            fig = px.pie(counts, names=col, values='Nombre',
                                         color_discrete_sequence=COLORS, hole=0.5, title=col)
                            fig.update_traces(textinfo='percent+label', textposition='inside')
                        else:
                            fig = px.bar(counts, x='Nombre', y=col, orientation='h',
                                         color=col, color_discrete_sequence=COLORS, title=col, text='%')
                            fig.update_traces(texttemplate='%{text}%', textposition='outside')
                            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                        chart_style(fig)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        st.caption(f"Impossible d'afficher {col}")

    # Évolution temporelle
    time_shown = False
    if dates and measures:
        st.markdown('<div class="section-title">Évolution dans le temps</div>', unsafe_allow_html=True)
        try:
            ts_g = build_time_series(df, dates[0], measures[0], is_period=False)
            if len(ts_g) > 1:
                fig_t = px.area(ts_g, x=dates[0], y=measures[0],
                                color_discrete_sequence=[COLORS[0]],
                                title=f"Évolution — {measures[0]}")
                fig_t.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
                chart_style(fig_t, h=280)
                st.plotly_chart(fig_t, use_container_width=True)
                time_shown = True
        except Exception as e:
            st.warning(f"Graphique temporel : {e}")

    if not time_shown and periods and measures:
        st.markdown('<div class="section-title">Évolution par période</div>', unsafe_allow_html=True)
        try:
            ts_g = build_time_series(df, periods[0], measures[0], is_period=True)
            if len(ts_g) > 1:
                fig_t = px.bar(ts_g, x=periods[0], y=measures[0],
                               color_discrete_sequence=[COLORS[0]],
                               title=f"{measures[0]} par {periods[0]}", text=measures[0])
                fig_t.update_traces(texttemplate='%{text:.3s}', textposition='outside', marker_line_width=0)
                chart_style(fig_t, h=280)
                st.plotly_chart(fig_t, use_container_width=True)
        except Exception as e:
            st.warning(f"Graphique période : {e}")

    # Classement
    if show_cats and measures:
        st.markdown('<div class="section-title">Classement</div>', unsafe_allow_html=True)
        best_cat, best_val = show_cats[0], measures[0]
        try:
            grp = df.groupby(best_cat)[best_val].sum().reset_index().sort_values(best_val, ascending=False)
            grp[best_val] = pd.to_numeric(grp[best_val], errors='coerce')
            total_grp = grp[best_val].sum()
            grp['%'] = (grp[best_val] / total_grp * 100).round(1) if total_grp != 0 else 0

            c1, c2 = st.columns(2)
            with c1:
                top = grp.head(8)
                fig_top = px.bar(top, x=best_val, y=best_cat, orientation='h',
                                 color=best_cat, color_discrete_sequence=COLORS,
                                 title=f"Top — {best_cat}", text='%')
                fig_top.update_traces(texttemplate='%{text}%', textposition='outside')
                fig_top.update_layout(yaxis={'categoryorder': 'total ascending'})
                chart_style(fig_top, h=320)
                st.plotly_chart(fig_top, use_container_width=True)
            with c2:
                flop = grp.tail(8).sort_values(best_val)
                fig_flop = px.bar(flop, x=best_val, y=best_cat, orientation='h',
                                  color=best_cat, color_discrete_sequence=COLORS[::-1],
                                  title=f"Bas — {best_cat}", text='%')
                fig_flop.update_traces(texttemplate='%{text}%', textposition='outside')
                fig_flop.update_layout(yaxis={'categoryorder': 'total ascending'})
                chart_style(fig_flop, h=320)
                st.plotly_chart(fig_flop, use_container_width=True)
        except Exception as e:
            st.warning(f"Classement : {e}")

# ══════════════════════════════════════════════════════════
# ONGLET 2
# ══════════════════════════════════════════════════════════
with tab2:
    good_cats = [c for c in categories if 2 <= df[c].nunique() <= 50]

    if good_cats and measures:
        st.markdown('<div class="section-title">Analyse croisée</div>', unsafe_allow_html=True)
        h1, h2, h3, h4 = st.columns(4)
        with h1: x_col = st.selectbox("Catégorie", good_cats, key="xc")
        with h2: y_col = st.selectbox("Mesure",    measures,  key="yc")
        with h3: agg   = st.selectbox("Calcul", ["Somme","Moyenne","Nombre","Maximum","Minimum"], key="ag")
        with h4: top_n = st.slider("Top N", 5, 25, 10, key="topn")

        try:
            agg_map = {"Somme":"sum","Moyenne":"mean","Nombre":"count","Maximum":"max","Minimum":"min"}
            grp2 = (df.groupby(x_col)[y_col]
                    .agg(agg_map[agg]).reset_index()
                    .sort_values(y_col, ascending=False).head(top_n))
            fig2 = px.bar(grp2, x=x_col, y=y_col, color=x_col,
                          color_discrete_sequence=COLORS,
                          title=f"{agg} de {y_col} par {x_col}", text=y_col)
            fig2.update_traces(texttemplate='%{text:.3s}', textposition='outside')
            chart_style(fig2, h=360)
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.warning(f"Analyse croisée : {e}")

    all_time_cols = dates + periods
    if all_time_cols and measures:
        st.markdown('<div class="section-title">Évolution personnalisée</div>', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: tc     = st.selectbox("Axe temporel", all_time_cols, key="tc2")
        with h2: vc_col = st.selectbox("Mesure", measures, key="vc2")
        with h3: cc     = st.selectbox("Découper par", ["Aucun"] + good_cats, key="cc2") if good_cats else "Aucun"

        try:
            is_p = tc in periods
            ts_g = build_time_series(df, tc, vc_col,
                                     col_group=cc if cc != "Aucun" else None,
                                     is_period=is_p)
            if cc != "Aucun" and cc in ts_g.columns:
                fig3 = px.line(ts_g, x=tc, y=vc_col, color=cc,
                               color_discrete_sequence=COLORS, title=f"{vc_col} par {cc}")
                fig3.update_layout(showlegend=True)
            else:
                fig3 = px.area(ts_g, x=tc, y=vc_col,
                               color_discrete_sequence=[COLORS[0]], title=f"{vc_col}")
                fig3.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig3, h=320)
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Évolution : {e}")

    if len(good_cats) >= 2 and measures:
        st.markdown('<div class="section-title">Comparaison croisée</div>', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: c1s = st.selectbox("Catégorie 1", good_cats, key="c1s")
        with h2:
            rem = [c for c in good_cats if c != c1s]
            c2s = st.selectbox("Catégorie 2", rem, key="c2s") if rem else None
        with h3: vs = st.selectbox("Mesure", measures, key="vs2")
        if c2s:
            try:
                grp4 = df.groupby([c1s, c2s])[vs].sum().reset_index()
                fig4 = px.bar(grp4, x=c1s, y=vs, color=c2s,
                              color_discrete_sequence=COLORS, barmode='group',
                              title=f"{vs} — {c1s} × {c2s}")
                chart_style(fig4, h=360).update_layout(showlegend=True)
                st.plotly_chart(fig4, use_container_width=True)
            except Exception as e:
                st.warning(f"Comparaison : {e}")

# ══════════════════════════════════════════════════════════
# ONGLET 3
# ══════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input("Rechercher", "", key="search", placeholder="Mot-clé…")
    with c2:
        sort_col = st.selectbox("Trier par", ["—"] + list(df.columns), key="sort_col")

    disp = df.copy()
    if search:
        try:
            mask = disp.astype(str).apply(
                lambda c: c.str.contains(search, case=False, na=False)
            ).any(axis=1)
            disp = disp[mask]
        except Exception:
            pass
    if sort_col != "—":
        try:
            disp = disp.sort_values(sort_col, ascending=False)
        except Exception:
            pass

    st.dataframe(disp, height=440, use_container_width=True)
    st.caption(f"{len(disp):,} lignes affichées sur {len(df):,}")

    c1, c2 = st.columns(2)
    with c1:
        try:
            buf = BytesIO()
            disp.to_excel(buf, index=False)
            st.download_button("📥 Exporter Excel", buf.getvalue(),
                               "tableau_de_bord.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:
            st.warning("Export Excel indisponible.")
    with c2:
        try:
            st.download_button("📥 Exporter CSV",
                               disp.to_csv(index=False, sep=';').encode('utf-8-sig'),
                               "tableau_de_bord.csv", "text/csv")
        except Exception:
            st.warning("Export CSV indisponible.")

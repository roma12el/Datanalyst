import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import json, os

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

# ─── PERSISTANCE CONFIG ───────────────────────────────────

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# ─── CHARGEMENT FICHIER ───────────────────────────────────

@st.cache_data
def load_excel(fb, sheet):
    return pd.read_excel(BytesIO(fb), sheet_name=sheet)

@st.cache_data
def load_csv(fb):
    for sep in [';',',','\t','|']:
        for enc in ['utf-8','latin-1','utf-8-sig']:
            try:
                df = pd.read_csv(BytesIO(fb), sep=sep, encoding=enc)
                if len(df.columns) > 1:
                    return df
            except Exception:
                pass
    return pd.read_csv(BytesIO(fb))

# ─── DÉTECTION AUTOMATIQUE ────────────────────────────────

ID_KW   = ['id','n°','no','num','numero','numéro','code','ref','reference',
            'matricule','identifiant','contrat','client','compte','dossier',
            'facture','commande','ticket','order','invoice','key','serial']
DATE_KW = ['date','année','annee','mois','jour','trimestre','semestre',
            'semaine','period','year','month','day','quarter','time']
MEAS_KW = ['montant','somme','total','chiffre','revenu','ca','budget','charge',
            'salaire','prix','cout','coût','marge','consommation','quantite',
            'volume','poids','duree','durée','heure','taux','valeur','amount',
            'sales','revenue','cost','profit','depense','recette','solde',
            'stock','energie','puissance','score','kpi','indicateur']

def auto_classify(df):
    measures, categories, dates, ignored = [], [], [], []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0:
            ignored.append(col); continue
        name = col.lower().replace(' ','').replace('_','').replace('-','').replace('°','')

        # Déjà datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            dates.append(col); continue

        # Texte → date ?
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                cd = pd.to_datetime(s, errors='coerce', dayfirst=True)
                if cd.notna().sum()/len(s) > 0.7:
                    df[col] = cd; dates.append(col); continue
            except Exception:
                pass
            categories.append(col); continue

        # Numérique : convertir si besoin
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) == 0:
            ignored.append(col); continue

        uniqueness = vals.nunique() / len(vals)

        # Mot-clé date numérique (Mois, Année…)
        if any(kw in name for kw in DATE_KW):
            dates.append(col); continue

        # Identifiant par nom
        if any(kw in name for kw in ID_KW):
            categories.append(col); continue

        # Quasi-unique → identifiant
        if uniqueness > 0.9:
            ignored.append(col); continue

        # Mot-clé mesure explicite
        if any(kw in name for kw in MEAS_KW):
            measures.append(col); continue

        # Peu de valeurs uniques → catégorie
        if uniqueness < 0.05 or vals.nunique() <= 20:
            categories.append(col); continue

        # Par défaut → mesure
        measures.append(col)

    return measures, categories, dates, ignored

def detect_domain(df):
    txt = ' '.join(df.columns).lower()
    scores = {
        'Financier':    sum(1 for k in ['montant','revenu','budget','charge','salaire','marge','prix'] if k in txt),
        'Commercial':   sum(1 for k in ['client','contrat','commande','vente','region','zone','agence'] if k in txt),
        'RH':           sum(1 for k in ['employe','effectif','absence','conge','departement','agent'] if k in txt),
        'Stocks':       sum(1 for k in ['stock','produit','quantite','inventaire','article','entrepot'] if k in txt),
        'Opérationnel': sum(1 for k in ['production','qualite','delai','incident','maintenance','panne'] if k in txt),
        'Informatique': sum(1 for k in ['pc','ordinateur','imprimante','bureau','portable','processeur'] if k in txt),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Général'

# ─── FORMATAGE ────────────────────────────────────────────

def fmt(val):
    if pd.isna(val): return "N/A"
    v = float(val)
    if abs(v) >= 1e9:  return f"{v/1e9:.2f} Md"
    if abs(v) >= 1e6:  return f"{v/1e6:.2f} M"
    if abs(v) >= 1e3:  return f"{v/1e3:.1f} K"
    if v == int(v):    return f"{int(v):,}"
    return f"{v:,.2f}"

def pct_change(new, old):
    if old == 0: return None
    return (new - old) / abs(old) * 100

def chart_style(fig, h=300):
    fig.update_layout(
        margin=dict(t=45,b=10,l=10,r=10), height=h,
        showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11, color='#333'),
        title_font_size=14, title_font_color='#1e2d3d'
    )
    return fig

# ─── ANALYSE BUSINESS LOGIQUE ─────────────────────────────

def analyse_business(df, measures, categories, dates, domain):
    insights = []

    # 1. Qualité des données
    total = len(df)
    missing_pct = df.isna().mean()
    bad_cols = missing_pct[missing_pct > 0.05]
    if bad_cols.empty:
        insights.append(('good', f"Qualité des données : aucune valeur manquante sur {total:,} enregistrements."))
    else:
        worst = bad_cols.idxmax()
        insights.append(('alert', f"Données incomplètes : la colonne **{worst}** a {round(bad_cols[worst]*100,1)}% de valeurs manquantes."))

    # 2. Analyse des mesures principales
    for col in measures[:2]:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) < 2: continue
        total_v  = vals.sum()
        mean_v   = vals.mean()
        max_v    = vals.max()
        min_v    = vals.min()
        top_pct  = (max_v - mean_v) / abs(mean_v) * 100 if mean_v != 0 else 0

        if top_pct > 300:
            insights.append(('alert', f"**{col}** : valeur maximale ({fmt(max_v)}) anormalement élevée — possibles données aberrantes à vérifier."))
        elif top_pct > 100:
            insights.append(('warn', f"**{col}** : forte dispersion des valeurs (max {fmt(max_v)} vs moyenne {fmt(mean_v)})."))
        else:
            insights.append(('good', f"**{col}** : distribution homogène — total {fmt(total_v)}, moyenne {fmt(mean_v)}."))

    # 3. Concentration des catégories
    for col in categories[:2]:
        vc = df[col].value_counts()
        if len(vc) < 2: continue
        top_share = vc.iloc[0] / total * 100
        top2_share = (vc.iloc[0] + vc.iloc[1]) / total * 100 if len(vc) >= 2 else top_share
        if top_share > 60:
            insights.append(('warn', f"**{col}** : « {vc.index[0]} » domine avec {round(top_share)}% — forte concentration."))
        elif top2_share > 80:
            insights.append(('info', f"**{col}** : 2 valeurs couvrent {round(top2_share)}% des données ({vc.index[0]}, {vc.index[1]})."))
        else:
            insights.append(('good', f"**{col}** : répartition équilibrée entre {len(vc)} catégories."))

    # 4. Tendance temporelle
    if dates and measures:
        try:
            col_d = dates[0]
            col_m = measures[0]
            ts = df[[col_d, col_m]].copy()
            ts[col_d] = pd.to_datetime(ts[col_d], errors='coerce', dayfirst=True)
            ts = ts.dropna().sort_values(col_d)
            if len(ts) > 1:
                mid = len(ts) // 2
                first_half = ts.iloc[:mid][col_m].mean()
                second_half = ts.iloc[mid:][col_m].mean()
                chg = pct_change(second_half, first_half)
                if chg is not None:
                    direction = "en hausse" if chg > 0 else "en baisse"
                    color = 'good' if chg > 0 else 'alert'
                    insights.append((color, f"Tendance **{col_m}** : {direction} de {abs(round(chg,1))}% sur la période analysée."))
        except Exception:
            pass

    # 5. Résumé global
    nb_m = len(measures)
    nb_c = len(categories)
    nb_d = len(dates)
    insights.append(('info', f"Domaine détecté : **{domain}** · {total:,} enregistrements · {nb_m} mesure(s) · {nb_c} catégorie(s) · {nb_d} date(s)."))

    return insights

# ═══════════════════════════════════════════════════════════
# BARRE LATÉRALE
# ═══════════════════════════════════════════════════════════

saved_cfg = load_config()

with st.sidebar:
    st.markdown("### 📁 Importer les données")
    uploaded = st.file_uploader(
        "Fichier Excel ou CSV",
        type=["xlsx","xls","csv"],
        help="Tous types de données acceptés"
    )

    df_raw = None
    if uploaded:
        fb = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()
        try:
            if ext in ['xlsx','xls']:
                xl = pd.ExcelFile(BytesIO(fb))
                sheets = xl.sheet_names
                sheet = st.selectbox("Feuille", sheets) if len(sheets) > 1 else sheets[0]
                df_raw = load_excel(fb, sheet)
            else:
                df_raw = load_csv(fb)
        except Exception as e:
            st.error(f"Erreur : {e}")

    if df_raw is not None:
        df_raw.columns = [str(c).strip() for c in df_raw.columns]
        df_raw = df_raw.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)

        # Détection auto
        auto_meas, auto_cat, auto_dates, auto_ign = auto_classify(df_raw.copy())

        # Charger config sauvegardée si même fichier
        file_key = uploaded.name
        cfg = saved_cfg.get(file_key, {})
        init_meas  = cfg.get("measures",   auto_meas)
        init_cat   = cfg.get("categories", auto_cat)
        init_dates = cfg.get("dates",      auto_dates)

        # Filtrer pour ne garder que les colonnes existantes
        all_cols = list(df_raw.columns)
        init_meas  = [c for c in init_meas  if c in all_cols]
        init_cat   = [c for c in init_cat   if c in all_cols]
        init_dates = [c for c in init_dates if c in all_cols]

        st.success(f"✅ {len(df_raw):,} lignes · {len(df_raw.columns)} colonnes")

        st.divider()
        st.markdown("### ⚙️ Configuration des colonnes")
        st.caption("Choisissez le rôle de chaque colonne")

        measures_sel  = st.multiselect("📊 Mesures (valeurs à analyser)", all_cols, default=init_meas,  key="sel_meas",  help="Ex: Montant, Consommation, Quantité")
        categories_sel= st.multiselect("🏷️ Catégories (regroupements)",  all_cols, default=init_cat,   key="sel_cat",   help="Ex: Région, Type, Statut")
        dates_sel     = st.multiselect("📅 Dates (axe temporel)",         all_cols, default=init_dates, key="sel_dates", help="Ex: Date, Année, Mois")

        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("💾 Sauvegarder", use_container_width=True):
                saved_cfg[file_key] = {
                    "measures":   measures_sel,
                    "categories": categories_sel,
                    "dates":      dates_sel
                }
                save_config(saved_cfg)
                st.success("Config sauvegardée !")
        with col_reset:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                measures_sel   = auto_meas
                categories_sel = auto_cat
                dates_sel      = auto_dates
                st.rerun()

        st.divider()
        st.markdown("### 🔽 Filtres")
        filters = {}
        for col in categories_sel[:4]:
            vals = sorted(df_raw[col].dropna().astype(str).unique().tolist())
            if 2 <= len(vals) <= 50:
                sel = st.multiselect(col, vals, default=[], key=f"f_{col}")
                if sel:
                    filters[col] = sel

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

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
    c1,c2,c3,c4 = st.columns(4)
    for col, icon, lbl in zip([c1,c2,c3,c4],
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
    df = df[df[col].astype(str).isin(vals)]

# Recalc après filtre
measures   = [c for c in measures_sel   if c in df.columns]
categories = [c for c in categories_sel if c in df.columns]
dates      = [c for c in dates_sel      if c in df.columns]
domain     = detect_domain(df)

DOMAIN_ICONS = {'Financier':'💰','Commercial':'🤝','RH':'👥','Stocks':'📦',
                'Opérationnel':'⚙️','Informatique':'💻','Général':'📊'}
d_icon = DOMAIN_ICONS.get(domain,'📊')

# ─── EN-TÊTE ─────────────────────────────────────────────

st.markdown(f"""
<div style="background:#1e2d3d;padding:18px 24px;border-radius:14px;margin-bottom:20px;
     display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
  <div>
    <div style="color:white;font-size:19px;font-weight:700">{d_icon} Tableau de bord — {uploaded.name}</div>
    <div style="color:#8899aa;font-size:12px;margin-top:3px">
      {len(df):,} enregistrements · {len(df.columns)} colonnes · Domaine : {domain}
      {f" · Filtre actif : {len(df_raw)-len(df):,} exclus" if filters else ""}
    </div>
  </div>
  <div style="background:#c0392b;color:white;padding:7px 16px;border-radius:8px;font-size:12px;font-weight:600">Tableau de bord</div>
</div>
""", unsafe_allow_html=True)

# ─── KPI ─────────────────────────────────────────────────

kpi_meas = measures[:5]
ncols = len(kpi_meas) + 1
kpi_grid = st.columns(ncols)

with kpi_grid[0]:
    st.metric("Enregistrements", f"{len(df):,}",
              delta=f"{len(df_raw)-len(df):,} filtrés" if filters else None)

for i, col in enumerate(kpi_meas):
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals) == 0: continue
    total_v = vals.sum()
    mean_v  = vals.mean()
    # Comparaison avec données non filtrées
    if filters:
        vals_all = pd.to_numeric(df_raw[col], errors='coerce').dropna()
        delta_pct = pct_change(total_v, vals_all.sum())
        delta_str = f"{round(delta_pct,1)}% vs total" if delta_pct is not None else None
    else:
        delta_str = f"Moy : {fmt(mean_v)}"
    with kpi_grid[i+1]:
        st.metric(col[:22], fmt(total_v), delta=delta_str)

st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

# ─── ANALYSE BUSINESS ────────────────────────────────────

insights = analyse_business(df, measures, categories, dates, domain)
with st.expander("💡 Analyse automatique", expanded=True):
    for kind, msg in insights:
        css_map = {'good':'insight-good','alert':'insight-alert','warn':'insight-warn','info':'insight-info'}
        st.markdown(f'<div class="{css_map.get(kind,"insight-info")}">{msg}</div>', unsafe_allow_html=True)

st.divider()

# ─── ONGLETS ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble","🔍 Analyse détaillée","🗂️ Données"])

# ══════════════════════════════════════════════════════════
# ONGLET 1 — VUE D'ENSEMBLE
# ══════════════════════════════════════════════════════════
with tab1:

    # ── Répartitions catégorielles ──────────────────────
    show_cats = [c for c in categories if 2 <= df[c].nunique() <= 30][:6]
    if show_cats:
        st.markdown('<div class="section-title">Répartitions</div>', unsafe_allow_html=True)
        pairs = [show_cats[i:i+2] for i in range(0, len(show_cats), 2)]
        for pair in pairs:
            gcols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with gcols[ci]:
                    counts = df[col].astype(str).value_counts().head(10).reset_index()
                    counts.columns = [col,'Nombre']
                    counts['%'] = (counts['Nombre']/counts['Nombre'].sum()*100).round(1)
                    if len(counts) <= 6:
                        fig = px.pie(counts, names=col, values='Nombre',
                                     color_discrete_sequence=COLORS, hole=0.5, title=col)
                        fig.update_traces(textinfo='percent+label', textposition='inside')
                    else:
                        fig = px.bar(counts, x='Nombre', y=col, orientation='h',
                                     color=col, color_discrete_sequence=COLORS,
                                     title=col, text='%')
                        fig.update_traces(texttemplate='%{text}%', textposition='outside')
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    chart_style(fig)
                    st.plotly_chart(fig, use_container_width=True)

    # ── Évolution temporelle automatique ────────────────
    if dates and measures:
        st.markdown('<div class="section-title">Évolution dans le temps</div>', unsafe_allow_html=True)
        try:
            col_d = dates[0]
            col_m = measures[0]
            ts = df[[col_d, col_m]].copy()
            ts[col_d] = pd.to_datetime(ts[col_d], errors='coerce', dayfirst=True)
            ts = ts.dropna().sort_values(col_d)
            ts_g = ts.groupby(col_d)[col_m].sum().reset_index()
            fig_t = px.area(ts_g, x=col_d, y=col_m,
                            color_discrete_sequence=[COLORS[0]],
                            title=f"Évolution — {col_m}")
            fig_t.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig_t, h=260)
            st.plotly_chart(fig_t, use_container_width=True)
        except Exception:
            pass

    # ── Top & Bas classement ─────────────────────────────
    if show_cats and measures:
        st.markdown('<div class="section-title">Classement</div>', unsafe_allow_html=True)
        best_cat = show_cats[0]
        best_val = measures[0]
        grp = (df.groupby(best_cat)[best_val]
               .sum().reset_index()
               .sort_values(best_val, ascending=False))
        total_grp = grp[best_val].sum()
        grp['%'] = (grp[best_val]/total_grp*100).round(1)

        c1, c2 = st.columns(2)
        with c1:
            top = grp.head(8)
            fig_top = px.bar(top, x=best_val, y=best_cat, orientation='h',
                             color=best_cat, color_discrete_sequence=COLORS,
                             title=f"Top — {best_cat}", text='%')
            fig_top.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            chart_style(fig_top, h=320)
            st.plotly_chart(fig_top, use_container_width=True)
        with c2:
            flop = grp.tail(8).sort_values(best_val)
            fig_flop = px.bar(flop, x=best_val, y=best_cat, orientation='h',
                              color=best_cat, color_discrete_sequence=COLORS[::-1],
                              title=f"Bas — {best_cat}", text='%')
            fig_flop.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_flop.update_layout(yaxis={'categoryorder':'total ascending'})
            chart_style(fig_flop, h=320)
            st.plotly_chart(fig_flop, use_container_width=True)

# ══════════════════════════════════════════════════════════
# ONGLET 2 — ANALYSE DÉTAILLÉE
# ══════════════════════════════════════════════════════════
with tab2:
    good_cats = [c for c in categories if 2 <= df[c].nunique() <= 50]

    # ── Analyse croisée ──────────────────────────────────
    if good_cats and measures:
        st.markdown('<div class="section-title">Analyse croisée</div>', unsafe_allow_html=True)
        h1,h2,h3,h4 = st.columns(4)
        with h1: x_col  = st.selectbox("Catégorie", good_cats, key="xc")
        with h2: y_col  = st.selectbox("Mesure",    measures,  key="yc")
        with h3: agg    = st.selectbox("Calcul", ["Somme","Moyenne","Nombre","Maximum","Minimum"], key="ag")
        with h4: top_n  = st.slider("Top N", 5, 25, 10, key="topn")

        agg_map = {"Somme":"sum","Moyenne":"mean","Nombre":"count","Maximum":"max","Minimum":"min"}
        grp2 = (df.groupby(x_col)[y_col]
                .agg(agg_map[agg]).reset_index()
                .sort_values(y_col, ascending=False).head(top_n))

        fig2 = px.bar(grp2, x=x_col, y=y_col,
                      color=x_col, color_discrete_sequence=COLORS,
                      title=f"{agg} de {y_col} par {x_col}", text=y_col)
        fig2.update_traces(texttemplate='%{text:.3s}', textposition='outside')
        chart_style(fig2, h=360)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Évolution personnalisée ──────────────────────────
    if dates and measures:
        st.markdown('<div class="section-title">Évolution personnalisée</div>', unsafe_allow_html=True)
        h1,h2,h3 = st.columns(3)
        with h1: tc = st.selectbox("Date",   dates,   key="tc2")
        with h2: vc = st.selectbox("Mesure", measures, key="vc2")
        with h3: cc = st.selectbox("Découper par", ["Aucun"] + good_cats, key="cc2") if good_cats else "Aucun"

        try:
            cols_n = [tc, vc] + ([cc] if cc != "Aucun" else [])
            ts2 = df[cols_n].copy()
            ts2[tc] = pd.to_datetime(ts2[tc], errors='coerce', dayfirst=True)
            ts2 = ts2.dropna(subset=[tc]).sort_values(tc)
            if cc != "Aucun":
                ts2_g = ts2.groupby([tc, cc])[vc].sum().reset_index()
                fig3  = px.line(ts2_g, x=tc, y=vc, color=cc,
                                color_discrete_sequence=COLORS,
                                title=f"{vc} par {cc} dans le temps")
                fig3.update_layout(showlegend=True)
            else:
                ts2_g = ts2.groupby(tc)[vc].sum().reset_index()
                fig3  = px.area(ts2_g, x=tc, y=vc,
                                color_discrete_sequence=[COLORS[0]],
                                title=f"{vc} dans le temps")
                fig3.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig3, h=320)
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossible de tracer : {e}")

    # ── Comparaison 2 catégories ─────────────────────────
    if len(good_cats) >= 2 and measures:
        st.markdown('<div class="section-title">Comparaison croisée</div>', unsafe_allow_html=True)
        h1,h2,h3 = st.columns(3)
        with h1: c1s = st.selectbox("Catégorie 1", good_cats, key="c1s")
        with h2:
            rem = [c for c in good_cats if c != c1s]
            c2s = st.selectbox("Catégorie 2", rem, key="c2s") if rem else None
        with h3: vs  = st.selectbox("Mesure", measures, key="vs2")
        if c2s:
            grp4 = df.groupby([c1s, c2s])[vs].sum().reset_index()
            fig4 = px.bar(grp4, x=c1s, y=vs, color=c2s,
                          color_discrete_sequence=COLORS, barmode='group',
                          title=f"{vs} — {c1s} × {c2s}")
            chart_style(fig4, h=360).update_layout(showlegend=True)
            st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════
# ONGLET 3 — DONNÉES
# ══════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns([3,1])
    with c1:
        search = st.text_input("Rechercher dans les données", "", key="search",
                               placeholder="Mot-clé…")
    with c2:
        sort_col = st.selectbox("Trier par", ["—"] + list(df.columns), key="sort_col")

    disp = df.copy()
    if search:
        mask = disp.astype(str).apply(lambda c: c.str.contains(search, case=False, na=False)).any(axis=1)
        disp = disp[mask]
    if sort_col != "—":
        disp = disp.sort_values(sort_col, ascending=False)

    st.dataframe(disp, height=440, use_container_width=True)
    st.caption(f"{len(disp):,} lignes affichées sur {len(df):,}")

    c1, c2 = st.columns(2)
    with c1:
        buf = BytesIO(); disp.to_excel(buf, index=False)
        st.download_button("📥 Exporter Excel", buf.getvalue(),
                           "tableau_de_bord.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button("📥 Exporter CSV",
                           disp.to_csv(index=False, sep=';').encode('utf-8-sig'),
                           "tableau_de_bord.csv", "text/csv")

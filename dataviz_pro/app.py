import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

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
[data-testid="stSidebar"] h3 { color: #e0e8f0 !important; border-bottom: 1px solid #2e4a63; padding-bottom:6px; }
[data-testid="stSidebar"] .stFileUploader label { color: white !important; font-size:14px; }
.block-container { padding: 1.2rem 2rem; }
div[data-testid="stMetric"] {
    background: white; border-radius: 12px; padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); border-top: 4px solid #c0392b;
}
div[data-testid="stMetric"] label { font-size: 12px !important; color: #888 !important; text-transform: uppercase; letter-spacing: .5px; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: 700 !important; color: #1e2d3d !important; }
.insight-box { background:#fff8f0; border-left:4px solid #f39c12; border-radius:8px; padding:12px 16px; margin:6px 0; font-size:14px; color:#333; }
.insight-good { background:#f0fff4; border-left:4px solid #27ae60; border-radius:8px; padding:12px 16px; margin:6px 0; font-size:14px; color:#1a5c2a; }
.insight-alert { background:#fff0f0; border-left:4px solid #c0392b; border-radius:8px; padding:12px 16px; margin:6px 0; font-size:14px; color:#7b1a1a; }
.section-title { font-size:16px; font-weight:600; color:#1e2d3d; margin:20px 0 10px; border-bottom:2px solid #c0392b; padding-bottom:6px; }
</style>
""", unsafe_allow_html=True)

COLORS = ['#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad',
          '#16a085','#d35400','#e74c3c','#3498db','#2ecc71']

# ─── CHARGEMENT ───────────────────────────────────────────

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

# ─── DÉTECTION INTELLIGENTE ───────────────────────────────

ID_KEYWORDS = [
    'id','n°','no','num','numero','numéro','code','ref','référence',
    'reference','matricule','immatricul','identifiant','key','pk','fk',
    'index','indice','serial','sequence','contrat','client','compte',
    'dossier','facture','commande','ticket','case','order','invoice'
]

DATE_KEYWORDS = [
    'date','année','annee','mois','jour','trimestre','semaine',
    'period','time','year','month','day','quarter'
]

MEASURE_KEYWORDS = [
    'montant','somme','total','chiffre','revenu','ca','budget','charge',
    'salaire','prix','cout','coût','marge','consommation','quantite',
    'qte','volume','poids','surface','duree','durée','heure','score',
    'taux','pourcentage','ratio','valeur','amount','value','sales',
    'revenue','cost','profit','loss','gain','depense','recette','solde',
    'balance','stock','niveau','capacite','puissance','energie'
]

def is_id_column(col_name, series):
    """Détecte si une colonne est un identifiant (à ne pas sommer)"""
    name_lower = col_name.lower().replace(' ', '').replace('_', '').replace('-', '')
    # Vérifie le nom
    for kw in ID_KEYWORDS:
        kw_clean = kw.replace(' ', '').replace('_', '').replace('-', '')
        if kw_clean in name_lower:
            return True
    # Vérifie si les valeurs sont des identifiants séquentiels ou quasi-uniques
    n_unique = series.nunique()
    n_total = len(series.dropna())
    if n_total == 0:
        return False
    uniqueness = n_unique / n_total
    # Si presque tous les valeurs sont uniques → identifiant
    if uniqueness > 0.9:
        return True
    # Si les valeurs ressemblent à des numéros séquentiels
    vals = pd.to_numeric(series, errors='coerce').dropna()
    if len(vals) > 10:
        if vals.min() >= 1 and vals.max() > 1000 and uniqueness > 0.5:
            return True
    return False

def is_date_like(col_name):
    name_lower = col_name.lower()
    for kw in DATE_KEYWORDS:
        if kw in name_lower:
            return True
    return False

def classify_numeric_cols(df):
    """
    Sépare les colonnes numériques en :
    - measure_cols  : vraies mesures business (à sommer/moyenner)
    - id_cols       : identifiants numériques (à traiter comme catégories)
    - date_num_cols : année/mois/jour numériques
    """
    measure_cols, id_cols, date_num_cols = [], [], []
    for col in df.select_dtypes(include='number').columns:
        name_lower = col.lower()
        # Date-like numérique (Année, Mois, etc.)
        if is_date_like(col):
            date_num_cols.append(col)
            continue
        # Identifiant
        if is_id_column(col, df[col]):
            id_cols.append(col)
            continue
        # Mesure business explicite
        is_measure = any(kw in name_lower for kw in MEASURE_KEYWORDS)
        if is_measure:
            measure_cols.append(col)
            continue
        # Par défaut : si peu de valeurs uniques → catégorie, sinon mesure
        uniqueness = df[col].nunique() / max(len(df[col].dropna()), 1)
        if uniqueness < 0.05:
            id_cols.append(col)  # traité comme cat
        else:
            measure_cols.append(col)

    return measure_cols, id_cols, date_num_cols

def detect_cols(df):
    num_raw, cat_cols, date_cols = [], [], []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            num_raw.append(col)
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
            continue
        cleaned = s.astype(str).str.replace(r'\s','',regex=True).str.replace(',','.',regex=False)
        try:
            cv = pd.to_numeric(cleaned, errors='coerce')
            if cv.notna().sum() / len(s) > 0.8:
                df[col] = pd.to_numeric(cleaned, errors='coerce')
                num_raw.append(col)
                continue
        except Exception:
            pass
        try:
            cd = pd.to_datetime(s, errors='coerce', dayfirst=True)
            if cd.notna().sum() / len(s) > 0.7:
                df[col] = cd
                date_cols.append(col)
                continue
        except Exception:
            pass
        cat_cols.append(col)

    measure_cols, id_cols, date_num_cols = classify_numeric_cols(df)

    # Les colonnes ID numériques → traiter comme catégories (ne pas sommer)
    # Les date_num → on les garde comme infos temporelles
    all_cat = cat_cols + id_cols
    all_date = date_cols + date_num_cols

    return measure_cols, all_cat, all_date

def detect_domain(df, measure_cols, cat_cols):
    all_cols = ' '.join(df.columns).lower()
    keywords = {
        'financier':    ['montant','revenu','chiffre','budget','charge','salaire','prix','marge','facture','paiement'],
        'rh':           ['employe','effectif','absence','conge','poste','departement','agent','personnel','formation'],
        'stocks':       ['stock','produit','quantite','inventaire','article','magasin','entrepot','livraison'],
        'operationnel': ['production','qualite','delai','incident','maintenance','intervention','anomalie','panne'],
        'informatique': ['pc','ordinateur','imprimante','bureau','portable','processeur','materiel','reseau'],
        'commercial':   ['client','contrat','commande','vente','region','zone','commercial','agence','consommation'],
    }
    scores = {d: sum(1 for kw in kws if kw in all_cols) for d, kws in keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'général'

def fmt(val):
    if pd.isna(val): return "N/A"
    val = float(val)
    if abs(val) >= 1_000_000_000: return f"{val/1_000_000_000:.2f} Md"
    if abs(val) >= 1_000_000:     return f"{val/1_000_000:.2f} M"
    if abs(val) >= 1_000:         return f"{val/1_000:.1f} K"
    if val == int(val):           return f"{int(val):,}"
    return f"{val:,.2f}"

def chart_style(fig, h=300):
    fig.update_layout(
        margin=dict(t=45,b=10,l=10,r=10), height=h,
        showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11, color='#333'),
        title_font_size=14, title_font_color='#1e2d3d'
    )
    return fig

def business_insights(df, measure_cols, cat_cols, domain):
    insights = []
    # Qualité données
    missing_cols = [(c, df[c].isna().sum()) for c in df.columns if df[c].isna().sum() > 0]
    if not missing_cols:
        insights.append(('good', "✅ Aucune valeur manquante — données complètes."))
    else:
        worst = max(missing_cols, key=lambda x: x[1])
        pct_miss = round(worst[1]/len(df)*100, 1)
        if pct_miss > 10:
            insights.append(('alert', f"🔴 **{worst[0]}** : {pct_miss}% de valeurs manquantes."))
        else:
            insights.append(('good', f"✅ Qualité correcte — moins de 10% de valeurs manquantes."))

    # Analyse mesures
    for col in measure_cols[:3]:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) == 0: continue
        mean_v = vals.mean()
        max_v = vals.max()
        if mean_v != 0:
            top_pct = (max_v - mean_v) / abs(mean_v) * 100
            if top_pct > 200:
                insights.append(('alert', f"⚠️ **{col}** : valeur max ({fmt(max_v)}) très élevée par rapport à la moyenne ({fmt(mean_v)}) — vérifier les anomalies."))

    # Concentration catégorielle
    for col in cat_cols[:2]:
        vc = df[col].value_counts()
        if len(vc) == 0: continue
        top_share = vc.iloc[0] / len(df) * 100
        if top_share > 50:
            insights.append(('box', f"📌 **{col}** : « {vc.index[0]} » représente {round(top_share)}% des données."))

    insights.append(('box', f"📋 **{len(df):,} enregistrements** · **{len(df.columns)} colonnes** · Domaine détecté : **{domain.upper()}**"))
    return insights

# ─── BARRE LATÉRALE ──────────────────────────────────────

with st.sidebar:
    st.markdown("### 📁 Importer les données")
    uploaded = st.file_uploader(
        "Fichier Excel ou CSV",
        type=["xlsx","xls","csv"],
        help="Tout type de données accepté"
    )

    df = None
    measure_cols, cat_cols, date_cols = [], [], []

    if uploaded:
        fb = uploaded.read()
        ext = uploaded.name.split('.')[-1].lower()
        try:
            if ext in ['xlsx','xls']:
                xl = pd.ExcelFile(BytesIO(fb))
                sheets = xl.sheet_names
                sheet = st.selectbox("Feuille", sheets) if len(sheets) > 1 else sheets[0]
                df = load_excel(fb, sheet)
            else:
                df = load_csv(fb)
        except Exception as e:
            st.error(f"Erreur : {e}")

        if df is not None:
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
            measure_cols, cat_cols, date_cols = detect_cols(df)
            domain = detect_domain(df, measure_cols, cat_cols)

            st.success(f"✅ {len(df):,} lignes · {len(df.columns)} colonnes")
            st.caption(f"Domaine : **{domain.upper()}**")
            if measure_cols:
                st.caption(f"Mesures : {', '.join(measure_cols[:3])}{'…' if len(measure_cols)>3 else ''}")

            st.divider()
            st.markdown("### 🔽 Filtres")
            filters = {}
            for col in cat_cols[:5]:
                vals = sorted(df[col].dropna().astype(str).unique().tolist())
                if 2 <= len(vals) <= 40:
                    sel = st.multiselect(col, vals, default=[], key=f"f_{col}")
                    if sel:
                        filters[col] = sel
            for col, vals in filters.items():
                df = df[df[col].astype(str).isin(vals)]
            if filters:
                st.caption(f"Après filtre : {len(df):,} lignes")

# ─── ACCUEIL ─────────────────────────────────────────────

if df is None:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px">
      <div style="font-size:64px">📊</div>
      <h1 style="color:#1e2d3d;font-size:28px;margin:16px 0 8px">Tableau de bord</h1>
      <p style="color:#666;font-size:16px;max-width:500px;margin:0 auto">
        Importez votre fichier Excel ou CSV dans la barre latérale.<br>
        Le tableau de bord s'adapte automatiquement à vos données.
      </p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col, icon, label in zip([c1,c2,c3,c4],
        ["📈","⚙️","👥","📦"],
        ["Financier\nCA · Budget · Charges","Opérationnel\nProduction · Qualité","RH\nEffectifs · Absences","Stocks / Ventes\nInventaire · Commandes"]):
        with col:
            st.markdown(f"""<div style="background:white;border-radius:12px;padding:20px;text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.06)"><div style="font-size:32px">{icon}</div>
            <p style="font-size:13px;color:#333;margin:8px 0 0;white-space:pre-line">{label}</p></div>""",
            unsafe_allow_html=True)
    st.stop()

domain = detect_domain(df, measure_cols, cat_cols)

DOMAIN_ICONS = {'financier':'💰','rh':'👥','stocks':'📦','operationnel':'⚙️','informatique':'💻','commercial':'🤝','général':'📊'}
icon = DOMAIN_ICONS.get(domain, '📊')

# ─── EN-TÊTE ─────────────────────────────────────────────

st.markdown(f"""
<div style="background:#1e2d3d;padding:18px 24px;border-radius:14px;margin-bottom:20px;
     display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
  <div>
    <span style="color:white;font-size:20px;font-weight:700">{icon} Tableau de bord — {uploaded.name}</span>
    <br><span style="color:#8899aa;font-size:12px">{len(df):,} enregistrements · {len(df.columns)} colonnes · Domaine : {domain.upper()}</span>
  </div>
  <span style="background:#c0392b;color:white;padding:7px 16px;border-radius:8px;font-size:13px;font-weight:600">Tableau de bord</span>
</div>
""", unsafe_allow_html=True)

# ─── KPI — UNIQUEMENT LES VRAIES MESURES ─────────────────

if measure_cols:
    kpi_show = measure_cols[:5]
    n = len(kpi_show) + 1
    kpi_grid = st.columns(n)
    with kpi_grid[0]:
        st.metric("Total enregistrements", f"{len(df):,}")
    for i, col in enumerate(kpi_show):
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals):
            with kpi_grid[i+1]:
                st.metric(
                    label=col[:22],
                    value=fmt(vals.sum()),
                    delta=f"Moyenne : {fmt(vals.mean())}"
                )
else:
    st.metric("Total enregistrements", f"{len(df):,}")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ─── INSIGHTS ────────────────────────────────────────────

insights = business_insights(df, measure_cols, cat_cols, domain)
with st.expander("💡 Analyse automatique du tableau de bord", expanded=True):
    for kind, msg in insights:
        css = 'insight-good' if kind=='good' else ('insight-alert' if kind=='alert' else 'insight-box')
        st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)

st.divider()

# ─── ONGLETS ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble","🔍 Analyse détaillée","🗂️ Données"])

# ══ ONGLET 1 ═════════════════════════════════════════════
with tab1:

    # Répartitions catégorielles
    show_cats = [c for c in cat_cols if 2 <= df[c].nunique() <= 30][:6]
    if show_cats:
        st.markdown('<div class="section-title">Répartitions</div>', unsafe_allow_html=True)
        pairs = [show_cats[i:i+2] for i in range(0, len(show_cats), 2)]
        for pair in pairs:
            cols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with cols[ci]:
                    counts = df[col].astype(str).value_counts().head(10).reset_index()
                    counts.columns = [col, 'Nombre']
                    total = counts['Nombre'].sum()
                    counts['%'] = (counts['Nombre']/total*100).round(1)
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

    # Évolution temporelle automatique
    if date_cols and measure_cols:
        st.markdown('<div class="section-title">Évolution dans le temps</div>', unsafe_allow_html=True)
        best_date = date_cols[0]
        best_meas = measure_cols[0]
        try:
            ts = df[[best_date, best_meas]].copy()
            ts[best_date] = pd.to_datetime(ts[best_date], errors='coerce', dayfirst=True)
            ts = ts.dropna().sort_values(best_date)
            ts_g = ts.groupby(best_date)[best_meas].sum().reset_index()
            fig_t = px.area(ts_g, x=best_date, y=best_meas,
                            color_discrete_sequence=[COLORS[0]],
                            title=f"Évolution de {best_meas}")
            fig_t.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig_t, h=280)
            st.plotly_chart(fig_t, use_container_width=True)
        except Exception:
            pass

    # Top / Bas classement
    if show_cats and measure_cols:
        st.markdown('<div class="section-title">Classements</div>', unsafe_allow_html=True)
        best_cat = show_cats[0]
        best_val = measure_cols[0]
        grouped = (df.groupby(best_cat)[best_val]
                   .sum().reset_index()
                   .sort_values(best_val, ascending=False))
        c1, c2 = st.columns(2)
        with c1:
            top5 = grouped.head(5)
            fig_top = px.bar(top5, x=best_val, y=best_cat, orientation='h',
                             color=best_cat, color_discrete_sequence=COLORS,
                             title=f"Top 5 — {best_cat}")
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            chart_style(fig_top)
            st.plotly_chart(fig_top, use_container_width=True)
        with c2:
            flop5 = grouped.tail(5).sort_values(best_val)
            fig_flop = px.bar(flop5, x=best_val, y=best_cat, orientation='h',
                              color=best_cat, color_discrete_sequence=COLORS[::-1],
                              title=f"Bas du classement — {best_cat}")
            fig_flop.update_layout(yaxis={'categoryorder':'total ascending'})
            chart_style(fig_flop)
            st.plotly_chart(fig_flop, use_container_width=True)

# ══ ONGLET 2 ═════════════════════════════════════════════
with tab2:
    all_cat_for_analysis = [c for c in cat_cols if 2 <= df[c].nunique() <= 50]

    if all_cat_for_analysis and measure_cols:
        st.markdown('<div class="section-title">Analyse croisée</div>', unsafe_allow_html=True)
        h1,h2,h3,h4 = st.columns(4)
        with h1: x_col = st.selectbox("Catégorie", all_cat_for_analysis, key="xc")
        with h2: y_col = st.selectbox("Valeur", measure_cols, key="yc")
        with h3: agg = st.selectbox("Calcul", ["Somme","Moyenne","Nombre","Maximum","Minimum"], key="ag")
        with h4: top_n = st.slider("Top N", 5, 25, 10, key="topn")

        agg_map = {"Somme":"sum","Moyenne":"mean","Nombre":"count","Maximum":"max","Minimum":"min"}
        grouped = (df.groupby(x_col)[y_col]
                   .agg(agg_map[agg]).reset_index()
                   .sort_values(y_col, ascending=False).head(top_n))
        fig2 = px.bar(grouped, x=x_col, y=y_col,
                      color=x_col, color_discrete_sequence=COLORS,
                      title=f"{agg} de {y_col} par {x_col}", text=y_col)
        fig2.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        chart_style(fig2, h=380)
        st.plotly_chart(fig2, use_container_width=True)

    if date_cols and measure_cols:
        st.markdown('<div class="section-title">Évolution personnalisée</div>', unsafe_allow_html=True)
        h1,h2,h3 = st.columns(3)
        with h1: tc = st.selectbox("Date", date_cols, key="tc2")
        with h2: vc = st.selectbox("Valeur", measure_cols, key="vc2")
        with h3: cc = st.selectbox("Découper par", ["Aucun"] + all_cat_for_analysis, key="cc2") if all_cat_for_analysis else "Aucun"
        try:
            cols_need = [tc, vc] + ([cc] if cc != "Aucun" else [])
            ts2 = df[cols_need].copy()
            ts2[tc] = pd.to_datetime(ts2[tc], errors='coerce', dayfirst=True)
            ts2 = ts2.dropna(subset=[tc]).sort_values(tc)
            if cc != "Aucun":
                ts2_g = ts2.groupby([tc, cc])[vc].sum().reset_index()
                fig3 = px.line(ts2_g, x=tc, y=vc, color=cc,
                               color_discrete_sequence=COLORS,
                               title=f"{vc} dans le temps par {cc}")
                fig3.update_layout(showlegend=True)
            else:
                ts2_g = ts2.groupby(tc)[vc].sum().reset_index()
                fig3 = px.area(ts2_g, x=tc, y=vc,
                               color_discrete_sequence=[COLORS[0]],
                               title=f"{vc} dans le temps")
                fig3.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig3, h=340)
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossible de tracer : {e}")

    if len(all_cat_for_analysis) >= 2 and measure_cols:
        st.markdown('<div class="section-title">Comparaison croisée</div>', unsafe_allow_html=True)
        h1,h2,h3 = st.columns(3)
        with h1: c1s = st.selectbox("Catégorie 1", all_cat_for_analysis, key="c1s")
        with h2:
            rem = [c for c in all_cat_for_analysis if c != c1s]
            c2s = st.selectbox("Catégorie 2", rem, key="c2s") if rem else None
        with h3: vs = st.selectbox("Valeur", measure_cols, key="vs2")
        if c2s:
            grouped2 = df.groupby([c1s, c2s])[vs].sum().reset_index()
            fig4 = px.bar(grouped2, x=c1s, y=vs, color=c2s,
                          color_discrete_sequence=COLORS, barmode='group',
                          title=f"{vs} par {c1s} et {c2s}")
            chart_style(fig4, h=360).update_layout(showlegend=True)
            st.plotly_chart(fig4, use_container_width=True)

# ══ ONGLET 3 ═════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns([3,1])
    with c1:
        search = st.text_input("Rechercher", "", key="search", placeholder="Rechercher dans les données…")
    with c2:
        sort_col = st.selectbox("Trier par", ["—"] + list(df.columns), key="sort_col")

    display_df = df.copy()
    if search:
        mask = display_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]
    if sort_col != "—":
        display_df = display_df.sort_values(sort_col, ascending=False)

    st.dataframe(display_df, height=440, use_container_width=True)
    st.caption(f"{len(display_df):,} lignes affichées sur {len(df):,}")

    c1, c2 = st.columns(2)
    with c1:
        buf = BytesIO()
        display_df.to_excel(buf, index=False)
        st.download_button("📥 Exporter en Excel", buf.getvalue(),
                           "tableau_de_bord.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button("📥 Exporter en CSV",
                           display_df.to_csv(index=False, sep=';').encode('utf-8-sig'),
                           "tableau_de_bord.csv", "text/csv")

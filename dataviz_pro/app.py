import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

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
div[data-testid="stMetric"] [data-testid="stMetricDelta"] { font-size: 12px !important; }
.chart-card {
    background: white; border-radius: 12px; padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px;
}
.insight-box {
    background: #fff8f0; border-left: 4px solid #f39c12;
    border-radius: 8px; padding: 12px 16px; margin: 8px 0;
    font-size: 14px; color: #333;
}
.insight-good {
    background: #f0fff4; border-left: 4px solid #27ae60;
    border-radius: 8px; padding: 12px 16px; margin: 8px 0;
    font-size: 14px; color: #1a5c2a;
}
.insight-alert {
    background: #fff0f0; border-left: 4px solid #c0392b;
    border-radius: 8px; padding: 12px 16px; margin: 8px 0;
    font-size: 14px; color: #7b1a1a;
}
.section-title {
    font-size: 16px; font-weight: 600; color: #1e2d3d;
    margin: 20px 0 10px; border-bottom: 2px solid #c0392b;
    padding-bottom: 6px;
}
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

# ─── DÉTECTION INTELLIGENTE DES COLONNES ──────────────────

def detect_cols(df):
    num, cat, date = [], [], []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            num.append(col)
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date.append(col)
            continue
        cleaned = s.astype(str).str.replace(r'\s','',regex=True).str.replace(',','.',regex=False)
        try:
            cv = pd.to_numeric(cleaned, errors='coerce')
            if cv.notna().sum() / len(s) > 0.8:
                df[col] = pd.to_numeric(cleaned, errors='coerce')
                num.append(col)
                continue
        except Exception:
            pass
        try:
            cd = pd.to_datetime(s, errors='coerce', dayfirst=True)
            if cd.notna().sum() / len(s) > 0.7:
                df[col] = cd
                date.append(col)
                continue
        except Exception:
            pass
        cat.append(col)
    return num, cat, date

# ─── DÉTECTION DU TYPE MÉTIER ─────────────────────────────

def detect_domain(df, num, cat, date):
    all_cols = ' '.join(df.columns).lower()
    keywords = {
        'financier':    ['montant','chiffre','revenu','vente','ca','budget','charge','salaire','prix','cout','marge','facture','paiement','recette','depense'],
        'rh':           ['employe','effectif','absence','conge','poste','departement','service','agent','personnel','formation','recrutement'],
        'stocks':       ['stock','produit','quantite','inventaire','article','reference','magasin','entrepot','commande','livraison'],
        'operationnel': ['production','qualite','delai','incident','ticket','maintenance','intervention','anomalie','panne','equipe'],
        'informatique': ['pc','ordinateur','imprimante','bureau','portable','processeur','marque','materiel','reseau','serveur'],
        'commercial':   ['client','contrat','prospect','commande','vente','region','zone','commercial','agence','partenaire'],
    }
    scores = {d: 0 for d in keywords}
    for domain, kws in keywords.items():
        for kw in kws:
            if kw in all_cols:
                scores[domain] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'général'

# ─── FORMATAGE ────────────────────────────────────────────

def fmt(val):
    if pd.isna(val): return "N/A"
    val = float(val)
    if abs(val) >= 1_000_000_000: return f"{val/1_000_000_000:.2f} Md"
    if abs(val) >= 1_000_000:     return f"{val/1_000_000:.2f} M"
    if abs(val) >= 1_000:         return f"{val/1_000:.1f} K"
    if val == int(val):           return f"{int(val):,}"
    return f"{val:,.2f}"

def pct(a, b):
    return f"{round(a/b*100,1)} %" if b else "N/A"

def chart_style(fig, h=300):
    fig.update_layout(
        margin=dict(t=40,b=10,l=10,r=10), height=h,
        showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11, color='#333'),
        title_font_size=14, title_font_color='#1e2d3d'
    )
    return fig

# ─── GÉNÉRATION D'INSIGHTS BUSINESS ──────────────────────

def business_insights(df, num, cat, date, domain):
    insights = []
    # Top valeur
    for col in num[:3]:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) == 0: continue
        top_pct = (vals.max() - vals.mean()) / vals.mean() * 100 if vals.mean() != 0 else 0
        if top_pct > 50:
            insights.append(('alert', f"⚠️ **{col}** : la valeur maximale ({fmt(vals.max())}) est {round(top_pct)}% au-dessus de la moyenne — vérifier les anomalies."))
        low_pct = (vals.mean() - vals.min()) / vals.mean() * 100 if vals.mean() != 0 else 0
        if low_pct > 80:
            insights.append(('alert', f"📉 **{col}** : certaines valeurs sont très basses ({fmt(vals.min())}) par rapport à la moyenne ({fmt(vals.mean())})."))

    # Concentration catégorielle
    for col in cat[:2]:
        vc = df[col].value_counts()
        if len(vc) == 0: continue
        top_share = vc.iloc[0] / len(df) * 100
        if top_share > 50:
            insights.append(('box', f"📌 **{col}** : « {vc.index[0]} » représente {round(top_share)}% des données — forte concentration."))
        if len(vc) >= 2:
            top2 = (vc.iloc[0] + vc.iloc[1]) / len(df) * 100
            if top2 > 70:
                insights.append(('good', f"✅ **{col}** : les 2 premières catégories couvrent {round(top2)}% des enregistrements."))

    # Données manquantes
    missing_cols = [(c, df[c].isna().sum()) for c in df.columns if df[c].isna().sum() > 0]
    if missing_cols:
        worst = max(missing_cols, key=lambda x: x[1])
        pct_miss = round(worst[1]/len(df)*100, 1)
        if pct_miss > 10:
            insights.append(('alert', f"🔴 **{worst[0]}** : {pct_miss}% de valeurs manquantes — données incomplètes."))
        else:
            insights.append(('good', f"✅ Qualité des données correcte — moins de 10% de valeurs manquantes."))
    else:
        insights.append(('good', "✅ Aucune valeur manquante — données complètes."))

    # Volume
    insights.append(('box', f"📋 Tableau de bord chargé : **{len(df):,} enregistrements** · **{len(df.columns)} colonnes** · Domaine détecté : **{domain.upper()}**"))

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
    num_cols, cat_cols, date_cols = [], [], []

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
            num_cols, cat_cols, date_cols = detect_cols(df)
            domain = detect_domain(df, num_cols, cat_cols, date_cols)

            st.success(f"✅ {len(df):,} lignes · {len(df.columns)} colonnes")
            st.caption(f"Domaine détecté : **{domain.upper()}**")

            st.divider()
            st.markdown("### 🔽 Filtres rapides")
            filters = {}
            for col in cat_cols[:4]:
                vals = sorted(df[col].dropna().astype(str).unique().tolist())
                if 2 <= len(vals) <= 40:
                    sel = st.multiselect(col, vals, default=[], key=f"f_{col}")
                    if sel:
                        filters[col] = sel
            for col, vals in filters.items():
                df = df[df[col].astype(str).isin(vals)]
            if filters:
                st.caption(f"Après filtre : {len(df):,} lignes")

# ─── PAGE D'ACCUEIL ──────────────────────────────────────

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

    c1, c2, c3, c4 = st.columns(4)
    for col, icon, label in zip(
        [c1,c2,c3,c4],
        ["📈","⚙️","👥","📦"],
        ["Financier\nCA · Budget · Charges","Opérationnel\nProduction · Qualité","RH\nEffectifs · Absences","Stocks / Ventes\nInventaire · Commandes"]
    ):
        with col:
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
              <div style="font-size:32px">{icon}</div>
              <p style="font-size:13px;color:#333;margin:8px 0 0;white-space:pre-line">{label}</p>
            </div>""", unsafe_allow_html=True)
    st.stop()

domain = detect_domain(df, num_cols, cat_cols, date_cols)

# ─── EN-TÊTE ─────────────────────────────────────────────

DOMAIN_ICONS = {
    'financier':'💰','rh':'👥','stocks':'📦',
    'operationnel':'⚙️','informatique':'💻','commercial':'🤝','général':'📊'
}
icon = DOMAIN_ICONS.get(domain, '📊')

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

# ─── KPI CARTES ──────────────────────────────────────────

kpi_num = [c for c in num_cols if df[c].nunique() > 5][:4]
n = len(kpi_num) + 1
kpi_grid = st.columns(n)

with kpi_grid[0]:
    st.metric("Total enregistrements", f"{len(df):,}")

for i, col in enumerate(kpi_num):
    vals = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(vals):
        with kpi_grid[i+1]:
            st.metric(
                label=col[:20],
                value=fmt(vals.sum()),
                delta=f"Moyenne : {fmt(vals.mean())}"
            )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ─── INSIGHTS BUSINESS ───────────────────────────────────

insights = business_insights(df, num_cols, cat_cols, date_cols, domain)
with st.expander("💡 Analyse automatique du tableau de bord", expanded=True):
    for kind, msg in insights:
        css = 'insight-good' if kind=='good' else ('insight-alert' if kind=='alert' else 'insight-box')
        st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)

st.divider()

# ─── ONGLETS ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "📊 Vue d'ensemble",
    "🔍 Analyse détaillée",
    "🗂️ Données"
])

# ══ ONGLET 1 : VUE D'ENSEMBLE ════════════════════════════
with tab1:

    # ── Répartitions catégorielles ──
    if cat_cols:
        st.markdown('<div class="section-title">Répartitions principales</div>', unsafe_allow_html=True)
        show_cats = [c for c in cat_cols if 2 <= df[c].nunique() <= 30][:6]
        pairs = [show_cats[i:i+2] for i in range(0, len(show_cats), 2)]
        for pair in pairs:
            cols = st.columns(len(pair))
            for ci, col in enumerate(pair):
                with cols[ci]:
                    counts = df[col].astype(str).value_counts().head(10).reset_index()
                    counts.columns = [col, 'Nombre']
                    total = counts['Nombre'].sum()
                    counts['%'] = (counts['Nombre'] / total * 100).round(1)

                    if len(counts) <= 6:
                        fig = px.pie(counts, names=col, values='Nombre',
                                     color_discrete_sequence=COLORS, hole=0.5,
                                     title=col)
                        fig.update_traces(textinfo='percent+label', textposition='inside')
                    else:
                        fig = px.bar(counts, x='Nombre', y=col, orientation='h',
                                     color=col, color_discrete_sequence=COLORS,
                                     title=col, text='%')
                        fig.update_traces(texttemplate='%{text}%', textposition='outside')
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})

                    chart_style(fig)
                    st.plotly_chart(fig, use_container_width=True)

    # ── Évolution temporelle ──
    if date_cols and num_cols:
        st.markdown('<div class="section-title">Évolution dans le temps</div>', unsafe_allow_html=True)
        best_date = date_cols[0]
        best_num = kpi_num[0] if kpi_num else num_cols[0]

        try:
            ts = df[[best_date, best_num]].copy()
            ts[best_date] = pd.to_datetime(ts[best_date], errors='coerce', dayfirst=True)
            ts = ts.dropna().sort_values(best_date)
            ts_g = ts.groupby(best_date)[best_num].sum().reset_index()

            fig_t = px.area(ts_g, x=best_date, y=best_num,
                            color_discrete_sequence=[COLORS[0]],
                            title=f"Évolution de {best_num}")
            fig_t.update_traces(fillcolor='rgba(192,57,43,0.1)', line_color='#c0392b')
            chart_style(fig_t, h=280)
            st.plotly_chart(fig_t, use_container_width=True)
        except Exception:
            pass

    # ── Top / Flop si catégorie + numérique ──
    if cat_cols and kpi_num:
        st.markdown('<div class="section-title">Classements</div>', unsafe_allow_html=True)
        best_cat = cat_cols[0]
        best_val = kpi_num[0]

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

# ══ ONGLET 2 : ANALYSE DÉTAILLÉE ═════════════════════════
with tab2:

    # ── Analyse croisée ──
    if cat_cols and num_cols:
        st.markdown('<div class="section-title">Analyse croisée</div>', unsafe_allow_html=True)
        h1, h2, h3, h4 = st.columns(4)
        with h1: x_col = st.selectbox("Catégorie", cat_cols, key="xc")
        with h2: y_col = st.selectbox("Valeur", num_cols, key="yc")
        with h3: agg = st.selectbox("Calcul", ["Somme","Moyenne","Nombre","Maximum","Minimum"], key="ag")
        with h4: top_n = st.slider("Afficher top", 5, 20, 10, key="topn")

        agg_map = {"Somme":"sum","Moyenne":"mean","Nombre":"count","Maximum":"max","Minimum":"min"}
        grouped = (df.groupby(x_col)[y_col]
                   .agg(agg_map[agg]).reset_index()
                   .sort_values(y_col, ascending=False).head(top_n))

        fig2 = px.bar(grouped, x=x_col, y=y_col,
                      color=x_col, color_discrete_sequence=COLORS,
                      title=f"{agg} de {y_col} par {x_col}",
                      text=y_col)
        fig2.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        chart_style(fig2, h=380)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Évolution personnalisée ──
    if date_cols and num_cols:
        st.markdown('<div class="section-title">Évolution personnalisée</div>', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: tc = st.selectbox("Date", date_cols, key="tc2")
        with h2: vc = st.selectbox("Valeur", num_cols, key="vc2")
        with h3: cc = st.selectbox("Découper par", ["Aucun"] + cat_cols, key="cc2") if cat_cols else "Aucun"

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

    # ── Comparaison entre catégories ──
    if len(cat_cols) >= 2 and num_cols:
        st.markdown('<div class="section-title">Comparaison croisée</div>', unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        with h1: c1s = st.selectbox("Catégorie 1", cat_cols, key="c1s")
        with h2:
            remaining = [c for c in cat_cols if c != c1s]
            c2s = st.selectbox("Catégorie 2", remaining, key="c2s") if remaining else None
        with h3: vs = st.selectbox("Valeur", num_cols, key="vs2")

        if c2s:
            grouped2 = df.groupby([c1s, c2s])[vs].sum().reset_index()
            fig4 = px.bar(grouped2, x=c1s, y=vs, color=c2s,
                          color_discrete_sequence=COLORS,
                          barmode='group',
                          title=f"{vs} par {c1s} et {c2s}")
            chart_style(fig4, h=360).update_layout(showlegend=True)
            st.plotly_chart(fig4, use_container_width=True)

# ══ ONGLET 3 : DONNÉES ═══════════════════════════════════
with tab3:
    c1, c2 = st.columns([3,1])
    with c1:
        search = st.text_input("Rechercher", "", key="search", placeholder="Rechercher dans les données…")
    with c2:
        sort_col = st.selectbox("Trier par", ["—"] + list(df.columns), key="sort_col")

    display_df = df.copy()
    if search:
        mask = display_df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
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

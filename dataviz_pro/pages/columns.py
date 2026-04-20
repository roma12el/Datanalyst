import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats

RED = "#E8002D"
GREEN = "#16A34A"
ORANGE = "#EA580C"
DARK = "#09090B"


def fmt(val):
    if abs(val) >= 1e6: return f"{val/1e6:.1f}M"
    if abs(val) >= 1e3: return f"{val/1e3:.1f}K"
    return f"{val:.2f}"


def show(df):
    st.markdown('<div class="page-title">Analyse <span>des colonnes</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Sélectionnez une colonne pour obtenir les insights clés.</div>', unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    tab_num, tab_cat = st.tabs(["🔢  Colonnes numériques", "🔤  Colonnes catégorielles"])

    # ── NUMÉRIQUES ────────────────────────────────────────────────────────────
    with tab_num:
        if not num_cols:
            st.info("Aucune colonne numérique détectée.")
        else:
            col_sel = st.selectbox("Colonne", num_cols, key="col_num")
            s = df[col_sel].dropna()
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            outliers = s[(s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)]
            skew = s.skew()

            # ── Verdict décisionnel ──────────────────────────────────────────
            st.markdown('<div class="section-header">Verdict pour la prise de décision</div>', unsafe_allow_html=True)
            verdicts = []

            if df[col_sel].isnull().sum() > 0:
                pct_miss = round(100 * df[col_sel].isnull().sum() / len(df), 1)
                verdicts.append(("red", f"⚠️ <strong>{pct_miss}% de valeurs manquantes</strong> dans cette colonne — données incomplètes."))

            if len(outliers) / len(s) > 0.05:
                verdicts.append(("orange", f"⚠️ <strong>{len(outliers)} valeurs aberrantes ({round(100*len(outliers)/len(s),1)}%)</strong> — vérifier si elles sont réelles ou erreurs de saisie."))

            if abs(skew) > 1.5:
                verdicts.append(("orange", f"📐 <strong>Distribution asymétrique</strong> (skew={skew:.2f}) — utilisez la <strong>médiane</strong> ({fmt(s.median())}) plutôt que la moyenne ({fmt(s.mean())}) pour vos décisions."))

            cv = s.std() / abs(s.mean()) if s.mean() != 0 else 0
            if cv > 1:
                verdicts.append(("orange", f"📊 <strong>Forte variabilité</strong> (CV={cv:.1f}) — les données sont très dispersées. Méfiez-vous des moyennes."))

            if not verdicts:
                verdicts.append(("green", "✅ <strong>Colonne fiable</strong> — distribution acceptable pour des analyses et décisions."))

            for color, msg in verdicts:
                st.markdown(f'<div class="alert-{color}">{msg}</div>', unsafe_allow_html=True)

            # ── Stats ────────────────────────────────────────────────────────
            st.markdown('<div class="section-header">Statistiques essentielles</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            pairs = [
                (c1, "Médiane", fmt(s.median())),
                (c2, "Moyenne", fmt(s.mean())),
                (c3, "Minimum", fmt(s.min())),
                (c4, "Maximum", fmt(s.max())),
                (c5, "Écart-type", fmt(s.std())),
                (c6, "Outliers", str(len(outliers))),
            ]
            for col, label, val in pairs:
                col.metric(label, val)

            # ── Graphiques ───────────────────────────────────────────────────
            st.markdown('<div class="section-header">Visualisation</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)

            with c1:
                # Histogram
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=s, nbinsx=25, marker_color=RED, marker_line_color="white",
                    marker_line_width=0.5, opacity=0.85, name="Distribution"
                ))
                # Médiane line
                fig.add_vline(x=s.median(), line_dash="dash", line_color=DARK, line_width=2,
                              annotation_text=f"Médiane {fmt(s.median())}",
                              annotation_position="top right",
                              annotation_font=dict(size=11, color=DARK))
                fig.update_layout(
                    template="plotly_white", height=300, showlegend=False,
                    margin=dict(t=20, b=30, l=40, r=20),
                    paper_bgcolor="white", plot_bgcolor="white",
                    font=dict(family="Inter", size=11),
                    xaxis=dict(gridcolor="#F4F4F5"),
                    yaxis=dict(gridcolor="#F4F4F5"),
                    title=dict(text="Distribution", font=dict(size=13, color=DARK))
                )
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                # Box plot
                fig2 = go.Figure()
                fig2.add_trace(go.Box(
                    y=s, name=col_sel,
                    marker_color=RED, line_color=RED,
                    fillcolor="rgba(232,0,45,0.08)",
                    boxpoints="outliers",
                    boxmean=True,
                    marker=dict(size=4, opacity=0.6)
                ))
                fig2.update_layout(
                    template="plotly_white", height=300, showlegend=False,
                    margin=dict(t=20, b=30, l=40, r=20),
                    paper_bgcolor="white", plot_bgcolor="white",
                    font=dict(family="Inter", size=11),
                    yaxis=dict(gridcolor="#F4F4F5"),
                    title=dict(text="Boxplot & Outliers", font=dict(size=13, color=DARK))
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Outliers table
            if not outliers.empty:
                with st.expander(f"Voir les {len(outliers)} valeurs aberrantes"):
                    st.dataframe(
                        outliers.reset_index().rename(columns={"index": "Ligne", col_sel: "Valeur"}),
                        use_container_width=True, height=200
                    )

    # ── CATÉGORIELLES ─────────────────────────────────────────────────────────
    with tab_cat:
        if not cat_cols:
            st.info("Aucune colonne catégorielle détectée.")
        else:
            col_sel = st.selectbox("Colonne", cat_cols, key="col_cat")
            vc = df[col_sel].value_counts()
            n_unique = df[col_sel].nunique()
            top_pct = round(100 * vc.iloc[0] / df[col_sel].count(), 1)
            missing_n = df[col_sel].isnull().sum()

            # Verdict
            st.markdown('<div class="section-header">Verdict pour la prise de décision</div>', unsafe_allow_html=True)
            verdicts = []

            if missing_n > 0:
                verdicts.append(("orange", f"⚠️ <strong>{missing_n} valeurs manquantes</strong> dans cette colonne."))
            if top_pct > 70:
                verdicts.append(("orange", f"⚠️ <strong>Concentration élevée</strong> : \"{vc.index[0]}\" représente {top_pct}% — peu de diversité."))
            if n_unique > 50:
                verdicts.append(("orange", f"🔤 <strong>{n_unique} valeurs uniques</strong> — haute cardinalité. Envisagez un regroupement."))
            if not verdicts:
                verdicts.append(("green", f"✅ <strong>Colonne exploitable</strong> — {n_unique} valeurs uniques, distribution raisonnable."))

            for color, msg in verdicts:
                st.markdown(f'<div class="alert-{color}">{msg}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">Top valeurs</div>', unsafe_allow_html=True)

            top_n = st.slider("Afficher les top N", 5, 30, 10, key="cat_top")
            vc_top = vc.head(top_n)

            fig = go.Figure(go.Bar(
                x=vc_top.values,
                y=vc_top.index.astype(str),
                orientation="h",
                marker_color=[RED] + ["#E4E4E7"] * (len(vc_top) - 1),
                marker_line_width=0,
                text=[f"{v:,}  ({100*v/len(df):.1f}%)" for v in vc_top.values],
                textposition="outside",
                textfont=dict(size=11, family="Inter")
            ))
            fig.update_layout(
                template="plotly_white", height=max(250, 32 * top_n), showlegend=False,
                margin=dict(t=10, b=10, l=10, r=80),
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Inter", size=11),
                xaxis=dict(visible=False),
                yaxis=dict(gridcolor="#F4F4F5"),
            )
            st.plotly_chart(fig, use_container_width=True)

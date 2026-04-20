import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

RED = "#E8002D"
GREEN = "#16A34A"
ORANGE = "#EA580C"
DARK = "#09090B"


def fmt(val):
    if abs(val) >= 1e9: return f"{val/1e9:.1f}B"
    if abs(val) >= 1e6: return f"{val/1e6:.1f}M"
    if abs(val) >= 1e3: return f"{val/1e3:.1f}K"
    return f"{val:.2f}"


def show(df, filename):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    missing_pct = round(100 * df.isnull().sum().sum() / (df.shape[0] * df.shape[1]), 2)
    duplicates = int(df.duplicated().sum())
    n_rows, n_cols = df.shape

    st.markdown(f'<div class="page-title">Vue d\'ensemble <span>·</span> {filename}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{n_rows:,} lignes · {n_cols} colonnes · analysé automatiquement</div>', unsafe_allow_html=True)

    # ── Santé des données ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Qualité des données</div>', unsafe_allow_html=True)

    health_score = 100
    if missing_pct > 0: health_score -= min(40, missing_pct * 2)
    if duplicates > 0: health_score -= min(20, duplicates / n_rows * 100)
    health_score = max(0, round(health_score))
    health_color = GREEN if health_score >= 80 else (ORANGE if health_score >= 50 else RED)
    health_label = "Excellent" if health_score >= 80 else ("Attention" if health_score >= 50 else "Critique")

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "Score qualité", f"{health_score}/100", health_label, "danger" if health_score < 50 else ("good" if health_score >= 80 else "")),
        (c2, "Lignes", f"{n_rows:,}", "enregistrements", ""),
        (c3, "Colonnes", str(n_cols), f"{len(num_cols)} num · {len(cat_cols)} cat", ""),
        (c4, "Données manquantes", f"{missing_pct}%", "à traiter" if missing_pct > 0 else "Aucun manquant", "danger" if missing_pct > 10 else ("good" if missing_pct == 0 else "")),
        (c5, "Doublons", str(duplicates), "lignes identiques" if duplicates > 0 else "Aucun doublon", "danger" if duplicates > 0 else "good"),
    ]
    for col, label, val, sub, cls in cards:
        with col:
            st.markdown(f"""
            <div class="kpi {cls}">
                <div class="label">{label}</div>
                <div class="val">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # Alertes qualité
    st.markdown("")
    if missing_pct == 0 and duplicates == 0:
        st.markdown('<div class="alert-green">✅ <strong>Données propres</strong> — aucune valeur manquante, aucun doublon détecté.</div>', unsafe_allow_html=True)
    if missing_pct > 20:
        st.markdown(f'<div class="alert-red">🚨 <strong>{missing_pct}% de valeurs manquantes</strong> — impacte fortement la fiabilité des analyses. Action requise avant toute décision.</div>', unsafe_allow_html=True)
    elif missing_pct > 0:
        st.markdown(f'<div class="alert-orange">⚠️ <strong>{missing_pct}% de valeurs manquantes</strong> — à imputer ou supprimer selon le contexte.</div>', unsafe_allow_html=True)
    if duplicates > 0:
        pct_dup = round(100 * duplicates / n_rows, 1)
        st.markdown(f'<div class="alert-orange">⚠️ <strong>{duplicates} lignes dupliquées ({pct_dup}%)</strong> — risque de double comptage dans vos agrégations.</div>', unsafe_allow_html=True)

    # ── KPIs numériques ──────────────────────────────────────────────────────
    if num_cols:
        st.markdown('<div class="section-header">Indicateurs clés</div>', unsafe_allow_html=True)
        cols = st.columns(min(4, len(num_cols)))
        for i, col in enumerate(num_cols[:4]):
            s = df[col].dropna()
            total = s.sum()
            mean = s.mean()
            with cols[i]:
                st.markdown(f"""
                <div class="kpi">
                    <div class="label">Σ {col[:22]}</div>
                    <div class="val">{fmt(total)}</div>
                    <div class="sub">Moy. {fmt(mean)}</div>
                </div>""", unsafe_allow_html=True)

    # ── Distribution rapide ───────────────────────────────────────────────────
    if num_cols:
        st.markdown('<div class="section-header">Distribution des variables numériques</div>', unsafe_allow_html=True)

        col_sel = st.selectbox("Variable à visualiser", num_cols, key="ov_col")
        s = df[col_sel].dropna()
        skew = s.skew()

        c1, c2 = st.columns([3, 1])
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=s, nbinsx=30,
                marker_color=RED, marker_line_color="white",
                marker_line_width=0.5, opacity=0.85, name=""
            ))
            fig.update_layout(
                template="plotly_white", height=280, showlegend=False,
                margin=dict(t=10, b=30, l=40, r=20),
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Inter", size=11),
                xaxis=dict(gridcolor="#F4F4F5", title=col_sel),
                yaxis=dict(gridcolor="#F4F4F5", title="Fréquence"),
                hoverlabel=dict(bgcolor="white", font_family="Inter")
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            outliers = s[(s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)]
            stats_items = [
                ("Médiane", fmt(s.median())),
                ("Moyenne", fmt(s.mean())),
                ("Min", fmt(s.min())),
                ("Max", fmt(s.max())),
                ("Asymétrie", f"{skew:.2f}"),
                ("Outliers", str(len(outliers))),
            ]
            for label, val in stats_items:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:6px 0;
                            border-bottom:1px solid #F4F4F5;font-size:0.8rem;">
                    <span style="color:#A1A1AA">{label}</span>
                    <span style="font-weight:600;color:#09090B">{val}</span>
                </div>""", unsafe_allow_html=True)

            if abs(skew) > 1.5:
                st.markdown(f'<div class="alert-orange" style="margin-top:8px;font-size:0.75rem">Distribution asymétrique — la moyenne peut être trompeuse. Privilégiez la médiane.</div>', unsafe_allow_html=True)
            if len(outliers) > 0:
                pct = round(100 * len(outliers) / len(s), 1)
                st.markdown(f'<div class="alert-orange" style="margin-top:8px;font-size:0.75rem">{len(outliers)} valeurs aberrantes ({pct}%) — à vérifier avant toute décision.</div>', unsafe_allow_html=True)

    # ── Top catégories ────────────────────────────────────────────────────────
    if cat_cols:
        st.markdown('<div class="section-header">Répartition catégorielle</div>', unsafe_allow_html=True)
        cat_sel = st.selectbox("Variable catégorielle", cat_cols, key="ov_cat")
        vc = df[cat_sel].value_counts().head(10)

        fig2 = go.Figure(go.Bar(
            x=vc.values, y=vc.index.astype(str),
            orientation="h",
            marker_color=[RED if i == 0 else "#E4E4E7" for i in range(len(vc))],
            marker_line_width=0,
            text=[f"{v:,} ({100*v/len(df):.0f}%)" for v in vc.values],
            textposition="outside",
            textfont=dict(size=11, family="Inter")
        ))
        fig2.update_layout(
            template="plotly_white", height=320, showlegend=False,
            margin=dict(t=10, b=10, l=10, r=80),
            paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Inter", size=11),
            xaxis=dict(gridcolor="#F4F4F5", visible=False),
            yaxis=dict(gridcolor="#F4F4F5"),
        )
        st.plotly_chart(fig2, use_container_width=True)

        top_val = vc.index[0]
        top_pct = round(100 * vc.iloc[0] / df[cat_sel].count(), 1)
        if top_pct > 50:
            st.markdown(f'<div class="alert-orange">⚠️ <strong>"{top_val}"</strong> représente {top_pct}% des données — forte concentration sur une seule valeur.</div>', unsafe_allow_html=True)

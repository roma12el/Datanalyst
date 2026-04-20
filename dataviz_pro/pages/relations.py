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


def show(df):
    st.markdown('<div class="page-title">Relations <span>entre variables</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Quelles variables sont liées ? Quelles influences identifier ?</div>', unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if len(num_cols) < 2:
        st.info("Il faut au moins 2 colonnes numériques pour analyser les relations.")
        return

    # ── Matrice de corrélation simplifiée ────────────────────────────────────
    st.markdown('<div class="section-header">Corrélations — ce qui varie ensemble</div>', unsafe_allow_html=True)

    corr = df[num_cols].corr().round(2)

    # Afficher les corrélations fortes sous forme d'alertes
    pairs = (
        corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        .stack().reset_index()
    )
    pairs.columns = ["Var A", "Var B", "r"]
    pairs["abs_r"] = pairs["r"].abs()
    strong = pairs[pairs["abs_r"] >= 0.6].sort_values("abs_r", ascending=False)

    if not strong.empty:
        st.markdown("**Relations significatives détectées :**")
        for _, row in strong.head(8).iterrows():
            direction = "positivement" if row["r"] > 0 else "négativement"
            strength = "très fortement" if row["abs_r"] >= 0.85 else ("fortement" if row["abs_r"] >= 0.7 else "modérément")
            color = "red" if row["abs_r"] >= 0.85 else "orange"
            st.markdown(f"""
            <div class="alert-{color}">
                📊 <strong>{row['Var A']}</strong> et <strong>{row['Var B']}</strong> sont 
                {strength} liées {direction} (r = {row['r']:.2f})
                {'— risque de redondance si utilisées ensemble.' if row['abs_r'] >= 0.85 else ''}
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-green">✅ Aucune corrélation forte (|r| ≥ 0.6) — vos variables sont relativement indépendantes.</div>', unsafe_allow_html=True)

    # Heatmap épurée
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(), y=corr.index.tolist(),
        colorscale=[[0, "#1E40AF"], [0.5, "#FFFFFF"], [1, RED]],
        zmid=0, zmin=-1, zmax=1,
        text=corr.values, texttemplate="%{text:.2f}",
        textfont={"size": 11, "family": "Inter"},
        colorbar=dict(thickness=10, len=0.8, title="r")
    ))
    fig.update_layout(
        template="plotly_white",
        height=max(350, 55 * len(num_cols)),
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Inter", size=11),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Exploration manuelle ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">Explorer une relation spécifique</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    x_col = c1.selectbox("Variable X", num_cols, key="rel_x")
    y_col = c2.selectbox("Variable Y", num_cols, index=min(1, len(num_cols)-1), key="rel_y")

    color_col = None
    if cat_cols:
        color_opt = st.selectbox("Colorer par (optionnel)", ["—"] + cat_cols, key="rel_c")
        color_col = None if color_opt == "—" else color_opt

    valid = df[[x_col, y_col]].dropna()
    if len(valid) > 2:
        r, p = stats.pearsonr(valid[x_col], valid[y_col])

        # Interprétation
        strength = (
            "très forte" if abs(r) >= 0.85 else
            "forte" if abs(r) >= 0.7 else
            "modérée" if abs(r) >= 0.4 else
            "faible"
        )
        direction = "positive" if r > 0 else "négative"
        sig = p < 0.05

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Corrélation r", f"{r:.3f}")
        col_b.metric("R²", f"{r**2:.3f}", delta=f"{round(r**2*100,1)}% variance expliquée")
        col_c.metric("Significativité", "✅ Oui" if sig else "❌ Non", delta=f"p={p:.4f}")

        color_sig = "green" if sig else "orange"
        if sig:
            st.markdown(f'<div class="alert-{color_sig}">📊 Relation <strong>{strength} {direction}</strong> entre ces deux variables (statistiquement significative). {"Quand l'un augmente, l'autre aussi." if r > 0 else "Quand l'un augmente, l'autre diminue."}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-orange">ℹ️ La relation observée n\'est <strong>pas statistiquement significative</strong> (p={p:.4f}) — peut être due au hasard.</div>', unsafe_allow_html=True)

        fig2 = px.scatter(
            df, x=x_col, y=y_col, color=color_col,
            trendline="ols",
            color_discrete_sequence=[RED] if not color_col else px.colors.qualitative.Set1,
            opacity=0.7,
        )
        fig2.update_layout(
            template="plotly_white", height=400,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Inter", size=11),
            xaxis=dict(gridcolor="#F4F4F5", title=x_col),
            yaxis=dict(gridcolor="#F4F4F5", title=y_col),
            showlegend=bool(color_col),
            hoverlabel=dict(bgcolor="white", font_family="Inter")
        )
        fig2.update_traces(marker=dict(size=6))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Comparaison num × catég ───────────────────────────────────────────────
    if cat_cols and num_cols:
        st.markdown('<div class="section-header">Comparaison par groupe</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        num_col = c1.selectbox("Valeur numérique", num_cols, key="grp_num")
        cat_col = c2.selectbox("Grouper par", cat_cols, key="grp_cat")

        top_cats = df[cat_col].value_counts().head(8).index.tolist()
        filtered = df[df[cat_col].isin(top_cats)]

        group_stats = filtered.groupby(cat_col)[num_col].agg(["mean", "median", "count"]).reset_index()
        group_stats.columns = [cat_col, "Moyenne", "Médiane", "N"]
        group_stats = group_stats.sort_values("Médiane", ascending=False)

        # ANOVA
        groups = [filtered[filtered[cat_col] == c][num_col].dropna() for c in top_cats]
        groups = [g for g in groups if len(g) >= 2]
        if len(groups) >= 2:
            try:
                f_stat, p_anova = stats.f_oneway(*groups)
                if p_anova < 0.05:
                    best = group_stats.iloc[0]
                    worst = group_stats.iloc[-1]
                    st.markdown(f'<div class="alert-red">📊 <strong>Différence significative entre les groupes</strong> (p={p_anova:.4f}) — "{best[cat_col]}" a la médiane la plus haute ({fmt(best["Médiane"])}), "{worst[cat_col]}" la plus basse ({fmt(worst["Médiane"])}).</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-green">ℹ️ Pas de différence significative entre les groupes (p={p_anova:.4f}).</div>', unsafe_allow_html=True)
            except Exception:
                pass

        fig3 = go.Figure()
        for i, (_, row) in enumerate(group_stats.iterrows()):
            fig3.add_trace(go.Bar(
                x=[row[cat_col]],
                y=[row["Médiane"]],
                name=str(row[cat_col]),
                marker_color=RED if i == 0 else "#E4E4E7",
                marker_line_width=0,
                text=[fmt(row["Médiane"])],
                textposition="outside",
                textfont=dict(size=11)
            ))
        fig3.update_layout(
            template="plotly_white", height=320, showlegend=False,
            margin=dict(t=20, b=40, l=50, r=20),
            paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Inter", size=11),
            xaxis=dict(gridcolor="#F4F4F5", title=cat_col),
            yaxis=dict(gridcolor="#F4F4F5", title=f"Médiane — {num_col}"),
            title=dict(text=f"Médiane de {num_col} par {cat_col}", font=dict(size=13))
        )
        st.plotly_chart(fig3, use_container_width=True)

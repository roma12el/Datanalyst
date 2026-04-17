import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


def show(df):
    st.markdown('<p class="section-title">🔗 Corrélations & Analyse bivariée</p>', unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    TEMPLATE = "plotly_white"

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌡️ Matrice de corrélation",
        "📊 Scatter & Bubble",
        "📉 Scatter Matrix",
        "🔢 Num × Catég"
    ])

    # ── CORRÉLATION ──────────────────────────────────────────────────────
    with tab1:
        if len(num_cols) < 2:
            st.info("Besoin d'au moins 2 colonnes numériques.")
        else:
            method = st.radio("Méthode", ["pearson", "spearman", "kendall"], horizontal=True)
            corr = df[num_cols].corr(method=method).round(3)

            fig = go.Figure(go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale="RdBu",
                zmid=0, zmin=-1, zmax=1,
                text=corr.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Corrélation")
            ))
            fig.update_layout(
                title=f"Matrice de corrélation — {method.title()}",
                height=max(500, 50 * len(num_cols)),
                template=TEMPLATE
            )
            st.plotly_chart(fig, use_container_width=True)

            # Top corrélations
            st.markdown("#### Top corrélations (valeur absolue)")
            corr_pairs = (
                corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                .stack()
                .reset_index()
            )
            corr_pairs.columns = ["Var A", "Var B", "Corrélation"]
            corr_pairs["|Corrélation|"] = corr_pairs["Corrélation"].abs()
            corr_pairs = corr_pairs.sort_values("|Corrélation|", ascending=False).head(20)

            col1, col2 = st.columns([2, 1])
            with col1:
                fig2 = px.bar(
                    corr_pairs.head(10),
                    x="Corrélation", y=corr_pairs.head(10).apply(lambda r: f"{r['Var A']} × {r['Var B']}", axis=1),
                    orientation="h",
                    color="Corrélation", color_continuous_scale="RdBu",
                    range_color=[-1, 1],
                    title="Top 10 corrélations"
                )
                fig2.update_layout(height=400, template=TEMPLATE)
                st.plotly_chart(fig2, use_container_width=True)
            with col2:
                st.dataframe(corr_pairs.drop(columns="|Corrélation|").round(3), height=400)

    # ── SCATTER ──────────────────────────────────────────────────────────
    with tab2:
        if len(num_cols) < 2:
            st.info("Besoin d'au moins 2 colonnes numériques.")
        else:
            col1, col2 = st.columns(2)
            x_col = col1.selectbox("Axe X", num_cols, index=0, key="sc_x")
            y_col = col2.selectbox("Axe Y", num_cols, index=min(1, len(num_cols) - 1), key="sc_y")

            col3, col4, col5 = st.columns(3)
            color_col = col3.selectbox("Couleur (optionnel)", ["—"] + cat_cols + num_cols, key="sc_c")
            size_col = col4.selectbox("Taille (optionnel)", ["—"] + num_cols, key="sc_s")
            trendline = col5.selectbox("Tendance", ["Aucune", "OLS", "LOWESS"], key="sc_t")

            trend_arg = None if trendline == "Aucune" else ("ols" if trendline == "OLS" else "lowess")
            color_arg = None if color_col == "—" else color_col
            size_arg = None if size_col == "—" else size_col

            # Filter out negative/zero for size
            plot_df = df.copy()
            if size_arg and (plot_df[size_arg] <= 0).any():
                plot_df[size_arg] = plot_df[size_arg].clip(lower=0.01)

            fig = px.scatter(
                plot_df, x=x_col, y=y_col,
                color=color_arg, size=size_arg,
                trendline=trend_arg,
                hover_data=df.columns.tolist()[:5],
                title=f"Scatter — {x_col} vs {y_col}",
                opacity=0.7,
                color_continuous_scale="Viridis" if color_arg and color_arg in num_cols else None
            )
            fig.update_layout(height=550, template=TEMPLATE)
            st.plotly_chart(fig, use_container_width=True)

            # Stats
            valid = df[[x_col, y_col]].dropna()
            if len(valid) > 2:
                r, p = stats.pearsonr(valid[x_col], valid[y_col])
                rho, p2 = stats.spearmanr(valid[x_col], valid[y_col])
                c1, c2, c3 = st.columns(3)
                c1.metric("Pearson r", f"{r:.4f}", delta=f"p={p:.4f}")
                c2.metric("Spearman ρ", f"{rho:.4f}", delta=f"p={p2:.4f}")
                c3.metric("R²", f"{r**2:.4f}")

    # ── SCATTER MATRIX ───────────────────────────────────────────────────
    with tab3:
        if len(num_cols) < 2:
            st.info("Besoin d'au moins 2 colonnes numériques.")
        else:
            max_cols = st.slider("Nombre de variables (max)", 2, min(8, len(num_cols)), min(5, len(num_cols)))
            selected = num_cols[:max_cols]
            color_cat = st.selectbox("Couleur catégorielle (optionnel)", ["—"] + cat_cols, key="sm_c")
            color_arg = None if color_cat == "—" else color_cat

            fig = px.scatter_matrix(
                df, dimensions=selected, color=color_arg,
                title="Scatter Matrix (SPLOM)",
                opacity=0.6,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(diagonal_visible=True, showupperhalf=False)
            fig.update_layout(
                height=max(600, 120 * max_cols),
                template=TEMPLATE
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── NUM × CATÉG ──────────────────────────────────────────────────────
    with tab4:
        if not num_cols or not cat_cols:
            st.info("Besoin d'au moins une colonne numérique et une catégorielle.")
        else:
            col1, col2 = st.columns(2)
            num_col = col1.selectbox("Colonne numérique", num_cols, key="nc_n")
            cat_col = col2.selectbox("Colonne catégorielle", cat_cols, key="nc_c")

            top_n = st.slider("Top N catégories", 5, 30, 10, key="nc_top")
            top_cats = df[cat_col].value_counts().head(top_n).index.tolist()
            filtered = df[df[cat_col].isin(top_cats)]

            chart_choice = st.radio(
                "Graphique",
                ["Box par catégorie", "Violin par catégorie", "Bar (moyenne)", "Strip plot"],
                horizontal=True, key="nc_chart"
            )

            if chart_choice == "Box par catégorie":
                fig = px.box(
                    filtered, x=cat_col, y=num_col,
                    color=cat_col, points="outliers",
                    title=f"{num_col} par {cat_col}"
                )
            elif chart_choice == "Violin par catégorie":
                fig = px.violin(
                    filtered, x=cat_col, y=num_col,
                    color=cat_col, box=True, points="outliers",
                    title=f"{num_col} par {cat_col}"
                )
            elif chart_choice == "Bar (moyenne)":
                agg = filtered.groupby(cat_col)[num_col].agg(["mean", "std", "count"]).reset_index()
                agg.columns = [cat_col, "Moyenne", "Écart-type", "N"]
                fig = px.bar(
                    agg, x=cat_col, y="Moyenne",
                    error_y="Écart-type",
                    color="Moyenne",
                    color_continuous_scale="Blues",
                    title=f"Moyenne de {num_col} par {cat_col}"
                )
            else:
                fig = px.strip(
                    filtered, x=cat_col, y=num_col,
                    color=cat_col,
                    title=f"Strip plot — {num_col} par {cat_col}"
                )

            fig.update_layout(height=500, template=TEMPLATE, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # ANOVA / Kruskal
            groups = [filtered[filtered[cat_col] == c][num_col].dropna() for c in top_cats]
            groups = [g for g in groups if len(g) >= 2]
            if len(groups) >= 2:
                try:
                    f_stat, p_anova = stats.f_oneway(*groups)
                    h_stat, p_kruskal = stats.kruskal(*groups)
                    c1, c2 = st.columns(2)
                    c1.metric("ANOVA F-stat", f"{f_stat:.3f}", delta=f"p={p_anova:.4f}")
                    c2.metric("Kruskal-Wallis H", f"{h_stat:.3f}", delta=f"p={p_kruskal:.4f}")
                    if p_anova < 0.05:
                        st.success("✅ Différence significative entre groupes (p < 0.05)")
                    else:
                        st.info("ℹ️ Pas de différence significative entre groupes (p ≥ 0.05)")
                except Exception:
                    pass
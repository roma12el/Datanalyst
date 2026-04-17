import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

RED = "#E8002D"
DARK = "#171717"
TEMPLATE = "plotly_white"


def apex_layout(fig, title="", height=450):
    fig.update_layout(
        template=TEMPLATE, height=height,
        title=dict(text=title, font=dict(family="DM Sans", size=14, color=DARK), x=0),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="DM Sans", color="#404040"),
        margin=dict(t=50, b=40, l=50, r=30),
        hoverlabel=dict(bgcolor="white", bordercolor="#E5E5E5", font_family="DM Sans", font_size=12),
    )
    fig.update_xaxes(gridcolor="#F2F2F2", linecolor="#E5E5E5")
    fig.update_yaxes(gridcolor="#F2F2F2", linecolor="#E5E5E5")
    return fig


def show(df):
    st.markdown("""
    <div class="page-header">
        <div>
            <div class="page-title">CORRELATIONS &amp;<span> BIVARIATE</span></div>
            <div class="page-subtitle">Correlation matrices · Scatter plots · ANOVA · Statistical tests</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌡️  Correlation Matrix",
        "📊  Scatter & Bubble",
        "📉  Scatter Matrix",
        "🔢  Num × Category"
    ])

    # ── CORRELATION ───────────────────────────────────────────────────────────
    with tab1:
        if len(num_cols) < 2:
            st.info("Need at least 2 numeric columns.")
        else:
            method = st.radio("Method", ["pearson", "spearman", "kendall"], horizontal=True)
            corr = df[num_cols].corr(method=method).round(3)

            fig = go.Figure(go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(), y=corr.index.tolist(),
                colorscale=[[0, "#1E40AF"], [0.5, "#FFFFFF"], [1, RED]],
                zmid=0, zmin=-1, zmax=1,
                text=corr.values.round(2), texttemplate="%{text}",
                textfont={"size": 10, "family": "JetBrains Mono"},
                colorbar=dict(title="Correlation", thickness=12, len=0.8)
            ))
            apex_layout(fig, f"Correlation Matrix — {method.title()}", max(500, 50 * len(num_cols)))
            st.plotly_chart(fig, use_container_width=True)

            corr_pairs = (
                corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                .stack().reset_index()
            )
            corr_pairs.columns = ["Var A", "Var B", "Correlation"]
            corr_pairs["|r|"] = corr_pairs["Correlation"].abs()
            corr_pairs = corr_pairs.sort_values("|r|", ascending=False).head(20)

            col1, col2 = st.columns([2, 1])
            with col1:
                top10 = corr_pairs.head(10).copy()
                top10["Pair"] = top10.apply(lambda r: f"{r['Var A']} × {r['Var B']}", axis=1)
                fig2 = px.bar(
                    top10, x="Correlation", y="Pair", orientation="h",
                    color="Correlation",
                    color_continuous_scale=[[0, "#1E40AF"], [0.5, "#FFFFFF"], [1, RED]],
                    range_color=[-1, 1],
                )
                fig2.update_traces(texttemplate="%{x:.3f}", textposition="outside",
                                   textfont=dict(size=10, family="JetBrains Mono"))
                apex_layout(fig2, "Top 10 Correlations", 420)
                st.plotly_chart(fig2, use_container_width=True)
            with col2:
                st.dataframe(corr_pairs.drop(columns="|r|").round(3), height=420, use_container_width=True)

    # ── SCATTER ───────────────────────────────────────────────────────────────
    with tab2:
        if len(num_cols) < 2:
            st.info("Need at least 2 numeric columns.")
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            x_col = c1.selectbox("X Axis", num_cols, index=0, key="sc_x")
            y_col = c2.selectbox("Y Axis", num_cols, index=min(1, len(num_cols)-1), key="sc_y")
            color_col = c3.selectbox("Color", ["—"] + cat_cols + num_cols, key="sc_c")
            size_col = c4.selectbox("Size", ["—"] + num_cols, key="sc_s")
            trendline = c5.selectbox("Trendline", ["None", "OLS", "LOWESS"], key="sc_t")

            trend_arg = None if trendline == "None" else ("ols" if trendline == "OLS" else "lowess")
            color_arg = None if color_col == "—" else color_col
            size_arg = None if size_col == "—" else size_col

            plot_df = df.copy()
            if size_arg and (plot_df[size_arg] <= 0).any():
                plot_df[size_arg] = plot_df[size_arg].clip(lower=0.01)

            fig = px.scatter(
                plot_df, x=x_col, y=y_col, color=color_arg, size=size_arg,
                trendline=trend_arg, hover_data=df.columns.tolist()[:5],
                opacity=0.7,
                color_continuous_scale=[[0, "#FFB3C1"], [1, RED]] if color_arg and color_arg in num_cols else None,
                color_discrete_sequence=px.colors.qualitative.Set1 if color_arg and color_arg in cat_cols else None,
            )
            apex_layout(fig, f"Scatter — {x_col} vs {y_col}", 550)
            st.plotly_chart(fig, use_container_width=True)

            valid = df[[x_col, y_col]].dropna()
            if len(valid) > 2:
                r, p = stats.pearsonr(valid[x_col], valid[y_col])
                rho, p2 = stats.spearmanr(valid[x_col], valid[y_col])
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Pearson r", f"{r:.4f}", delta=f"p={p:.4f}")
                c2.metric("Spearman ρ", f"{rho:.4f}", delta=f"p={p2:.4f}")
                c3.metric("R²", f"{r**2:.4f}")
                strength = "Strong" if abs(r) > 0.7 else "Moderate" if abs(r) > 0.4 else "Weak"
                direction = "positive" if r > 0 else "negative"
                c4.markdown(f'<div class="insight-card"><strong>{strength} {direction} correlation</strong></div>', unsafe_allow_html=True)

    # ── SCATTER MATRIX ────────────────────────────────────────────────────────
    with tab3:
        if len(num_cols) < 2:
            st.info("Need at least 2 numeric columns.")
        else:
            c1, c2 = st.columns(2)
            max_cols = c1.slider("Variables (max)", 2, min(8, len(num_cols)), min(5, len(num_cols)))
            color_cat = c2.selectbox("Color by", ["—"] + cat_cols, key="sm_c")
            color_arg = None if color_cat == "—" else color_cat
            selected = num_cols[:max_cols]

            fig = px.scatter_matrix(
                df, dimensions=selected, color=color_arg,
                opacity=0.6,
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            fig.update_traces(diagonal_visible=True, showupperhalf=False,
                              marker=dict(size=3))
            apex_layout(fig, "Scatter Matrix (SPLOM)", max(600, 120 * max_cols))
            st.plotly_chart(fig, use_container_width=True)

    # ── NUM × CATEG ───────────────────────────────────────────────────────────
    with tab4:
        if not num_cols or not cat_cols:
            st.info("Need at least one numeric and one categorical column.")
        else:
            c1, c2, c3 = st.columns(3)
            num_col = c1.selectbox("Numeric column", num_cols, key="nc_n")
            cat_col = c2.selectbox("Categorical column", cat_cols, key="nc_c")
            top_n = c3.slider("Top N categories", 5, 30, 10, key="nc_top")
            chart_choice = st.radio(
                "Chart", ["Box by Category", "Violin by Category", "Bar (Mean)", "Strip Plot"],
                horizontal=True, key="nc_chart"
            )

            top_cats = df[cat_col].value_counts().head(top_n).index.tolist()
            filtered = df[df[cat_col].isin(top_cats)]

            palette = px.colors.qualitative.Set1
            if chart_choice == "Box by Category":
                fig = px.box(filtered, x=cat_col, y=num_col, color=cat_col,
                             points="outliers", color_discrete_sequence=palette)
            elif chart_choice == "Violin by Category":
                fig = px.violin(filtered, x=cat_col, y=num_col, color=cat_col,
                                box=True, points="outliers", color_discrete_sequence=palette)
            elif chart_choice == "Bar (Mean)":
                agg = filtered.groupby(cat_col)[num_col].agg(["mean", "std"]).reset_index()
                agg.columns = [cat_col, "Mean", "Std"]
                fig = px.bar(agg, x=cat_col, y="Mean", error_y="Std",
                             color="Mean", color_continuous_scale=[[0, "#FFB3C1"], [1, RED]])
                fig.update_layout(coloraxis_showscale=False)
            else:
                fig = px.strip(filtered, x=cat_col, y=num_col, color=cat_col,
                               color_discrete_sequence=palette)

            apex_layout(fig, f"{num_col} by {cat_col}", 520)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            groups = [filtered[filtered[cat_col] == c][num_col].dropna() for c in top_cats]
            groups = [g for g in groups if len(g) >= 2]
            if len(groups) >= 2:
                try:
                    f_stat, p_anova = stats.f_oneway(*groups)
                    h_stat, p_kruskal = stats.kruskal(*groups)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("ANOVA F-stat", f"{f_stat:.3f}", delta=f"p={p_anova:.4f}")
                    c2.metric("Kruskal-Wallis H", f"{h_stat:.3f}", delta=f"p={p_kruskal:.4f}")
                    if p_anova < 0.05:
                        c3.markdown('<div class="insight-card">✅ <strong>Significant difference</strong> between groups (p &lt; 0.05)</div>', unsafe_allow_html=True)
                    else:
                        c3.markdown('<div class="insight-card">ℹ️ <strong>No significant difference</strong> between groups (p ≥ 0.05)</div>', unsafe_allow_html=True)
                except Exception:
                    pass

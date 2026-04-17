import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(df):
    st.markdown('<p class="section-title">🎯 Tableau de bord KPI</p>', unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    TEMPLATE = "plotly_white"

    if not num_cols:
        st.warning("Aucune colonne numérique disponible pour les KPIs.")
        return

    # ── KPI Auto ──────────────────────────────────────────────────────────
    st.markdown("#### 📌 KPIs automatiques")
    cols = st.columns(min(5, len(num_cols)))
    for i, col in enumerate(num_cols[:5]):
        with cols[i]:
            total = df[col].sum()
            mean = df[col].mean()
            if abs(total) > 1e6:
                disp = f"{total/1e6:.2f}M"
            elif abs(total) > 1e3:
                disp = f"{total/1e3:.1f}K"
            else:
                disp = f"{total:.2f}"
            st.metric(label=f"Σ {col}", value=disp, delta=f"μ={mean:.2f}")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Barres & Funnel",
        "🥧 Donut & Sunburst",
        "🌳 Treemap",
        "🎯 Jauges",
        "🌊 Waterfall"
    ])

    # ── BARRES & FUNNEL ──────────────────────────────────────────────────
    with tab1:
        if not cat_cols:
            st.info("Besoin d'une colonne catégorielle.")
        else:
            col1, col2 = st.columns(2)
            cat_col = col1.selectbox("Catégorie", cat_cols, key="kpi_cat")
            num_col = col2.selectbox("Valeur", num_cols, key="kpi_num")
            agg_func = st.selectbox("Agrégation", ["sum", "mean", "count", "median", "max"], key="kpi_agg")
            top_n = st.slider("Top N", 5, 30, 10, key="kpi_n")

            agg_df = (
                df.groupby(cat_col)[num_col]
                .agg(agg_func)
                .sort_values(ascending=False)
                .head(top_n)
                .reset_index()
            )
            agg_df.columns = [cat_col, "Valeur"]

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    agg_df, x=cat_col, y="Valeur",
                    color="Valeur", color_continuous_scale="Blues",
                    title=f"{agg_func.upper()} de {num_col} par {cat_col}",
                    text="Valeur"
                )
                fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
                fig.update_layout(height=450, template=TEMPLATE, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Funnel
                fig2 = go.Figure(go.Funnel(
                    y=agg_df[cat_col].astype(str),
                    x=agg_df["Valeur"],
                    textinfo="value+percent initial",
                    marker=dict(color=px.colors.sequential.Blues_r[:len(agg_df)])
                ))
                fig2.update_layout(
                    title=f"Funnel — {num_col} par {cat_col}",
                    height=450, template=TEMPLATE
                )
                st.plotly_chart(fig2, use_container_width=True)

    # ── DONUT & SUNBURST ─────────────────────────────────────────────────
    with tab2:
        if not cat_cols:
            st.info("Besoin d'une colonne catégorielle.")
        else:
            cat_col = st.selectbox("Catégorie", cat_cols, key="donut_cat")
            num_col = st.selectbox("Valeur", num_cols, key="donut_num")
            top_n = st.slider("Top N", 5, 20, 8, key="donut_n")

            agg_df = (
                df.groupby(cat_col)[num_col].sum()
                .sort_values(ascending=False)
                .head(top_n)
                .reset_index()
            )
            agg_df.columns = [cat_col, "Valeur"]

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(
                    agg_df, values="Valeur", names=cat_col,
                    hole=0.5, title=f"Donut — {num_col} par {cat_col}",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(height=450, template=TEMPLATE)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Sunburst (besoin de 2 cat si possible)
                if len(cat_cols) >= 2:
                    cat2 = st.selectbox("2ème niveau", [c for c in cat_cols if c != cat_col], key="sun_c2")
                    sun_df = (
                        df.groupby([cat_col, cat2])[num_col].sum()
                        .reset_index()
                    )
                    sun_df.columns = ["parent", "child", "value"]
                    fig2 = px.sunburst(
                        sun_df, path=["parent", "child"], values="value",
                        title=f"Sunburst — {cat_col} → {cat2}",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                else:
                    fig2 = px.sunburst(
                        agg_df, path=[cat_col], values="Valeur",
                        title=f"Sunburst — {cat_col}"
                    )
                fig2.update_layout(height=450, template=TEMPLATE)
                st.plotly_chart(fig2, use_container_width=True)

    # ── TREEMAP ──────────────────────────────────────────────────────────
    with tab3:
        if not cat_cols:
            st.info("Besoin d'une colonne catégorielle.")
        else:
            cat_col = st.selectbox("Catégorie", cat_cols, key="tree_cat")
            num_col = st.selectbox("Valeur", num_cols, key="tree_num")

            agg_df = (
                df.groupby(cat_col)[num_col].sum()
                .reset_index()
                .sort_values(num_col, ascending=False)
                .head(40)
            )
            agg_df.columns = [cat_col, "Valeur"]

            fig = px.treemap(
                agg_df,
                path=[px.Constant("Total"), cat_col],
                values="Valeur",
                color="Valeur",
                color_continuous_scale="RdYlGn",
                title=f"Treemap — {num_col} par {cat_col}"
            )
            fig.update_traces(textinfo="label+value+percent root")
            fig.update_layout(height=600, template=TEMPLATE)
            st.plotly_chart(fig, use_container_width=True)

    # ── JAUGES ───────────────────────────────────────────────────────────
    with tab4:
        st.markdown("#### Jauges KPI dynamiques")
        selected_kpis = st.multiselect(
            "Colonnes à afficher", num_cols, default=num_cols[:3]
        )
        if selected_kpis:
            gauge_cols = st.columns(len(selected_kpis))
            for i, col_name in enumerate(selected_kpis):
                s = df[col_name].dropna()
                val = s.mean()
                min_v, max_v = s.min(), s.max()
                target = s.median()

                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=round(val, 2),
                    delta={"reference": round(target, 2), "valueformat": ".2f"},
                    title={"text": col_name, "font": {"size": 14}},
                    gauge={
                        "axis": {"range": [min_v, max_v]},
                        "bar": {"color": "#667eea"},
                        "steps": [
                            {"range": [min_v, min_v + (max_v - min_v) / 3], "color": "#fadcdc"},
                            {"range": [min_v + (max_v - min_v) / 3, min_v + 2 * (max_v - min_v) / 3], "color": "#fff3cd"},
                            {"range": [min_v + 2 * (max_v - min_v) / 3, max_v], "color": "#d4edda"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75, "value": target
                        }
                    }
                ))
                fig.update_layout(height=280, template=TEMPLATE, margin=dict(t=60, b=0))
                with gauge_cols[i]:
                    st.plotly_chart(fig, use_container_width=True)

    # ── WATERFALL ────────────────────────────────────────────────────────
    with tab5:
        if not cat_cols:
            st.info("Besoin d'une colonne catégorielle.")
        else:
            cat_col = st.selectbox("Catégorie", cat_cols, key="wf_cat")
            num_col = st.selectbox("Valeur", num_cols, key="wf_num")
            top_n = st.slider("Top N", 5, 20, 10, key="wf_n")

            agg_df = (
                df.groupby(cat_col)[num_col].sum()
                .sort_values(ascending=False)
                .head(top_n)
                .reset_index()
            )
            agg_df.columns = [cat_col, "Valeur"]

            measures = ["relative"] * len(agg_df) + ["total"]
            x_vals = agg_df[cat_col].astype(str).tolist() + ["TOTAL"]
            y_vals = agg_df["Valeur"].tolist() + [agg_df["Valeur"].sum()]

            fig = go.Figure(go.Waterfall(
                name="KPI",
                orientation="v",
                measure=measures,
                x=x_vals,
                y=y_vals,
                text=[f"{v:.2s}" for v in y_vals],
                textposition="outside",
                connector={"line": {"color": "#667eea"}},
                increasing={"marker": {"color": "#27ae60"}},
                decreasing={"marker": {"color": "#c0392b"}},
                totals={"marker": {"color": "#667eea"}}
            ))
            fig.update_layout(
                title=f"Waterfall — {num_col} par {cat_col}",
                height=500, template=TEMPLATE,
                waterfallgap=0.3
            )
            st.plotly_chart(fig, use_container_width=True)

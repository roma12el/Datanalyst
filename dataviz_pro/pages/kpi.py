import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
            <div class="page-title">KPI<span> DASHBOARD</span></div>
            <div class="page-subtitle">Bars · Funnels · Donuts · Treemaps · Gauges · Waterfall</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        st.warning("No numeric columns available for KPIs.")
        return

    # ── Auto KPIs ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Auto KPIs</div>', unsafe_allow_html=True)
    cols = st.columns(min(5, len(num_cols)))
    for i, col in enumerate(num_cols[:5]):
        total = df[col].sum()
        mean = df[col].mean()
        if abs(total) > 1e9:
            disp = f"{total/1e9:.2f}B"
        elif abs(total) > 1e6:
            disp = f"{total/1e6:.2f}M"
        elif abs(total) > 1e3:
            disp = f"{total/1e3:.1f}K"
        else:
            disp = f"{total:.2f}"
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Σ {col[:18]}</div>
                <div class="value">{disp}</div>
                <div class="sub">avg {mean:.3g}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊  Bars & Funnel",
        "🥧  Donut & Sunburst",
        "🌳  Treemap",
        "🎯  Gauges",
        "🌊  Waterfall"
    ])

    # ── BARS & FUNNEL ─────────────────────────────────────────────────────────
    with tab1:
        if not cat_cols:
            st.info("Need a categorical column.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            cat_col = c1.selectbox("Category", cat_cols, key="kpi_cat")
            num_col = c2.selectbox("Value", num_cols, key="kpi_num")
            agg_func = c3.selectbox("Aggregation", ["sum", "mean", "count", "median", "max"], key="kpi_agg")
            top_n = c4.slider("Top N", 5, 30, 10, key="kpi_n")

            agg_df = (
                df.groupby(cat_col)[num_col].agg(agg_func)
                .sort_values(ascending=False).head(top_n).reset_index()
            )
            agg_df.columns = [cat_col, "Value"]

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    agg_df, x=cat_col, y="Value",
                    color="Value", color_continuous_scale=[[0, "#FFB3C1"], [1, RED]],
                    text="Value"
                )
                fig.update_traces(texttemplate="%{text:.3s}", textposition="outside",
                                  textfont=dict(family="DM Sans", size=11),
                                  marker_line_color="white", marker_line_width=0.5)
                apex_layout(fig, f"{agg_func.upper()} of {num_col} by {cat_col}", 460)
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                n = len(agg_df)
                shades = [f"rgba(232,0,45,{max(0.2, 1 - i*0.8/max(n-1,1)):.2f})" for i in range(n)]
                fig2 = go.Figure(go.Funnel(
                    y=agg_df[cat_col].astype(str),
                    x=agg_df["Value"],
                    textinfo="value+percent initial",
                    textfont=dict(family="DM Sans", size=11),
                    marker=dict(color=shades, line=dict(color="white", width=1))
                ))
                apex_layout(fig2, f"Funnel — {num_col} by {cat_col}", 460)
                st.plotly_chart(fig2, use_container_width=True)

    # ── DONUT & SUNBURST ──────────────────────────────────────────────────────
    with tab2:
        if not cat_cols:
            st.info("Need a categorical column.")
        else:
            c1, c2, c3 = st.columns(3)
            cat_col = c1.selectbox("Category", cat_cols, key="donut_cat")
            num_col = c2.selectbox("Value", num_cols, key="donut_num")
            top_n = c3.slider("Top N", 5, 20, 8, key="donut_n")

            agg_df = (
                df.groupby(cat_col)[num_col].sum()
                .sort_values(ascending=False).head(top_n).reset_index()
            )
            agg_df.columns = [cat_col, "Value"]

            col1, col2 = st.columns(2)
            with col1:
                n = len(agg_df)
                shades = [f"rgba(232,0,45,{max(0.15, 1 - i*0.75/max(n-1,1)):.2f})" for i in range(n)]
                fig = go.Figure(go.Pie(
                    values=agg_df["Value"], labels=agg_df[cat_col],
                    hole=0.58,
                    marker=dict(colors=shades, line=dict(color="white", width=3)),
                    textfont=dict(family="DM Sans", size=11)
                ))
                total = agg_df["Value"].sum()
                disp_total = f"{total/1e6:.1f}M" if total > 1e6 else f"{total/1e3:.1f}K" if total > 1e3 else f"{total:.2f}"
                fig.add_annotation(text=f"<b>{disp_total}</b><br>total",
                                   x=0.5, y=0.5, showarrow=False,
                                   font=dict(size=16, family="Bebas Neue", color=DARK))
                apex_layout(fig, f"Donut — {num_col} by {cat_col}", 460)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if len(cat_cols) >= 2:
                    cat2 = st.selectbox("2nd level", [c for c in cat_cols if c != cat_col], key="sun_c2")
                    sun_df = df.groupby([cat_col, cat2])[num_col].sum().reset_index()
                    sun_df.columns = ["parent", "child", "value"]
                    fig2 = px.sunburst(sun_df, path=["parent", "child"], values="value",
                                       color_discrete_sequence=px.colors.sequential.Reds_r)
                else:
                    fig2 = px.sunburst(agg_df, path=[cat_col], values="Value",
                                       color_discrete_sequence=px.colors.sequential.Reds_r)
                apex_layout(fig2, f"Sunburst — {cat_col}", 460)
                st.plotly_chart(fig2, use_container_width=True)

    # ── TREEMAP ───────────────────────────────────────────────────────────────
    with tab3:
        if not cat_cols:
            st.info("Need a categorical column.")
        else:
            c1, c2 = st.columns(2)
            cat_col = c1.selectbox("Category", cat_cols, key="tree_cat")
            num_col = c2.selectbox("Value", num_cols, key="tree_num")

            agg_df = (
                df.groupby(cat_col)[num_col].sum()
                .reset_index().sort_values(num_col, ascending=False).head(40)
            )
            agg_df.columns = [cat_col, "Value"]

            fig = px.treemap(
                agg_df, path=[px.Constant("All"), cat_col], values="Value",
                color="Value",
                color_continuous_scale=[[0, "#FFB3C1"], [0.5, RED], [1, "#7B0015"]],
            )
            fig.update_traces(textinfo="label+value+percent root",
                              textfont=dict(family="DM Sans", size=12))
            apex_layout(fig, f"Treemap — {num_col} by {cat_col}", 620)
            st.plotly_chart(fig, use_container_width=True)

    # ── GAUGES ────────────────────────────────────────────────────────────────
    with tab4:
        selected_kpis = st.multiselect("Columns for gauges", num_cols, default=num_cols[:3])
        if selected_kpis:
            n = len(selected_kpis)
            rows = (n + 2) // 3
            gauge_cols = st.columns(min(3, n))
            for i, col_name in enumerate(selected_kpis):
                s = df[col_name].dropna()
                val, min_v, max_v, target = s.mean(), s.min(), s.max(), s.median()
                rng = max_v - min_v if max_v > min_v else 1

                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=round(val, 2),
                    delta={"reference": round(target, 2), "valueformat": ".2f",
                           "increasing": {"color": "#22C55E"}, "decreasing": {"color": RED}},
                    title={"text": col_name, "font": {"size": 13, "family": "DM Sans", "color": DARK}},
                    number={"font": {"family": "Bebas Neue", "size": 32, "color": DARK}},
                    gauge={
                        "axis": {"range": [min_v, max_v], "tickfont": {"size": 10}},
                        "bar": {"color": RED, "thickness": 0.25},
                        "bgcolor": "white",
                        "borderwidth": 1, "bordercolor": "#E5E5E5",
                        "steps": [
                            {"range": [min_v, min_v + rng/3], "color": "#FFE4E8"},
                            {"range": [min_v + rng/3, min_v + 2*rng/3], "color": "#FFF5F5"},
                            {"range": [min_v + 2*rng/3, max_v], "color": "#F7FFF9"},
                        ],
                        "threshold": {
                            "line": {"color": DARK, "width": 3},
                            "thickness": 0.75, "value": target
                        }
                    }
                ))
                apex_layout(fig, "", 300)
                fig.update_layout(margin=dict(t=60, b=10, l=30, r=30))
                with gauge_cols[i % 3]:
                    st.plotly_chart(fig, use_container_width=True)

    # ── WATERFALL ─────────────────────────────────────────────────────────────
    with tab5:
        if not cat_cols:
            st.info("Need a categorical column.")
        else:
            c1, c2, c3 = st.columns(3)
            cat_col = c1.selectbox("Category", cat_cols, key="wf_cat")
            num_col = c2.selectbox("Value", num_cols, key="wf_num")
            top_n = c3.slider("Top N", 5, 20, 10, key="wf_n")

            agg_df = (
                df.groupby(cat_col)[num_col].sum()
                .sort_values(ascending=False).head(top_n).reset_index()
            )
            agg_df.columns = [cat_col, "Value"]

            measures = ["relative"] * len(agg_df) + ["total"]
            x_vals = agg_df[cat_col].astype(str).tolist() + ["TOTAL"]
            y_vals = agg_df["Value"].tolist() + [agg_df["Value"].sum()]

            fig = go.Figure(go.Waterfall(
                orientation="v", measure=measures, x=x_vals, y=y_vals,
                text=[f"{v:.3s}" for v in y_vals], textposition="outside",
                textfont=dict(family="DM Sans", size=11),
                connector={"line": {"color": "#E5E5E5", "width": 1}},
                increasing={"marker": {"color": "#22C55E", "line": {"color": "white", "width": 1}}},
                decreasing={"marker": {"color": RED, "line": {"color": "white", "width": 1}}},
                totals={"marker": {"color": DARK, "line": {"color": "white", "width": 1}}}
            ))
            apex_layout(fig, f"Waterfall — {num_col} by {cat_col}", 520)
            st.plotly_chart(fig, use_container_width=True)

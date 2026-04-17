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
            <div class="page-title">UNIVARIATE<span> ANALYSIS</span></div>
            <div class="page-subtitle">Distribution · Outliers · Normality · Frequency</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols and not cat_cols:
        st.warning("No analysable columns detected.")
        return

    tab_num, tab_cat = st.tabs(["🔢  Numeric Columns", "🔤  Categorical Columns"])

    # ── NUMERIC ───────────────────────────────────────────────────────────────
    with tab_num:
        if not num_cols:
            st.info("No numeric columns found.")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                col_sel = st.selectbox("Select column", num_cols, key="uni_num")
            with col2:
                chart_type = st.selectbox("Chart type", [
                    "Histogram + Normal", "Boxplot", "Violin", "ECDF", "4-in-1 Overview"
                ], key="uni_chart")

            s = df[col_sel].dropna()

            # Stats strip
            kpi_cols = st.columns(6)
            stats_vals = [
                ("MEAN", f"{s.mean():.4g}"),
                ("MEDIAN", f"{s.median():.4g}"),
                ("STD DEV", f"{s.std():.4g}"),
                ("MIN", f"{s.min():.4g}"),
                ("MAX", f"{s.max():.4g}"),
                ("SKEWNESS", f"{s.skew():.3f}"),
            ]
            for col, (label, val) in zip(kpi_cols, stats_vals):
                with col:
                    color = RED if label == "SKEWNESS" and abs(s.skew()) > 1 else DARK
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">{label}</div>
                        <div class="value" style="font-size:1.4rem;color:{color}">{val}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("")

            if chart_type == "Histogram + Normal":
                n_bins = st.slider("Bins", 5, 100, 30, key="bins_uni")
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=s, nbinsx=n_bins, histnorm="probability density",
                    marker_color=RED, marker_line_color="white",
                    marker_line_width=0.5, opacity=0.8, name="Distribution"
                ))
                mu, sigma = s.mean(), s.std()
                xr = np.linspace(s.min(), s.max(), 300)
                fig.add_trace(go.Scatter(
                    x=xr, y=stats.norm.pdf(xr, mu, sigma),
                    mode="lines", line=dict(color=DARK, width=2.5, dash="dash"),
                    name="Normal fit"
                ))
                apex_layout(fig, f"Distribution — {col_sel}", 480)
                st.plotly_chart(fig, use_container_width=True)

                # QQ Plot
                qq = stats.probplot(s, dist="norm")
                fig_qq = go.Figure()
                fig_qq.add_trace(go.Scatter(
                    x=qq[0][0], y=qq[0][1], mode="markers",
                    marker=dict(color=RED, size=4, opacity=0.7), name="Data"
                ))
                ref = np.array([qq[0][0][0], qq[0][0][-1]])
                fig_qq.add_trace(go.Scatter(
                    x=ref, y=qq[1][1] + qq[1][0] * ref,
                    mode="lines", line=dict(color=DARK, dash="dash", width=2), name="Normal line"
                ))
                apex_layout(fig_qq, "QQ-Plot — Normality Check", 350)
                st.plotly_chart(fig_qq, use_container_width=True)

                # Normality tests
                if len(s) >= 8:
                    stat_sw, p_sw = stats.shapiro(s.sample(min(5000, len(s)), random_state=42))
                    c1, c2 = st.columns(2)
                    c1.metric("Shapiro-Wilk W", f"{stat_sw:.4f}", delta=f"p={p_sw:.4f}")
                    if p_sw > 0.05:
                        c2.success("✅ Cannot reject normality (p ≥ 0.05)")
                    else:
                        c2.error("❌ Non-normal distribution (p < 0.05)")

            elif chart_type == "Boxplot":
                q1, q3 = s.quantile(0.25), s.quantile(0.75)
                iqr_val = q3 - q1
                outliers = s[(s < q1 - 1.5 * iqr_val) | (s > q3 + 1.5 * iqr_val)]

                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=s, name=col_sel, boxpoints="outliers",
                    marker=dict(color=RED, size=4, opacity=0.7),
                    line=dict(color=RED, width=2),
                    fillcolor="rgba(232,0,45,0.08)",
                    whiskerwidth=0.8
                ))
                apex_layout(fig, f"Boxplot — {col_sel}", 480)
                st.plotly_chart(fig, use_container_width=True)

                if not outliers.empty:
                    st.markdown(f'<div class="insight-card">⚠️ <strong>{len(outliers)} outliers detected</strong> via IQR × 1.5 method</div>', unsafe_allow_html=True)
                    st.dataframe(outliers.reset_index().rename(columns={"index": "Row"}), height=200, use_container_width=True)
                else:
                    st.markdown('<div class="insight-card">✅ <strong>No outliers detected</strong> via IQR × 1.5 method</div>', unsafe_allow_html=True)

            elif chart_type == "Violin":
                fig = px.violin(df, y=col_sel, box=True, points="outliers",
                                color_discrete_sequence=[RED])
                apex_layout(fig, f"Violin Plot — {col_sel}", 480)
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "ECDF":
                fig = px.ecdf(df, x=col_sel, color_discrete_sequence=[RED])
                apex_layout(fig, f"Empirical CDF — {col_sel}", 480)
                st.plotly_chart(fig, use_container_width=True)

            else:  # 4-in-1
                fig = make_subplots(rows=2, cols=2,
                                    subplot_titles=["Histogram", "Boxplot", "Violin", "ECDF"])
                fig.add_trace(go.Histogram(x=s, nbinsx=30, marker_color=RED, opacity=0.8, name="Hist"), row=1, col=1)
                fig.add_trace(go.Box(y=s, marker_color=RED, name="Box", boxpoints="outliers"), row=1, col=2)
                fig.add_trace(go.Violin(y=s, fillcolor="rgba(232,0,45,0.15)", line_color=RED, box_visible=True, name="Violin"), row=2, col=1)
                s_sorted = np.sort(s)
                ecdf = np.arange(1, len(s_sorted) + 1) / len(s_sorted)
                fig.add_trace(go.Scatter(x=s_sorted, y=ecdf, mode="lines", line=dict(color=RED, width=2), name="ECDF"), row=2, col=2)
                apex_layout(fig, f"Complete Analysis — {col_sel}", 700)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("📋  Full Descriptive Statistics"):
                desc = s.describe(percentiles=[.05, .1, .25, .5, .75, .9, .95])
                desc["skewness"] = s.skew()
                desc["kurtosis"] = s.kurtosis()
                desc["variance"] = s.var()
                desc["cv_%"] = 100 * s.std() / s.mean() if s.mean() != 0 else np.nan
                st.dataframe(pd.DataFrame(desc).T.round(4), use_container_width=True)

    # ── CATEGORICAL ───────────────────────────────────────────────────────────
    with tab_cat:
        if not cat_cols:
            st.info("No categorical columns found.")
        else:
            c1, c2 = st.columns([2, 1])
            col_sel = c1.selectbox("Select column", cat_cols, key="uni_cat")
            top_n = c2.slider("Top N values", 5, 50, 15, key="top_n")

            vc = df[col_sel].value_counts().head(top_n)

            kpi_cols = st.columns(4)
            kpis = [
                ("UNIQUE VALUES", str(df[col_sel].nunique())),
                ("TOP VALUE", str(vc.index[0])[:20]),
                ("TOP FREQUENCY", f"{vc.iloc[0]:,}"),
                ("TOP %", f"{100 * vc.iloc[0] / df[col_sel].count():.1f}%"),
            ]
            for col, (label, val) in zip(kpi_cols, kpis):
                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">{label}</div>
                        <div class="value" style="font-size:1.2rem">{val}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("")

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    x=vc.index.astype(str), y=vc.values,
                    color=vc.values,
                    color_continuous_scale=[[0, "#FFB3C1"], [1, RED]],
                    text=vc.values
                )
                fig.update_traces(textposition="outside", textfont=dict(size=11))
                apex_layout(fig, f"Top {top_n} Values — {col_sel}", 450)
                fig.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = go.Figure(go.Pie(
                    values=vc.values, labels=vc.index.astype(str),
                    hole=0.5,
                    marker=dict(
                        colors=px.colors.sequential.Reds_r[:len(vc)],
                        line=dict(color="white", width=2)
                    ),
                    textfont=dict(family="DM Sans", size=11)
                ))
                apex_layout(fig2, f"Share — {col_sel}", 450)
                st.plotly_chart(fig2, use_container_width=True)

            # Treemap
            vc_all = df[col_sel].value_counts().head(50)
            fig3 = px.treemap(
                names=vc_all.index.astype(str),
                values=vc_all.values,
                parents=["" for _ in range(len(vc_all))],
                color=vc_all.values,
                color_continuous_scale=[[0, "#FFB3C1"], [1, RED]],
            )
            apex_layout(fig3, f"Treemap — {col_sel}", 400)
            fig3.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig3, use_container_width=True)

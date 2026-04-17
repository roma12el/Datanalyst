import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.loader import get_file_info
from utils.profiling import compute_profile

TEMPLATE = "plotly_white"
RED = "#E8002D"
DARK = "#171717"

COLORS = {
    "primary": RED,
    "secondary": "#171717",
    "accent": "#FF1A45",
    "neutral": ["#E8002D", "#FF4D6D", "#FF8FA3", "#FFB3C1", "#FFCCD5"],
    "seq": [[0, "#FFFFFF"], [0.5, "#FF8FA3"], [1, "#E8002D"]],
    "div": "RdBu",
}


def apex_chart_layout(fig, title="", height=450):
    fig.update_layout(
        template=TEMPLATE,
        height=height,
        title=dict(text=title, font=dict(family="DM Sans", size=14, color=DARK), x=0, xanchor="left"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans", color="#404040"),
        margin=dict(t=50, b=40, l=50, r=30),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E5E5E5",
            font_family="DM Sans",
            font_size=12,
        )
    )
    fig.update_xaxes(gridcolor="#F2F2F2", linecolor="#E5E5E5", tickfont=dict(size=11))
    fig.update_yaxes(gridcolor="#F2F2F2", linecolor="#E5E5E5", tickfont=dict(size=11))
    return fig


def show(df, filename, sheet_info):
    info = get_file_info(df)

    st.markdown(f"""
    <div class="page-header">
        <div>
            <div class="page-title">DATA<span>OVERVIEW</span></div>
            <div class="page-subtitle">Auto profiling · {filename} · {info['rows']:,} rows × {info['cols']} columns</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Strip ────────────────────────────────────────────────────────────
    cols = st.columns(6)
    kpis = [
        ("ROWS", f"{info['rows']:,}", "records"),
        ("COLUMNS", str(info['cols']), "features"),
        ("NUMERIC", str(len(info['num_cols'])), "columns"),
        ("CATEGORICAL", str(len(info['cat_cols'])), "columns"),
        ("MISSING", f"{info['missing_pct']}%", "of values"),
        ("DUPLICATES", str(info['duplicates']), "rows"),
    ]
    for col, (label, value, sub) in zip(cols, kpis):
        with col:
            color = RED if (label == "MISSING" and info['missing_pct'] > 0) or (label == "DUPLICATES" and info['duplicates'] > 0) else DARK
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value" style="color:{color}">{value}</div>
                <div class="sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋  Data Preview",
        "🔬  Column Profiles",
        "❓  Missing Values",
        "📊  Type Distribution"
    ])

    # ── TAB 1: DATA PREVIEW ──────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('<div class="section-title">Sample Data</div>', unsafe_allow_html=True)
            n = st.slider("Rows to display", 5, 100, 10)
            st.dataframe(df.head(n), use_container_width=True, height=350)

        with col2:
            st.markdown('<div class="section-title">Column Types</div>', unsafe_allow_html=True)
            dtype_df = pd.DataFrame({
                "Column": df.dtypes.index,
                "Type": df.dtypes.values.astype(str),
                "Non-null": df.count().values,
                "Null": df.isnull().sum().values,
            })
            st.dataframe(dtype_df, use_container_width=True, height=350)

        st.markdown('<div class="section-title">Descriptive Statistics</div>', unsafe_allow_html=True)
        st.dataframe(df.describe(include="all").T.round(3), use_container_width=True)

    # ── TAB 2: COLUMN PROFILES ───────────────────────────────────────────────
    with tab2:
        profile_df = compute_profile(df)
        st.markdown('<div class="section-title">Full Column Profile</div>', unsafe_allow_html=True)

        def color_missing(val):
            if isinstance(val, float) and val > 30:
                return "background-color: #FFE4E8; color: #B8001F;"
            elif isinstance(val, float) and val > 10:
                return "background-color: #FFF3CD;"
            return ""

        st.dataframe(
            profile_df.style.applymap(color_missing, subset=["missing_pct"]),
            use_container_width=True, height=500
        )
        csv = profile_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️  Download Profile CSV", csv, "apex_column_profile.csv", "text/csv")

    # ── TAB 3: MISSING VALUES ────────────────────────────────────────────────
    with tab3:
        missing = df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)

        if missing.empty:
            st.markdown("""
            <div style="background:#F0FFF4;border:1.5px solid #22C55E;border-radius:10px;
                        padding:20px;text-align:center;margin:20px 0;">
                <div style="font-size:2rem;margin-bottom:8px;">✅</div>
                <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;letter-spacing:0.08em;color:#15803D;">
                    ZERO MISSING VALUES
                </div>
                <div style="font-size:0.8rem;color:#166534;margin-top:4px;">
                    Your dataset is perfectly complete.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=missing.index,
                    y=missing.values,
                    marker_color=RED,
                    marker_line_color="white",
                    marker_line_width=1,
                    text=missing.values,
                    textposition="outside",
                    textfont=dict(size=11, family="DM Sans"),
                    name="Missing Count"
                ))
                fig.add_trace(go.Scatter(
                    x=missing.index,
                    y=[100 * v / len(df) for v in missing.values],
                    mode="lines+markers",
                    name="% Missing",
                    yaxis="y2",
                    line=dict(color=DARK, width=2),
                    marker=dict(size=6, color=DARK)
                ))
                fig.update_layout(
                    yaxis2=dict(overlaying="y", side="right", title="% Missing",
                                tickfont=dict(size=10), gridcolor="rgba(0,0,0,0)"),
                    legend=dict(x=0.7, y=1.05, orientation="h", font=dict(size=11)),
                )
                apex_chart_layout(fig, "Missing Values by Column", 400)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)
                miss_df = pd.DataFrame({
                    "Column": missing.index,
                    "Count": missing.values,
                    "%": (100 * missing / len(df)).round(1)
                })
                st.dataframe(miss_df, use_container_width=True, height=380)

            if len(df.columns) <= 50:
                st.markdown('<div class="section-title">Nullity Heatmap</div>', unsafe_allow_html=True)
                sample = df.sample(min(200, len(df)), random_state=42)
                mask = sample.isnull().astype(int)
                fig2 = go.Figure(go.Heatmap(
                    z=mask.values,
                    x=mask.columns.tolist(),
                    y=[f"Row {i}" for i in mask.index],
                    colorscale=[[0, "#F0FFF4"], [1, RED]],
                    showscale=True,
                    colorbar=dict(tickvals=[0, 1], ticktext=["Present", "Missing"],
                                  len=0.5, thickness=12)
                ))
                apex_chart_layout(fig2, "Nullity Map — 200 row sample", 500)
                st.plotly_chart(fig2, use_container_width=True)

    # ── TAB 4: TYPE DISTRIBUTION ─────────────────────────────────────────────
    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            type_counts = pd.Series({
                "Numeric": len(info["num_cols"]),
                "Categorical": len(info["cat_cols"]),
                "Date/Time": len(info["date_cols"]),
            })
            fig3 = go.Figure(go.Pie(
                values=type_counts.values,
                labels=type_counts.index,
                hole=0.62,
                marker=dict(colors=[RED, DARK, "#737373"], line=dict(color="white", width=3)),
                textfont=dict(family="DM Sans", size=12),
            ))
            fig3.add_annotation(
                text=f"<b>{len(df.columns)}</b><br>cols",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=18, family="Bebas Neue", color=DARK)
            )
            apex_chart_layout(fig3, "Column Type Distribution", 350)
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            completeness = (df.count() / len(df) * 100).sort_values()
            bar_colors = [RED if v < 70 else "#F59E0B" if v < 90 else "#22C55E" for v in completeness]
            fig4 = go.Figure(go.Bar(
                x=completeness.values, y=completeness.index,
                orientation="h",
                marker_color=bar_colors,
                text=[f"{v:.0f}%" for v in completeness.values],
                textposition="outside",
                textfont=dict(size=10, family="DM Sans"),
            ))
            apex_chart_layout(fig4, "Column Completeness (%)", max(350, len(df.columns) * 22))
            fig4.update_layout(xaxis_range=[0, 115])
            st.plotly_chart(fig4, use_container_width=True)

        if info["cat_cols"]:
            st.markdown('<div class="section-title">Categorical Cardinality</div>', unsafe_allow_html=True)
            card_df = pd.DataFrame({
                "Column": info["cat_cols"],
                "Unique Values": [df[c].nunique() for c in info["cat_cols"]]
            }).sort_values("Unique Values", ascending=False)
            fig5 = px.bar(
                card_df, x="Column", y="Unique Values",
                color="Unique Values", color_continuous_scale=[[0, "#FFB3C1"], [1, RED]],
            )
            apex_chart_layout(fig5, "Unique Values per Categorical Column", 380)
            fig5.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig5, use_container_width=True)

    # ── AUTO INSIGHTS ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Auto Insights</div>', unsafe_allow_html=True)
    insights = []
    if info["missing_pct"] > 20:
        insights.append(f"⚠️ <strong>{info['missing_pct']}% missing values</strong> — consider imputation or removal.")
    if info["duplicates"] > 0:
        insights.append(f"⚠️ <strong>{info['duplicates']} duplicate rows</strong> detected — risk of analytical bias.")
    if info["missing_pct"] == 0 and info["duplicates"] == 0:
        insights.append("✅ <strong>Clean dataset</strong> — zero missing values and zero duplicates.")
    for col in info["num_cols"]:
        skew = df[col].skew()
        if abs(skew) > 1.5:
            insights.append(f"📐 <strong>{col}</strong>: highly skewed distribution (skew={skew:.2f}) — log transform recommended.")
    if not info["num_cols"]:
        insights.append("ℹ️ No numeric columns detected — quantitative analysis unavailable.")
    if info["cat_cols"]:
        high_card = [c for c in info["cat_cols"] if df[c].nunique() > 50]
        if high_card:
            insights.append(f"🔤 High-cardinality columns (>50 values): <strong>{', '.join(high_card)}</strong> — encoding recommended.")
    if info["memory_mb"] > 100:
        insights.append(f"💾 Dataset is <strong>{info['memory_mb']:.1f} MB</strong> — some operations may be slow.")

    for ins in insights[:8]:
        st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)

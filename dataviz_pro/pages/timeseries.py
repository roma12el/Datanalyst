import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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


def try_parse_dates(df):
    date_candidates = []
    for col in df.select_dtypes(include=["datetime"]).columns:
        date_candidates.append((col, df[col]))
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if parsed.notna().sum() / len(df) > 0.5:
                date_candidates.append((col, parsed))
        except Exception:
            pass
    return date_candidates


def show(df):
    st.markdown("""
    <div class="page-header">
        <div>
            <div class="page-title">TIME<span> SERIES</span></div>
            <div class="page-subtitle">Trends · Seasonality · Candlesticks · Cumulative returns</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    date_candidates = try_parse_dates(df)
    num_cols = df.select_dtypes(include=np.number).columns.tolist()

    if not date_candidates:
        st.markdown("""
        <div style="background:#FFF5F5;border:1.5px solid #FFB3C1;border-radius:12px;
                    padding:24px;text-align:center;margin:20px 0;">
            <div style="font-size:2rem;margin-bottom:8px;">📅</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;letter-spacing:0.08em;color:#B8001F;">
                NO DATE COLUMN DETECTED
            </div>
            <div style="font-size:0.82rem;color:#737373;margin-top:6px;">
                Ensure date columns are in a recognizable format (e.g. 2024-01-15, 01/15/2024)
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    if not num_cols:
        st.warning("No numeric column for Y axis.")
        return

    c1, c2, c3, c4 = st.columns(4)
    date_col_name = c1.selectbox("Date column", [c for c, _ in date_candidates], key="ts_date")
    y_col = c2.selectbox("Y Value", num_cols, key="ts_y")
    granularity = c3.selectbox("Granularity", ["Original", "Day", "Week", "Month", "Quarter", "Year"], key="ts_gran")
    agg_func = c4.selectbox("Aggregation", ["sum", "mean", "median", "max", "min"], key="ts_agg")

    date_series = dict(date_candidates)[date_col_name]
    ts_df = pd.DataFrame({"date": date_series, "value": df[y_col]}).dropna().sort_values("date").reset_index(drop=True)

    if len(ts_df) < 3:
        st.warning("Not enough valid time series data.")
        return

    grain_map = {"Day": "D", "Week": "W", "Month": "ME", "Quarter": "QE", "Year": "YE"}
    if granularity != "Original":
        ts_df = (
            ts_df.set_index("date").resample(grain_map[granularity])["value"]
            .agg(agg_func).reset_index()
        )
        ts_df.columns = ["date", "value"]
    ts_df = ts_df.dropna()

    ma_options = st.multiselect("Moving Averages", [7, 14, 30, 90, 365],
                                 default=[7] if len(ts_df) > 7 else [])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈  Time Series",
        "📊  Seasonality",
        "🕯️  Candlestick (OHLC)",
        "📉  Growth & Returns"
    ])

    # ── SÉRIE TEMPORELLE ──────────────────────────────────────────────────────
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_df["date"], y=ts_df["value"],
            mode="lines", name=y_col,
            line=dict(color=RED, width=1.8),
            fill="tozeroy", fillcolor="rgba(232,0,45,0.06)"
        ))
        for ma in ma_options:
            if len(ts_df) > ma:
                ma_series = ts_df["value"].rolling(ma).mean()
                fig.add_trace(go.Scatter(
                    x=ts_df["date"], y=ma_series,
                    mode="lines", name=f"MA {ma}",
                    line=dict(width=1.8, dash="dot", color=DARK)
                ))

        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True, thickness=0.05, bgcolor="#F2F2F2"),
                rangeselector=dict(
                    bgcolor="#F2F2F2", activecolor=RED, borderwidth=0,
                    font=dict(family="DM Sans", size=10),
                    buttons=[
                        dict(count=7, label="7D", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="ALL")
                    ]
                )
            ),
            hovermode="x unified",
            legend=dict(orientation="h", x=0, y=1.08, font=dict(size=11))
        )
        apex_layout(fig, f"Time Series — {y_col}", 560)
        st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Period", f"{ts_df['date'].min().date()} → {ts_df['date'].max().date()}")
        c2.metric("Total", f"{ts_df['value'].sum():.4g}")
        c3.metric("Average", f"{ts_df['value'].mean():.4g}")
        trend_dir = "↑ Rising" if ts_df["value"].iloc[-1] > ts_df["value"].iloc[0] else "↓ Falling"
        c4.metric("Trend", trend_dir)

    # ── SAISONNALITÉ ──────────────────────────────────────────────────────────
    with tab2:
        ts_work = ts_df.copy()
        ts_work["month"] = pd.to_datetime(ts_work["date"]).dt.month_name()
        ts_work["weekday"] = pd.to_datetime(ts_work["date"]).dt.day_name()
        ts_work["year"] = pd.to_datetime(ts_work["date"]).dt.year

        months_order = ["January","February","March","April","May","June",
                        "July","August","September","October","November","December"]
        days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

        col1, col2 = st.columns(2)
        with col1:
            monthly = ts_work.groupby("month")["value"].mean().reindex(months_order).dropna()
            if not monthly.empty:
                fig2 = px.bar(x=monthly.index, y=monthly.values,
                              color=monthly.values,
                              color_continuous_scale=[[0, "#FFB3C1"], [1, RED]],
                              labels={"x": "Month", "y": "Avg Value"})
                fig2.update_traces(marker_line_color="white", marker_line_width=0.5)
                apex_layout(fig2, "Monthly Seasonality", 370)
                fig2.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

        with col2:
            weekly = ts_work.groupby("weekday")["value"].mean().reindex(days_order).dropna()
            if not weekly.empty:
                fig3 = px.bar(x=weekly.index, y=weekly.values,
                              color=weekly.values,
                              color_continuous_scale=[[0, "#FFB3C1"], [1, RED]],
                              labels={"x": "Day", "y": "Avg Value"})
                fig3.update_traces(marker_line_color="white", marker_line_width=0.5)
                apex_layout(fig3, "Weekly Seasonality", 370)
                fig3.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig3, use_container_width=True)

        pivot = ts_work.pivot_table(values="value", index="year", columns="month", aggfunc="sum")
        pivot = pivot.reindex(columns=[m for m in months_order if m in pivot.columns])
        if not pivot.empty:
            fig4 = px.imshow(pivot, color_continuous_scale=[[0, "#FFF5F5"], [0.5, RED], [1, "#7B0015"]],
                             aspect="auto")
            apex_layout(fig4, "Year × Month Heatmap", 420)
            st.plotly_chart(fig4, use_container_width=True)

    # ── CANDLESTICK ───────────────────────────────────────────────────────────
    with tab3:
        if len(ts_df) < 10:
            st.info("Not enough data points for candlestick chart.")
        else:
            grain = st.selectbox("OHLC Period", ["Week", "Month", "Quarter"], key="ohlc_g")
            grain_map2 = {"Week": "W", "Month": "ME", "Quarter": "QE"}
            ohlc = (
                ts_df.set_index("date")["value"]
                .resample(grain_map2[grain]).ohlc().dropna().reset_index()
            )
            if not ohlc.empty:
                fig_c = go.Figure(go.Candlestick(
                    x=ohlc["date"],
                    open=ohlc["open"], high=ohlc["high"],
                    low=ohlc["low"], close=ohlc["close"],
                    increasing=dict(line=dict(color="#22C55E", width=1.5),
                                    fillcolor="rgba(34,197,94,0.3)"),
                    decreasing=dict(line=dict(color=RED, width=1.5),
                                    fillcolor="rgba(232,0,45,0.3)")
                ))
                apex_layout(fig_c, f"OHLC Candlestick ({grain}) — {y_col}", 520)
                fig_c.update_layout(xaxis_rangeslider_visible=True,
                                    xaxis_rangeslider=dict(thickness=0.05, bgcolor="#F2F2F2"))
                st.plotly_chart(fig_c, use_container_width=True)

    # ── GROWTH & RETURNS ──────────────────────────────────────────────────────
    with tab4:
        ts_work2 = ts_df.copy()
        ts_work2["variation_pct"] = ts_work2["value"].pct_change() * 100
        ts_work2["cumulative_return"] = (1 + ts_work2["value"].pct_change()).cumprod() - 1

        fig5 = make_subplots(rows=2, cols=1,
                             subplot_titles=["Period-over-Period Change (%)", "Cumulative Return (%)"],
                             shared_xaxes=True, vertical_spacing=0.1)

        colors = [RED if v < 0 else "#22C55E" for v in ts_work2["variation_pct"].fillna(0)]
        fig5.add_trace(go.Bar(
            x=ts_work2["date"], y=ts_work2["variation_pct"],
            marker_color=colors, marker_line_width=0, name="Change %"
        ), row=1, col=1)

        fig5.add_trace(go.Scatter(
            x=ts_work2["date"], y=ts_work2["cumulative_return"] * 100,
            mode="lines", line=dict(color=RED, width=2), name="Cumulative %",
            fill="tozeroy", fillcolor="rgba(232,0,45,0.07)"
        ), row=2, col=1)

        apex_layout(fig5, "Growth & Returns Analysis", 620)
        fig5.update_layout(showlegend=False)
        fig5.update_yaxes(gridcolor="#F2F2F2", linecolor="#E5E5E5")
        st.plotly_chart(fig5, use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def try_parse_dates(df):
    """Return list of (col_name, parsed_series) for date-like columns."""
    date_candidates = []
    for col in df.select_dtypes(include=["datetime"]).columns:
        date_candidates.append((col, df[col]))
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            ratio = parsed.notna().sum() / len(df)
            if ratio > 0.5:
                date_candidates.append((col, parsed))
        except Exception:
            pass
    return date_candidates


def show(df):
    st.markdown('<p class="section-title">📅 Analyse temporelle</p>', unsafe_allow_html=True)

    date_candidates = try_parse_dates(df)
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    TEMPLATE = "plotly_white"

    if not date_candidates:
        st.warning("Aucune colonne de date détectée dans ce dataset.")
        st.info("**Astuce :** Assurez-vous que vos colonnes de dates sont au format reconnaissable (ex: 2024-01-15, 01/15/2024).")
        return

    if not num_cols:
        st.warning("Aucune colonne numérique pour l'axe Y.")
        return

    date_col_names = [c for c, _ in date_candidates]
    col1, col2 = st.columns(2)
    date_col_name = col1.selectbox("Colonne de date", date_col_names, key="ts_date")
    y_col = col2.selectbox("Valeur (axe Y)", num_cols, key="ts_y")

    # Parse date
    date_series = dict(date_candidates)[date_col_name]

    # Build working df
    ts_df = pd.DataFrame({
        "date": date_series,
        "value": df[y_col]
    }).dropna().sort_values("date").reset_index(drop=True)

    if len(ts_df) < 3:
        st.warning("Pas assez de données temporelles valides.")
        return

    # Granularity
    date_range = (ts_df["date"].max() - ts_df["date"].min()).days
    granularity_options = ["Original", "Jour", "Semaine", "Mois", "Trimestre", "Année"]
    granularity = st.selectbox("Granularité d'agrégation", granularity_options, key="ts_gran")
    agg_func = st.selectbox("Agrégation", ["sum", "mean", "median", "max", "min"], key="ts_agg")

    grain_map = {
        "Jour": "D", "Semaine": "W", "Mois": "ME",
        "Trimestre": "QE", "Année": "YE"
    }
    if granularity != "Original":
        ts_df = (
            ts_df.set_index("date")
            .resample(grain_map[granularity])["value"]
            .agg(agg_func)
            .reset_index()
        )
        ts_df.columns = ["date", "value"]

    ts_df = ts_df.dropna()

    # Moving averages
    ma_options = st.multiselect(
        "Moyennes mobiles", [7, 14, 30, 90, 365],
        default=[7] if len(ts_df) > 7 else []
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Série temporelle", "📊 Saisonnalité",
        "🕯️ Candlestick (OHLC)", "📉 Croissance & Variation"
    ])

    # ── SÉRIE TEMPORELLE ─────────────────────────────────────────────────
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_df["date"], y=ts_df["value"],
            mode="lines", name=y_col,
            line=dict(color="#667eea", width=1.5),
            fill="tozeroy", fillcolor="rgba(102,126,234,0.07)"
        ))

        for ma in ma_options:
            if len(ts_df) > ma:
                ma_series = ts_df["value"].rolling(ma).mean()
                fig.add_trace(go.Scatter(
                    x=ts_df["date"], y=ma_series,
                    mode="lines", name=f"MA {ma}",
                    line=dict(width=1.5, dash="dot")
                ))

        fig.update_layout(
            title=f"Évolution temporelle — {y_col}",
            xaxis=dict(
                rangeslider=dict(visible=True),
                rangeselector=dict(buttons=[
                    dict(count=7, label="7J", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(step="all", label="Tout")
                ])
            ),
            height=550, template=TEMPLATE,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Période", f"{ts_df['date'].min().date()} → {ts_df['date'].max().date()}")
        c2.metric("Total", f"{ts_df['value'].sum():.4g}")
        c3.metric("Moyenne", f"{ts_df['value'].mean():.4g}")
        c4.metric("Tendance",
                  "↑ Hausse" if ts_df["value"].iloc[-1] > ts_df["value"].iloc[0] else "↓ Baisse")

    # ── SAISONNALITÉ ─────────────────────────────────────────────────────
    with tab2:
        ts_work = ts_df.copy()
        ts_work["month"] = pd.to_datetime(ts_work["date"]).dt.month_name()
        ts_work["weekday"] = pd.to_datetime(ts_work["date"]).dt.day_name()
        ts_work["year"] = pd.to_datetime(ts_work["date"]).dt.year
        ts_work["quarter"] = pd.to_datetime(ts_work["date"]).dt.quarter

        months_order = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"]
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        col1, col2 = st.columns(2)
        with col1:
            monthly = ts_work.groupby("month")["value"].mean().reindex(months_order).dropna()
            if not monthly.empty:
                fig2 = px.bar(
                    x=monthly.index, y=monthly.values,
                    title="Saisonnalité mensuelle (moyenne)",
                    color=monthly.values, color_continuous_scale="Blues",
                    labels={"x": "Mois", "y": "Valeur moyenne"}
                )
                fig2.update_layout(height=350, template=TEMPLATE, coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

        with col2:
            weekly = ts_work.groupby("weekday")["value"].mean().reindex(days_order).dropna()
            if not weekly.empty:
                fig3 = px.bar(
                    x=weekly.index, y=weekly.values,
                    title="Saisonnalité hebdomadaire (moyenne)",
                    color=weekly.values, color_continuous_scale="Purples",
                    labels={"x": "Jour", "y": "Valeur moyenne"}
                )
                fig3.update_layout(height=350, template=TEMPLATE, coloraxis_showscale=False)
                st.plotly_chart(fig3, use_container_width=True)

        # Heatmap année × mois
        pivot = ts_work.pivot_table(values="value", index="year", columns="month", aggfunc="sum")
        pivot = pivot.reindex(columns=[m for m in months_order if m in pivot.columns])
        if not pivot.empty:
            fig4 = px.imshow(
                pivot, title="Heatmap année × mois",
                color_continuous_scale="RdYlGn",
                aspect="auto"
            )
            fig4.update_layout(height=400, template=TEMPLATE)
            st.plotly_chart(fig4, use_container_width=True)

    # ── CANDLESTICK ──────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### OHLC Candlestick")
        if len(ts_df) < 10:
            st.info("Pas assez de points pour un candlestick.")
        else:
            grain = st.selectbox("Période OHLC", ["Semaine", "Mois", "Trimestre"], key="ohlc_g")
            grain_map2 = {"Semaine": "W", "Mois": "ME", "Trimestre": "QE"}
            ohlc = (
                ts_df.set_index("date")["value"]
                .resample(grain_map2[grain])
                .ohlc()
                .dropna()
                .reset_index()
            )
            if not ohlc.empty:
                fig_c = go.Figure(go.Candlestick(
                    x=ohlc["date"],
                    open=ohlc["open"], high=ohlc["high"],
                    low=ohlc["low"], close=ohlc["close"],
                    increasing_line_color="#27ae60",
                    decreasing_line_color="#c0392b"
                ))
                fig_c.update_layout(
                    title=f"Candlestick {grain} — {y_col}",
                    height=500, template=TEMPLATE,
                    xaxis_rangeslider_visible=True
                )
                st.plotly_chart(fig_c, use_container_width=True)

    # ── CROISSANCE & VARIATION ───────────────────────────────────────────
    with tab4:
        ts_work2 = ts_df.copy()
        ts_work2["variation_pct"] = ts_work2["value"].pct_change() * 100
        ts_work2["cumulative_return"] = (1 + ts_work2["value"].pct_change()).cumprod() - 1

        fig5 = make_subplots(rows=2, cols=1,
                              subplot_titles=["Variation % période sur période", "Rendement cumulé"],
                              shared_xaxes=True)

        colors = ["#27ae60" if v >= 0 else "#c0392b" for v in ts_work2["variation_pct"].fillna(0)]
        fig5.add_trace(go.Bar(
            x=ts_work2["date"], y=ts_work2["variation_pct"],
            marker_color=colors, name="Variation %"
        ), row=1, col=1)

        fig5.add_trace(go.Scatter(
            x=ts_work2["date"], y=ts_work2["cumulative_return"] * 100,
            mode="lines", line=dict(color="#667eea"),
            name="Rendement cumulé %", fill="tozeroy",
            fillcolor="rgba(102,126,234,0.1)"
        ), row=2, col=1)

        fig5.update_layout(height=600, template=TEMPLATE, showlegend=False)
        fig5.update_yaxes(title_text="Var %", row=1, col=1)
        fig5.update_yaxes(title_text="Cumulé %", row=2, col=1)
        st.plotly_chart(fig5, use_container_width=True)
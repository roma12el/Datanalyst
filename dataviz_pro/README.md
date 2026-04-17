# APEX Analytics Platform 🔴

**World-class data analysis platform — White & Red design**

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure

```
apex_analytics/
├── app.py                  # Main entry point
├── requirements.txt
├── pages/
│   ├── profiling.py        # Overview & auto profiling
│   ├── univariate.py       # Distributions, outliers, normality
│   ├── bivariate.py        # Correlations, scatter, ANOVA
│   ├── kpi.py              # KPI dashboard (gauges, treemaps, funnels)
│   ├── timeseries.py       # Time series, candlesticks, seasonality
│   └── export.py           # Reports, data download, cleaning
└── utils/
    ├── loader.py
    ├── profiling.py
    ├── export.py
    └── charts.py
```

## Features

- 🎨 **White & Red design** — Bebas Neue + DM Sans typography
- 📊 **50+ chart types** — All powered by Plotly
- 🔬 **Auto profiling** — Stats, missing values, outliers, insights
- 🎯 **KPI dashboards** — Gauges, waterfalls, funnels, sunbursts
- 📅 **Time series** — OHLC candlesticks, seasonality heatmaps, MA
- 📤 **One-click export** — Markdown reports, Excel, CSV
- 🧹 **Data cleaning** — Deduplication, imputation, normalization

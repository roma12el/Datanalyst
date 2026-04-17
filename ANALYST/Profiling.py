import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.loader import get_file_info
from utils.profiling import compute_profile, compute_missing_heatmap_data


def show(df, filename, sheet_info):
    st.markdown('<p class="section-title">🏠 Profiling automatique du dataset</p>', unsafe_allow_html=True)

    info = get_file_info(df)

    # ── KPI Cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📋 Lignes", f"{info['rows']:,}")
    c2.metric("📊 Colonnes", info['cols'])
    c3.metric("🔢 Num.", len(info['num_cols']))
    c4.metric("🔤 Catég.", len(info['cat_cols']))
    c5.metric("❓ Manquants", f"{info['missing_pct']}%")
    c6.metric("🔁 Doublons", info['duplicates'])

    st.markdown("---")

    # ── Overview tabs ───────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Aperçu données", "🔍 Profil colonnes",
        "❓ Valeurs manquantes", "📊 Types & Distribution"
    ])

    with tab1:
        st.markdown("#### Premiers enregistrements")
        n = st.slider("Nombre de lignes", 5, 100, 10)
        st.dataframe(df.head(n), use_container_width=True, height=350)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Types de colonnes")
            dtype_df = pd.DataFrame({
                "Colonne": df.dtypes.index,
                "Type Python": df.dtypes.values.astype(str),
                "Non-nuls": df.count().values,
                "Nuls": df.isnull().sum().values
            })
            st.dataframe(dtype_df, use_container_width=True, height=300)
        with col2:
            st.markdown("#### Statistiques rapides")
            st.dataframe(df.describe(include="all").T.round(3), use_container_width=True, height=300)

    with tab2:
        profile_df = compute_profile(df)
        st.markdown("#### Profil complet de chaque colonne")

        # Color-code by missing_pct
        def color_missing(val):
            if isinstance(val, float) and val > 30:
                return "background-color: #ffcccc"
            elif isinstance(val, float) and val > 10:
                return "background-color: #fff0cc"
            return ""

        st.dataframe(
            profile_df.style.applymap(color_missing, subset=["missing_pct"]),
            use_container_width=True, height=500
        )

        # Download profile
        csv = profile_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Télécharger le profil CSV", csv, "profil_colonnes.csv", "text/csv")

    with tab3:
        missing = df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)

        if missing.empty:
            st.success("✅ Aucune valeur manquante dans ce dataset !")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=missing.index, y=missing.values,
                    marker_color=px.colors.sequential.Reds_r[:len(missing)],
                    text=missing.values, textposition="outside",
                    name="Valeurs manquantes"
                ))
                fig.add_trace(go.Scatter(
                    x=missing.index,
                    y=[100 * v / len(df) for v in missing.values],
                    mode="lines+markers", name="% Manquant",
                    yaxis="y2", line=dict(color="#764ba2", width=2)
                ))
                fig.update_layout(
                    title="Valeurs manquantes par colonne",
                    yaxis2=dict(overlaying="y", side="right", title="% Manquant"),
                    height=400, template="plotly_white",
                    legend=dict(x=0.7, y=1.1, orientation="h")
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                missing_df = pd.DataFrame({
                    "Colonne": missing.index,
                    "Manquants": missing.values,
                    "% Total": (100 * missing / len(df)).round(1)
                })
                st.dataframe(missing_df, use_container_width=True, height=400)

            # Heatmap de nullité (limité à 50 cols × 200 lignes pour perf)
            if len(df.columns) <= 50:
                st.markdown("#### Carte de nullité")
                sample = df.sample(min(200, len(df)), random_state=42)
                mask = sample.isnull().astype(int)
                fig2 = go.Figure(go.Heatmap(
                    z=mask.values,
                    x=mask.columns.tolist(),
                    y=[f"Ligne {i}" for i in mask.index],
                    colorscale=[[0, "#d9f0a3"], [1, "#c0392b"]],
                    showscale=True,
                    colorbar=dict(tickvals=[0, 1], ticktext=["Présent", "Manquant"])
                ))
                fig2.update_layout(
                    title="Heatmap de nullité (échantillon 200 lignes)",
                    height=500, template="plotly_white"
                )
                st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        col1, col2 = st.columns(2)

        # Donut des types
        type_counts = pd.Series({
            "Numérique": len(info["num_cols"]),
            "Catégorielle": len(info["cat_cols"]),
            "Date/Heure": len(info["date_cols"]),
        })
        with col1:
            fig3 = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Répartition des types de colonnes",
                hole=0.5,
                color_discrete_sequence=["#667eea", "#f093fb", "#4facfe"]
            )
            fig3.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)

        # Completeness par colonne
        with col2:
            completeness = (df.count() / len(df) * 100).sort_values()
            colors = ["#c0392b" if v < 70 else "#e67e22" if v < 90 else "#27ae60" for v in completeness]
            fig4 = go.Figure(go.Bar(
                x=completeness.values, y=completeness.index,
                orientation="h",
                marker_color=colors,
                text=[f"{v:.1f}%" for v in completeness.values],
                textposition="outside"
            ))
            fig4.update_layout(
                title="Complétude par colonne (%)",
                xaxis_range=[0, 110], height=max(350, len(df.columns) * 22),
                template="plotly_white"
            )
            st.plotly_chart(fig4, use_container_width=True)

        # Cardinalité des colonnes catégorielles
        if info["cat_cols"]:
            st.markdown("#### Cardinalité des colonnes catégorielles")
            card_df = pd.DataFrame({
                "Colonne": info["cat_cols"],
                "Valeurs uniques": [df[c].nunique() for c in info["cat_cols"]]
            }).sort_values("Valeurs uniques", ascending=False)

            fig5 = px.bar(
                card_df, x="Colonne", y="Valeurs uniques",
                title="Nombre de valeurs uniques (catégorielles)",
                color="Valeurs uniques",
                color_continuous_scale="Viridis"
            )
            fig5.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig5, use_container_width=True)

    # ── Insights automatiques ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🤖 Insights automatiques")
    insights = []
    if info["missing_pct"] > 20:
        insights.append(f"⚠️ **{info['missing_pct']}% de valeurs manquantes** — envisagez une imputation ou suppression.")
    if info["duplicates"] > 0:
        insights.append(f"⚠️ **{info['duplicates']} doublons** détectés — risque de biais dans l'analyse.")
    if info["missing_pct"] == 0 and info["duplicates"] == 0:
        insights.append("✅ Dataset propre : aucune valeur manquante, aucun doublon.")
    for col in info["num_cols"]:
        skew = df[col].skew()
        if abs(skew) > 1.5:
            insights.append(f"📐 **{col}** : distribution très asymétrique (skew={skew:.2f}) — une transformation log peut être utile.")
    if len(info["num_cols"]) == 0:
        insights.append("ℹ️ Aucune colonne numérique détectée — analyse quantitative limitée.")
    if len(info["cat_cols"]) > 0:
        high_card = [c for c in info["cat_cols"] if df[c].nunique() > 50]
        if high_card:
            insights.append(f"🔤 Colonnes à haute cardinalité (>50 valeurs) : **{', '.join(high_card)}** — encodage recommandé.")

    for ins in insights[:8]:
        st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)
        st.markdown("")
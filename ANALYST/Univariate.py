import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


def show(df):
    st.markdown('<p class="section-title">📈 Analyse univariée</p>', unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols and not cat_cols:
        st.warning("Aucune colonne analysable détectée.")
        return

    tab_num, tab_cat = st.tabs(["🔢 Colonnes numériques", "🔤 Colonnes catégorielles"])

    # ── NUMÉRIQUES ────────────────────────────────────────────────────────
    with tab_num:
        if not num_cols:
            st.info("Aucune colonne numérique.")
        else:
            col_sel = st.selectbox("Sélectionner une colonne", num_cols, key="uni_num")
            s = df[col_sel].dropna()

            # Stats summary
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Moyenne", f"{s.mean():.3g}")
            c2.metric("Médiane", f"{s.median():.3g}")
            c3.metric("Écart-type", f"{s.std():.3g}")
            c4.metric("Min", f"{s.min():.3g}")
            c5.metric("Max", f"{s.max():.3g}")
            c6.metric("Skewness", f"{s.skew():.3f}")

            st.markdown("---")
            chart_type = st.radio(
                "Type de graphique",
                ["Histogramme + courbe normale", "Boxplot", "Violin", "ECDF", "Toutes vues (4-en-1)"],
                horizontal=True, key="uni_chart"
            )

            TEMPLATE = "plotly_white"

            if chart_type == "Histogramme + courbe normale":
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=s, nbinsx=st.slider("Nombre de bins", 5, 100, 30, key="bins"),
                    name="Distribution", marker_color="#667eea", opacity=0.75,
                    histnorm="probability density"
                ))
                # Fitted normal
                mu, sigma = s.mean(), s.std()
                x_range = np.linspace(s.min(), s.max(), 300)
                y_normal = stats.norm.pdf(x_range, mu, sigma)
                fig.add_trace(go.Scatter(
                    x=x_range, y=y_normal, mode="lines",
                    line=dict(color="#e74c3c", width=2.5),
                    name="Courbe normale ajustée"
                ))
                fig.update_layout(
                    title=f"Distribution de {col_sel}",
                    xaxis_title=col_sel, yaxis_title="Densité",
                    height=450, template=TEMPLATE,
                    bargap=0.05
                )
                st.plotly_chart(fig, use_container_width=True)

                # QQ-Plot
                st.markdown("#### QQ-Plot (normalité)")
                qq = stats.probplot(s, dist="norm")
                fig_qq = go.Figure()
                fig_qq.add_trace(go.Scatter(
                    x=qq[0][0], y=qq[0][1], mode="markers",
                    marker=dict(color="#667eea", size=4), name="Données"
                ))
                ref_line_x = np.array([qq[0][0][0], qq[0][0][-1]])
                ref_line_y = qq[1][1] + qq[1][0] * ref_line_x
                fig_qq.add_trace(go.Scatter(
                    x=ref_line_x, y=ref_line_y, mode="lines",
                    line=dict(color="#e74c3c", dash="dash"), name="Droite normale"
                ))
                fig_qq.update_layout(
                    title="QQ-Plot", xaxis_title="Quantiles théoriques",
                    yaxis_title="Quantiles observés", height=350, template=TEMPLATE
                )
                st.plotly_chart(fig_qq, use_container_width=True)

            elif chart_type == "Boxplot":
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=s, name=col_sel,
                    boxpoints="outliers",
                    marker_color="#667eea",
                    line_color="#764ba2",
                    fillcolor="rgba(102,126,234,0.2)"
                ))
                fig.update_layout(
                    title=f"Boxplot — {col_sel}",
                    height=450, template=TEMPLATE
                )
                # Outliers table
                q1, q3 = s.quantile(0.25), s.quantile(0.75)
                iqr = q3 - q1
                outliers = s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)]
                st.plotly_chart(fig, use_container_width=True)
                if not outliers.empty:
                    st.markdown(f"**{len(outliers)} outliers détectés** (méthode IQR ×1.5)")
                    st.dataframe(outliers.reset_index().rename(columns={"index": "Ligne"}), height=200)
                else:
                    st.success("Aucun outlier détecté (IQR ×1.5)")

            elif chart_type == "Violin":
                fig = px.violin(
                    df, y=col_sel, box=True, points="outliers",
                    title=f"Violin plot — {col_sel}",
                    color_discrete_sequence=["#667eea"]
                )
                fig.update_layout(height=450, template=TEMPLATE)
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "ECDF":
                fig = px.ecdf(
                    df, x=col_sel,
                    title=f"Fonction de répartition empirique (ECDF) — {col_sel}",
                    color_discrete_sequence=["#667eea"]
                )
                fig.update_layout(height=450, template=TEMPLATE)
                st.plotly_chart(fig, use_container_width=True)

            else:  # 4-en-1
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=["Histogramme", "Boxplot", "Violin", "ECDF"]
                )
                # Histogramme
                fig.add_trace(go.Histogram(
                    x=s, nbinsx=30, name="Hist",
                    marker_color="#667eea", opacity=0.75
                ), row=1, col=1)
                # Boxplot
                fig.add_trace(go.Box(
                    y=s, name="Box", boxpoints="outliers",
                    marker_color="#764ba2"
                ), row=1, col=2)
                # Violin
                fig.add_trace(go.Violin(
                    y=s, name="Violin", fillcolor="rgba(102,126,234,0.3)",
                    line_color="#667eea", box_visible=True
                ), row=2, col=1)
                # ECDF
                s_sorted = np.sort(s)
                ecdf = np.arange(1, len(s_sorted) + 1) / len(s_sorted)
                fig.add_trace(go.Scatter(
                    x=s_sorted, y=ecdf, mode="lines", name="ECDF",
                    line=dict(color="#e74c3c")
                ), row=2, col=2)
                fig.update_layout(
                    height=700, template=TEMPLATE,
                    title=f"Analyse complète — {col_sel}",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

            # Statistiques descriptives détaillées
            with st.expander("📋 Statistiques descriptives complètes"):
                desc = s.describe(percentiles=[.05, .1, .25, .5, .75, .9, .95])
                desc["skewness"] = s.skew()
                desc["kurtosis"] = s.kurtosis()
                desc["variance"] = s.var()
                desc["cv_%"] = 100 * s.std() / s.mean() if s.mean() != 0 else np.nan
                st.dataframe(pd.DataFrame(desc).T.round(4))

    # ── CATÉGORIELLES ─────────────────────────────────────────────────────
    with tab_cat:
        if not cat_cols:
            st.info("Aucune colonne catégorielle.")
        else:
            col_sel = st.selectbox("Sélectionner une colonne", cat_cols, key="uni_cat")
            top_n = st.slider("Top N valeurs", 5, 50, 15, key="top_n")

            vc = df[col_sel].value_counts().head(top_n)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Valeurs uniques", df[col_sel].nunique())
            c2.metric("Valeur la + fréquente", str(vc.index[0]))
            c3.metric("Fréquence max", f"{vc.iloc[0]:,}")
            c4.metric("% de la valeur top", f"{100 * vc.iloc[0] / df[col_sel].count():.1f}%")

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    x=vc.index.astype(str), y=vc.values,
                    labels={"x": col_sel, "y": "Fréquence"},
                    title=f"Top {top_n} — {col_sel}",
                    color=vc.values,
                    color_continuous_scale="Viridis",
                    text=vc.values
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(height=450, template="plotly_white", coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = px.pie(
                    values=vc.values, names=vc.index.astype(str),
                    title=f"Parts relatives — {col_sel}",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig2.update_layout(height=450, template="plotly_white")
                st.plotly_chart(fig2, use_container_width=True)

            # Treemap
            st.markdown("#### Treemap des fréquences")
            vc_all = df[col_sel].value_counts()
            fig3 = px.treemap(
                names=vc_all.index.astype(str)[:50],
                values=vc_all.values[:50],
                parents=["" for _ in range(min(50, len(vc_all)))],
                title=f"Treemap — {col_sel}"
            )
            fig3.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)

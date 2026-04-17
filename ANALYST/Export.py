import streamlit as st
import pandas as pd
import numpy as np
import io
from utils.profiling import compute_profile
from utils.export import df_to_excel_bytes, df_to_csv_bytes


def show(df, filename):
    st.markdown('<p class="section-title">📤 Export & Rapport</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📊 Rapport exécutif",
        "⬇️ Export données",
        "🔧 Nettoyage & Transform."
    ])

    # ── RAPPORT EXÉCUTIF ─────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 📋 Résumé exécutif automatique")

        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        missing_pct = round(100 * df.isnull().sum().sum() / (df.shape[0] * df.shape[1]), 2)
        duplicates = int(df.duplicated().sum())

        report_lines = [
            f"# 📊 Rapport d'analyse — {filename}",
            "",
            "## 1. Vue d'ensemble",
            f"- **Fichier :** {filename}",
            f"- **Dimensions :** {df.shape[0]:,} lignes × {df.shape[1]} colonnes",
            f"- **Colonnes numériques :** {len(num_cols)} ({', '.join(num_cols[:5])}{'...' if len(num_cols) > 5 else ''})",
            f"- **Colonnes catégorielles :** {len(cat_cols)} ({', '.join(cat_cols[:5])}{'...' if len(cat_cols) > 5 else ''})",
            f"- **Valeurs manquantes :** {missing_pct}%",
            f"- **Doublons :** {duplicates}",
            f"- **Mémoire :** {df.memory_usage(deep=True).sum() / 1e6:.2f} MB",
            "",
            "## 2. Qualité des données",
        ]

        if missing_pct == 0 and duplicates == 0:
            report_lines.append("✅ Dataset propre : aucune valeur manquante, aucun doublon.")
        if missing_pct > 0:
            missing_by_col = df.isnull().sum()
            worst = missing_by_col[missing_by_col > 0].sort_values(ascending=False).head(5)
            report_lines.append(f"⚠️ {missing_pct}% de valeurs manquantes.")
            for col, cnt in worst.items():
                report_lines.append(f"   - `{col}` : {cnt} manquants ({100*cnt/len(df):.1f}%)")
        if duplicates > 0:
            report_lines.append(f"⚠️ {duplicates} lignes dupliquées détectées.")

        if num_cols:
            report_lines += ["", "## 3. Statistiques numériques"]
            desc = df[num_cols].describe().round(3)
            report_lines.append(desc.to_string())

        if cat_cols:
            report_lines += ["", "## 4. Colonnes catégorielles"]
            for col in cat_cols[:5]:
                top = df[col].value_counts().head(3)
                report_lines.append(f"**{col}** — {df[col].nunique()} valeurs uniques | Top: {', '.join([f'{k}({v})' for k,v in top.items()])}")

        # Insights
        report_lines += ["", "## 5. Insights automatiques"]
        for col in num_cols[:5]:
            skew = df[col].skew()
            if abs(skew) > 1.5:
                report_lines.append(f"- `{col}` : distribution asymétrique (skewness={skew:.2f})")
        if num_cols and len(num_cols) >= 2:
            corr = df[num_cols].corr()
            pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
            high = pairs[pairs.abs() > 0.7]
            if not high.empty:
                report_lines.append(f"- Corrélations fortes (|r|>0.7) : {len(high)} paires")
                for (a, b), r in list(high.items())[:3]:
                    report_lines.append(f"   - `{a}` × `{b}` : r={r:.3f}")

        report_text = "\n".join(report_lines)
        st.markdown(report_text)

        # Download report
        report_bytes = report_text.encode("utf-8")
        st.download_button(
            "⬇️ Télécharger rapport (.md)",
            report_bytes,
            f"rapport_{filename.split('.')[0]}.md",
            "text/markdown"
        )

    # ── EXPORT DONNÉES ───────────────────────────────────────────────────
    with tab2:
        st.markdown("#### ⬇️ Télécharger les données")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Excel (.xlsx)**")
            excel_bytes = df_to_excel_bytes(df)
            st.download_button(
                "⬇️ Télécharger Excel",
                excel_bytes,
                f"data_{filename.split('.')[0]}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col2:
            st.markdown("**CSV**")
            csv_bytes = df_to_csv_bytes(df)
            st.download_button(
                "⬇️ Télécharger CSV",
                csv_bytes,
                f"data_{filename.split('.')[0]}.csv",
                "text/csv"
            )

        with col3:
            st.markdown("**Profil colonnes (.csv)**")
            profile = compute_profile(df)
            profile_csv = profile.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Télécharger profil",
                profile_csv,
                f"profil_{filename.split('.')[0]}.csv",
                "text/csv"
            )

        st.markdown("---")
        st.markdown("#### 🔍 Sélection de colonnes pour l'export")
        selected_cols = st.multiselect(
            "Colonnes à exporter", df.columns.tolist(), default=df.columns.tolist()
        )
        if selected_cols:
            filtered_df = df[selected_cols]
            st.markdown(f"**Aperçu** : {len(filtered_df):,} lignes × {len(selected_cols)} colonnes")
            st.dataframe(filtered_df.head(20), use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "⬇️ Excel (sélection)",
                    df_to_excel_bytes(filtered_df),
                    "selection_export.xlsx"
                )
            with col2:
                st.download_button(
                    "⬇️ CSV (sélection)",
                    df_to_csv_bytes(filtered_df),
                    "selection_export.csv"
                )

    # ── NETTOYAGE ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 🔧 Transformations et nettoyage")
        clean_df = df.copy()

        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox("Supprimer les doublons"):
                before = len(clean_df)
                clean_df = clean_df.drop_duplicates()
                st.success(f"✅ {before - len(clean_df)} doublons supprimés")

        with col2:
            missing_strategy = st.selectbox(
                "Stratégie valeurs manquantes (numériques)",
                ["Ne rien faire", "Supprimer lignes", "Remplacer par la moyenne", "Remplacer par la médiane", "Remplacer par 0"]
            )
            if missing_strategy != "Ne rien faire":
                num_cols = clean_df.select_dtypes(include=np.number).columns
                if missing_strategy == "Supprimer lignes":
                    clean_df = clean_df.dropna()
                elif missing_strategy == "Remplacer par la moyenne":
                    clean_df[num_cols] = clean_df[num_cols].fillna(clean_df[num_cols].mean())
                elif missing_strategy == "Remplacer par la médiane":
                    clean_df[num_cols] = clean_df[num_cols].fillna(clean_df[num_cols].median())
                elif missing_strategy == "Remplacer par 0":
                    clean_df[num_cols] = clean_df[num_cols].fillna(0)
                st.success(f"✅ Traitement appliqué")

        # Normalisation
        st.markdown("#### Normalisation")
        norm_cols = st.multiselect(
            "Colonnes à normaliser",
            clean_df.select_dtypes(include=np.number).columns.tolist()
        )
        norm_method = st.selectbox(
            "Méthode", ["Min-Max [0,1]", "Z-score (standardisation)", "Log1p"]
        )
        if norm_cols and st.button("Appliquer normalisation"):
            for col in norm_cols:
                if norm_method == "Min-Max [0,1]":
                    mn, mx = clean_df[col].min(), clean_df[col].max()
                    clean_df[f"{col}_normalized"] = (clean_df[col] - mn) / (mx - mn) if mx > mn else 0
                elif norm_method == "Z-score (standardisation)":
                    clean_df[f"{col}_zscore"] = (clean_df[col] - clean_df[col].mean()) / clean_df[col].std()
                elif norm_method == "Log1p":
                    clean_df[f"{col}_log1p"] = np.log1p(clean_df[col].clip(lower=0))
            st.success(f"✅ Normalisation appliquée sur {len(norm_cols)} colonne(s)")
            st.dataframe(clean_df.head(10), use_container_width=True)

        st.markdown("---")
        st.markdown(f"**Résultat :** {len(clean_df):,} lignes × {len(clean_df.columns)} colonnes")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Télécharger données nettoyées (Excel)",
                df_to_excel_bytes(clean_df),
                "data_cleaned.xlsx"
            )
        with col2:
            st.download_button(
                "⬇️ Télécharger données nettoyées (CSV)",
                df_to_csv_bytes(clean_df),
                "data_cleaned.csv"
            )
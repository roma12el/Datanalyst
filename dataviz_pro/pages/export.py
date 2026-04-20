import streamlit as st
import pandas as pd
import numpy as np
import io


def to_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()


def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def show(df, filename):
    st.markdown('<div class="page-title">Export <span>& Nettoyage</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Téléchargez vos données nettoyées et votre rapport synthétique.</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔧  Nettoyage rapide", "⬇️  Télécharger"])

    with tab1:
        st.markdown('<div class="section-header">Actions de nettoyage</div>', unsafe_allow_html=True)
        clean_df = df.copy()
        applied = []

        c1, c2 = st.columns(2)
        with c1:
            if st.checkbox("Supprimer les doublons"):
                before = len(clean_df)
                clean_df = clean_df.drop_duplicates()
                removed = before - len(clean_df)
                applied.append(f"✅ {removed} doublon(s) supprimé(s)")

        with c2:
            strat = st.selectbox("Valeurs manquantes (numériques)", [
                "Conserver", "Supprimer les lignes incomplètes",
                "Remplacer par la médiane", "Remplacer par la moyenne", "Remplacer par 0"
            ])
            if strat != "Conserver":
                num_c = clean_df.select_dtypes(include=np.number).columns
                if strat == "Supprimer les lignes incomplètes":
                    before = len(clean_df)
                    clean_df = clean_df.dropna()
                    applied.append(f"✅ {before - len(clean_df)} ligne(s) supprimée(s)")
                elif strat == "Remplacer par la médiane":
                    clean_df[num_c] = clean_df[num_c].fillna(clean_df[num_c].median())
                    applied.append("✅ Valeurs manquantes remplacées par la médiane")
                elif strat == "Remplacer par la moyenne":
                    clean_df[num_c] = clean_df[num_c].fillna(clean_df[num_c].mean())
                    applied.append("✅ Valeurs manquantes remplacées par la moyenne")
                elif strat == "Remplacer par 0":
                    clean_df[num_c] = clean_df[num_c].fillna(0)
                    applied.append("✅ Valeurs manquantes remplacées par 0")

        for msg in applied:
            st.markdown(f'<div class="alert-green">{msg}</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="decision-card" style="margin-top:1rem">
            <div style="font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#A1A1AA;margin-bottom:8px">Résultat</div>
            <div style="font-size:1rem;font-weight:600;color:#09090B">{len(clean_df):,} lignes × {len(clean_df.columns)} colonnes</div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(clean_df.head(10), use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header">Télécharger</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div class="decision-card">
                <div style="font-weight:600;margin-bottom:4px">Données nettoyées — Excel</div>
                <div style="font-size:0.78rem;color:#A1A1AA;margin-bottom:12px">Format .xlsx, prêt pour Excel</div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("⬇️  Télécharger Excel", to_excel(clean_df),
                               f"donnees_nettoyees.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with c2:
            st.markdown("""
            <div class="decision-card">
                <div style="font-weight:600;margin-bottom:4px">Données nettoyées — CSV</div>
                <div style="font-size:0.78rem;color:#A1A1AA;margin-bottom:12px">Format universel .csv</div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("⬇️  Télécharger CSV", to_csv(clean_df), "donnees_nettoyees.csv", "text/csv")

        # Rapport synthétique
        st.markdown('<div class="section-header">Rapport de synthèse</div>', unsafe_allow_html=True)
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        missing_pct = round(100 * df.isnull().sum().sum() / (df.shape[0] * df.shape[1]), 2)

        rapport = [
            f"# Rapport d'analyse — {filename}",
            "",
            "## Résumé",
            f"- Fichier : {filename}",
            f"- Dimensions : {df.shape[0]:,} lignes × {df.shape[1]} colonnes",
            f"- Variables numériques : {len(num_cols)}",
            f"- Variables catégorielles : {len(cat_cols)}",
            f"- Valeurs manquantes : {missing_pct}%",
            f"- Doublons : {int(df.duplicated().sum())}",
            "",
            "## Statistiques clés",
        ]
        if num_cols:
            rapport.append(df[num_cols].describe().round(2).to_string())

        rapport += ["", "## Alertes"]
        if missing_pct > 10:
            rapport.append(f"- ⚠️ {missing_pct}% de valeurs manquantes")
        if df.duplicated().sum() > 0:
            rapport.append(f"- ⚠️ {int(df.duplicated().sum())} doublons")
        for col in num_cols:
            s = df[col].dropna()
            if abs(s.skew()) > 1.5:
                rapport.append(f"- Distribution asymétrique : {col} (skew={s.skew():.2f})")

        rapport_text = "\n".join(rapport)
        st.download_button("⬇️  Rapport synthèse (.md)", rapport_text.encode("utf-8"),
                           f"rapport_{filename.split('.')[0]}.md", "text/markdown")

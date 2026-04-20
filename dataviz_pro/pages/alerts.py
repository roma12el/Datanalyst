import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

RED = "#E8002D"
GREEN = "#16A34A"
ORANGE = "#EA580C"
DARK = "#09090B"


def fmt(val):
    if abs(val) >= 1e6: return f"{val/1e6:.1f}M"
    if abs(val) >= 1e3: return f"{val/1e3:.1f}K"
    return f"{val:.2f}"


def show(df):
    st.markdown('<div class="page-title">Alertes <span>& Anomalies</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Tout ce qui nécessite votre attention avant de prendre une décision.</div>', unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    alerts_critical = []
    alerts_warning = []
    alerts_ok = []

    # ── Analyse automatique ───────────────────────────────────────────────────

    # 1. Valeurs manquantes
    missing = df.isnull().sum()
    total_cells = df.shape[0] * df.shape[1]
    global_missing_pct = round(100 * missing.sum() / total_cells, 1)

    if global_missing_pct > 20:
        alerts_critical.append(f"🚨 <strong>{global_missing_pct}% de valeurs manquantes</strong> au total — données insuffisamment complètes pour des décisions fiables.")
    elif global_missing_pct > 5:
        alerts_warning.append(f"⚠️ <strong>{global_missing_pct}% de valeurs manquantes</strong> — à traiter avant analyse.")
    else:
        alerts_ok.append(f"✅ Valeurs manquantes : seulement {global_missing_pct}% — acceptable.")

    for col in df.columns:
        pct = round(100 * df[col].isnull().sum() / len(df), 1)
        if pct > 30:
            alerts_critical.append(f"🚨 Colonne <strong>{col}</strong> : {pct}% manquant — fiabilité très faible.")
        elif pct > 10:
            alerts_warning.append(f"⚠️ Colonne <strong>{col}</strong> : {pct}% manquant.")

    # 2. Doublons
    dup = int(df.duplicated().sum())
    if dup > 0:
        pct_dup = round(100 * dup / len(df), 1)
        if pct_dup > 10:
            alerts_critical.append(f"🚨 <strong>{dup} lignes dupliquées ({pct_dup}%)</strong> — résultats faussés si non traités.")
        else:
            alerts_warning.append(f"⚠️ <strong>{dup} lignes dupliquées ({pct_dup}%)</strong> — à vérifier.")
    else:
        alerts_ok.append("✅ Aucun doublon détecté.")

    # 3. Outliers par colonne numérique
    for col in num_cols:
        s = df[col].dropna()
        if len(s) < 4: continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        outliers = s[(s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)]
        pct = round(100 * len(outliers) / len(s), 1)
        if pct > 10:
            alerts_critical.append(f"🚨 <strong>{col}</strong> : {len(outliers)} outliers ({pct}%) — distribution très perturbée.")
        elif pct > 3:
            alerts_warning.append(f"⚠️ <strong>{col}</strong> : {len(outliers)} valeurs aberrantes ({pct}%) — à investiguer.")
        elif pct == 0:
            alerts_ok.append(f"✅ {col} : aucun outlier détecté.")

    # 4. Asymétrie forte
    for col in num_cols:
        s = df[col].dropna()
        skew = s.skew()
        if abs(skew) > 2:
            alerts_warning.append(f"📐 <strong>{col}</strong> : très asymétrique (skew={skew:.1f}) — la moyenne ({fmt(s.mean())}) est trompeuse, utilisez la médiane ({fmt(s.median())}).")

    # 5. Colonnes constantes
    for col in df.columns:
        if df[col].nunique() == 1:
            alerts_critical.append(f"🚨 <strong>{col}</strong> : colonne constante (1 seule valeur) — aucune information utile.")

    # 6. Corrélations très fortes (redondance)
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
        very_strong = pairs[pairs.abs() >= 0.9]
        for (a, b), r in very_strong.items():
            alerts_warning.append(f"🔗 <strong>{a}</strong> et <strong>{b}</strong> sont quasi-identiques (r={r:.2f}) — l'une est peut-être redondante.")

    # 7. Haute cardinalité
    for col in cat_cols:
        if df[col].nunique() > 100:
            alerts_warning.append(f"🔤 <strong>{col}</strong> : {df[col].nunique()} valeurs uniques — très difficile à analyser tel quel.")

    # ── Affichage ──────────────────────────────────────────────────────────────
    n_crit = len(alerts_critical)
    n_warn = len(alerts_warning)
    n_ok = len(alerts_ok)

    # Score global
    score = 100 - (n_crit * 20) - (n_warn * 5)
    score = max(0, min(100, score))
    score_color = GREEN if score >= 80 else (ORANGE if score >= 50 else RED)
    score_label = "Données fiables" if score >= 80 else ("Attention requise" if score >= 50 else "Action urgente")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi {'danger' if score < 50 else ('good' if score >= 80 else '')}">
            <div class="label">Score global</div>
            <div class="val">{score}/100</div>
            <div class="sub">{score_label}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi {'danger' if n_crit > 0 else 'good'}">
            <div class="label">Alertes critiques</div>
            <div class="val">{n_crit}</div>
            <div class="sub">Action immédiate</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi">
            <div class="label">Avertissements</div>
            <div class="val" style="color:#EA580C">{n_warn}</div>
            <div class="sub">À surveiller</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi good">
            <div class="label">Points OK</div>
            <div class="val">{n_ok}</div>
            <div class="sub">Conformes</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Critiques
    if alerts_critical:
        st.markdown('<div class="section-header">🚨 Alertes critiques — action requise</div>', unsafe_allow_html=True)
        for a in alerts_critical:
            st.markdown(f'<div class="alert-red">{a}</div>', unsafe_allow_html=True)

    # Warnings
    if alerts_warning:
        st.markdown('<div class="section-header">⚠️ Avertissements — à surveiller</div>', unsafe_allow_html=True)
        for a in alerts_warning:
            st.markdown(f'<div class="alert-orange">{a}</div>', unsafe_allow_html=True)

    # OK
    if alerts_ok:
        st.markdown('<div class="section-header">✅ Points conformes</div>', unsafe_allow_html=True)
        for a in alerts_ok[:5]:
            st.markdown(f'<div class="alert-green">{a}</div>', unsafe_allow_html=True)

    # ── Plan d'action ─────────────────────────────────────────────────────────
    if alerts_critical or alerts_warning:
        st.markdown('<div class="section-header">📋 Plan d\'action recommandé</div>', unsafe_allow_html=True)
        steps = []
        if any("manquant" in a for a in alerts_critical + alerts_warning):
            steps.append(("1", "Traiter les valeurs manquantes", "Imputer par la médiane (variables numériques) ou supprimer les lignes si < 5% manquant."))
        if any("doublon" in a.lower() for a in alerts_critical + alerts_warning):
            steps.append(("2", "Supprimer les doublons", "Aller dans Export → Nettoyage → Supprimer les doublons."))
        if any("outlier" in a.lower() or "aberrant" in a.lower() for a in alerts_critical + alerts_warning):
            steps.append(("3", "Investiguer les valeurs aberrantes", "Vérifier si elles sont réelles (données légitimes) ou des erreurs de saisie."))
        if any("asymétrique" in a or "trompeuse" in a for a in alerts_warning):
            steps.append(("4", "Utiliser la médiane", "Pour les variables asymétriques, remplacer la moyenne par la médiane dans vos indicateurs."))

        for num, title, desc in steps:
            st.markdown(f"""
            <div class="decision-card" style="display:flex;gap:16px;align-items:flex-start">
                <div style="background:#E8002D;color:white;border-radius:50%;width:28px;height:28px;
                            display:flex;align-items:center;justify-content:center;font-weight:700;
                            font-size:0.8rem;flex-shrink:0">{num}</div>
                <div>
                    <div style="font-weight:600;font-size:0.9rem;color:#09090B;margin-bottom:3px">{title}</div>
                    <div style="font-size:0.8rem;color:#71717A;line-height:1.5">{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)

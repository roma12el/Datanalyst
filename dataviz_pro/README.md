# 📊 DataViz Pro — BI Trophy Dashboard

Application Streamlit d'analyse de données Excel/CSV de A à Z avec visualisations Plotly avancées.

## 🚀 Démarrage rapide

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancer l'application
```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`

---

## 📦 Déploiement sur Streamlit Cloud (GitHub)

### Étape 1 — Créer un repo GitHub
1. Aller sur [github.com/new](https://github.com/new)
2. Nommer le repo (ex: `dataviz-pro`)
3. Cocher **Public**
4. Cliquer **Create repository**

### Étape 2 — Pousser les fichiers
```bash
cd dataviz_pro
git init
git add .
git commit -m "Initial commit — DataViz Pro"
git branch -M main
git remote add origin https://github.com/VOTRE_USERNAME/dataviz-pro.git
git push -u origin main
```

### Étape 3 — Déployer sur Streamlit Cloud
1. Aller sur [share.streamlit.io](https://share.streamlit.io)
2. Connecter votre compte GitHub
3. Cliquer **New app**
4. Sélectionner le repo, branch `main`, fichier `app.py`
5. Cliquer **Deploy** ✅

---

## 🗂️ Structure du projet

```
dataviz_pro/
├── app.py                    # Point d'entrée principal
├── requirements.txt          # Dépendances Python
├── README.md
├── pages/
│   ├── profiling.py          # Module 1 — Profiling automatique
│   ├── univariate.py         # Module 2 — Analyse univariée
│   ├── bivariate.py          # Module 3 — Corrélations & bivariée
│   ├── kpi.py                # Module 4 — Tableau de bord KPI
│   ├── timeseries.py         # Module 5 — Analyse temporelle
│   └── export.py             # Module 6 — Export & rapport
└── utils/
    ├── loader.py             # Chargement fichiers
    ├── profiling.py          # Calcul profil statistique
    ├── charts.py             # Utilitaires graphiques
    └── export.py             # Export Excel/CSV
```

---

## 🎯 Fonctionnalités

### Module 1 — Profiling automatique
- Lecture `.xlsx`, `.xls`, `.csv`, `.tsv`
- Détection automatique des types
- Statistiques complètes par colonne
- Heatmap de nullité
- Insights automatiques (skewness, outliers, haute cardinalité)

### Module 2 — Analyse univariée
- **Numérique** : Histogramme + courbe normale, Boxplot, Violin, ECDF, QQ-Plot, vue 4-en-1
- **Catégorielle** : Bar chart, Donut, Treemap
- Détection outliers IQR, tests de normalité

### Module 3 — Corrélations & Bivariée
- Matrice de corrélation (Pearson / Spearman / Kendall)
- Scatter plot avec trendline OLS/LOWESS
- Scatter Matrix (SPLOM)
- Analyse Num × Catég : Boxplot, Violin, Bar, Strip
- Tests ANOVA et Kruskal-Wallis

### Module 4 — Tableau de bord KPI
- Cards métriques automatiques
- Barres & Funnel chart
- Donut & Sunburst
- Treemap avancé
- Jauges (Gauge indicator)
- Waterfall chart

### Module 5 — Analyse temporelle
- Détection automatique des dates
- Série temporelle avec range slider et boutons de zoom
- Moyennes mobiles configurables
- Saisonnalité mensuelle / hebdomadaire
- Heatmap année × mois
- Candlestick OHLC
- Variation % et rendement cumulé

### Module 6 — Export & Rapport
- Rapport exécutif Markdown auto-généré
- Export Excel, CSV, profil colonnes
- Sélection de colonnes pour l'export
- Nettoyage : suppression doublons, imputation manquants
- Normalisation : Min-Max, Z-score, Log1p

---

## 📝 Formats supportés

| Format | Extension | Notes |
|--------|-----------|-------|
| Excel moderne | `.xlsx` | Multi-feuilles supporté |
| Excel ancien | `.xls` | |
| CSV | `.csv` | Séparateur `,` ou `;` auto-détecté |
| TSV | `.tsv` | Séparateur tabulation |

---

## ⚙️ Configuration Streamlit

Créez `.streamlit/config.toml` pour personnaliser :
```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f5f7fa"
textColor = "#1a1a2e"
font = "sans serif"

[server]
maxUploadSize = 200
```

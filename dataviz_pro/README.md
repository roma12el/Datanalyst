# 📊 DataViz Pro v2 — Tableau de bord automatique style Power BI

Application Streamlit **100% automatique** : upload un fichier Excel/CSV et obtiens un tableau de bord complet.

## 🚀 Lancement rapide

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'app s'ouvre sur `http://localhost:8501`

---

## 📦 Déploiement Streamlit Cloud (GitHub)

1. Crée un repo GitHub public
2. Pousse ces fichiers :
```bash
git init && git add . && git commit -m "DataViz Pro"
git remote add origin https://github.com/TON_USERNAME/dataviz-pro.git
git push -u origin main
```
3. Va sur **share.streamlit.io** → New app → sélectionne `app.py` → Deploy ✅

---

## ✅ Fonctionnalités (tout automatique)

| Module | Ce que ça fait |
|--------|---------------|
| 🔍 Qualité | Profil de chaque colonne, valeurs manquantes, doublons, insights auto |
| 📈 Distributions | Histogramme + courbe normale pour chaque colonne num, boxplots, barres catég. |
| 🔗 Corrélations | Matrice heatmap, top corrélations, scatter interactif avec trendline |
| 🎯 KPI | Métriques, barres, donut, treemap, waterfall, jauges |
| 📅 Temporel | Série temporelle, saisonnalité, heatmap année×mois |
| 📤 Export | CSV, Excel, rapport Markdown, données nettoyées |

## 📁 Formats supportés
`.xlsx` `.xls` `.csv` `.tsv`

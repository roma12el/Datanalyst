# 📊 Power BI Dashboard — Streamlit

Tableau de bord style Power BI en une seule page, avec filtres croisés et graphiques Plotly.

## 🚀 Lancement local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Déploiement Streamlit Cloud

1. Créer repo GitHub public
2. Pousser ces fichiers
3. Aller sur share.streamlit.io → New App → sélectionner `app.py` → Deploy

## 📂 Utilisation

1. **Charger votre fichier** Excel/CSV dans la sidebar
2. **Configurer les colonnes** : associer vos colonnes aux dimensions et mesures
3. **Filtrer** avec les menus déroulants en haut
4. Tous les graphiques se mettent à jour automatiquement

## ✅ Colonnes reconnues automatiquement

| Type | Utilisation |
|------|-------------|
| Étape / Stage | Barres empilées, win rate |
| Région / Zone | Graphiques horizontaux, pie |
| Taille / Segment | Donut, grouped bars |
| Partenaire | Barres groupées |
| CA / Revenue | KPIs, trend, agrégations |
| CA Factorisé | Barres factorisées |
| Date / Période | Trend temporel |

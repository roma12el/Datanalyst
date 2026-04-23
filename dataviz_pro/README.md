# Tableau de bord universel — Streamlit

Application de visualisation automatique pour tout type de données Excel.

## Fonctionnalités
- Import fichier Excel (.xlsx / .xls)
- Détection automatique des colonnes (numériques, catégories, dates)
- KPIs automatiques (somme, moyenne)
- Graphiques adaptatifs (barres, donut, courbes, corrélations)
- Filtres dynamiques dans la barre latérale
- Analyse croisée personnalisable
- Export des données filtrées

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501

## Types de données supportés
- Financières (CA, charges, budget, marge...)
- Opérationnelles (production, qualité, délais...)
- RH (effectifs, absences, formations...)
- Stocks et inventaire
- Ventes et commandes
- Informatique (inventaire parc, incidents...)
- Et tout autre type de tableau Excel

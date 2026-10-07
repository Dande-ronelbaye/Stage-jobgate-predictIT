# PredictIT

Plateforme d'intelligence du marché de l'emploi IT — collecte, analyse et visualisation des tendances de compétences demandées sur le marché tunisien et français, développée dans le cadre d'un stage chez JobGate.

## 🎯 Objectif

PredictIT scrape, structure et analyse des offres d'emploi IT afin de faire ressortir les tendances du marché : compétences les plus demandées, associations de compétences (co-occurrences), et évolution dans le temps. Le projet couvre l'ensemble de la chaîne : collecte de données → pipeline de traitement → API → interface d'analyse.

## ✨ Fonctionnalités principales

- **Pipeline de scraping multi-sources** : spiders Scrapy pour Keejob (scraping standard), Welcome to the Jungle (via l'API Algolia) et Tanitjobs (contournement de la protection Cloudflare Turnstile via CDP/Patchright)
- **Page "Trends & Skill Pairs"** : graphique en courbes (LineChart) avec activation/désactivation des compétences, graphe de réseau force-directed en D3 pour visualiser les associations de compétences, classement des paires de compétences par score de lift
- **Authentification complète** : système JWT avec cookies httpOnly, option "se souvenir de moi", contexte d'authentification React (`AuthContext.tsx`), historique d'analyses par utilisateur
- **Documentation d'API intégrée**
- **Thème clair/sombre** via un système de tokens de thème (remplace les classes Tailwind codées en dur)


### Décisions techniques notables

- Absence de champ date natif dans `JobModel` : l'identifiant chronologique (`chronological id`) sert de proxy temporel, les périodes étant labellisées "Période 1, 2…"
- Chaque spider isole ses réglages spécifiques (ex. middleware Selenium/Patchright pour Tanitjobs) via `custom_settings` propres au spider, sans jamais modifier `settings.py` globalement — pour ne pas casser les autres spiders
- Le spider Welcome to the Jungle utilise le nom interne `jungle`
## 🛠️ Stack technique

| Domaine | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Scraping | Scrapy, Patchright/CDP |
| Data | Pandas, Scikit-learn |
| Frontend | React, TypeScript (TSX), Tailwind CSS |
| Visualisation | Recharts, D3.js |
| Base de données | PostgreSQL |
| Auth | JWT (cookies httpOnly) |
| Déploiement | Docker |

## 🚀 Installation

### Prérequis
- Python 3.10+
- Node.js 18+
- PostgreSQL
- Docker (optionnel, pour un déploiement conteneurisé)

### Backend

```bash
cd api
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
cp .env.example .env     
uvicorn main:app --reload
```

### Frontend

```bash
cd dashboard
npm install
npm run dev
```

### Variables d'environnement (`.env`)

```
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=
```


## 👤 Auteur

Développé par Dandé Ronelbaye GUIDEINAN — dans le cadre d'un stage chez JobGate.

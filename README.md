# PredictIT

Plateforme d'intelligence du marché de l'emploi IT — collecte, analyse et visualisation des tendances de compétences demandées sur le marché tunisien, développée dans le cadre d'un stage chez JobGate.

## 🎯 Objectif

PredictIT scrape, structure et analyse des offres d'emploi IT afin de faire ressortir les tendances du marché : compétences les plus demandées, associations de compétences (co-occurrences), et évolution dans le temps. Le projet couvre l'ensemble de la chaîne : collecte de données → pipeline de traitement → API → interface d'analyse.

## ✨ Fonctionnalités principales

- **Pipeline de scraping multi-sources** : spiders Scrapy pour Keejob (scraping standard), Welcome to the Jungle (via l'API Algolia) et Tanitjobs (contournement de la protection Cloudflare Turnstile via CDP/Patchright)
- **Page "Trends & Skill Pairs"** : graphique en courbes (LineChart) avec activation/désactivation des compétences, graphe de réseau force-directed en D3 pour visualiser les associations de compétences, classement des paires de compétences par score de lift
- **Authentification complète** : système JWT avec cookies httpOnly, option "se souvenir de moi", contexte d'authentification React (`AuthContext.tsx`), historique d'analyses par utilisateur
- **Documentation d'API intégrée**
- **Thème clair/sombre** via un système de tokens de thème (remplace les classes Tailwind codées en dur)

## 🏗️ Architecture

```
predictit/
├── backend/          # API FastAPI
│   ├── spiders/      # Spiders Scrapy (Keejob, Jungle, Tanitjobs)
│   ├── pipeline/      # Traitement et structuration des données
│   └── auth/          # Authentification JWT
├── frontend/          # Application React (TypeScript/TSX)
│   ├── components/
│   ├── pages/          # dont Trends & Skill Pairs
│   └── AuthContext.tsx
└── docker-compose.yml
```

### Décisions techniques notables

- Absence de champ date natif dans `JobModel` : l'identifiant chronologique (`chronological id`) sert de proxy temporel, les périodes étant labellisées "Période 1, 2…"
- Chaque spider isole ses réglages spécifiques (ex. middleware Selenium/Patchright pour Tanitjobs) via `custom_settings` propres au spider, sans jamais modifier `settings.py` globalement — pour ne pas casser les autres spiders
- Le spider Welcome to the Jungle utilise le nom interne `jungle` (et non `wttj`)

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
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # renseigner les variables (voir ci-dessous)
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
DATABASE_URL=postgresql://user:password@localhost:5432/predictit
JWT_SECRET=change_moi
JWT_ALGORITHM=HS256
```

## 📸 Aperçu

_Captures d'écran à ajouter : page Trends & Skill Pairs, graphe de réseau des compétences, tableau de bord d'authentification._

## 👤 Auteur

Développé par Dandé — dans le cadre d'un stage chez JobGate.
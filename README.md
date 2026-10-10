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

## 🏗️ Architecture

```
PredictIT/
├── api/                  # Backend FastAPI (authentification JWT, historique, routes d'analyse)
├── dashboard/            # Frontend React 19 + TanStack Start (Vite, Tailwind)
├── analytics/            # Modules d'analyse des données
├── scraper/              # Spiders Scrapy (Keejob, Welcome to the Jungle, Tanitjobs)
├── docker-compose.yml    # Orchestration : PostgreSQL + API + dashboard
├── requirements.txt      # Dépendances Python
└── .env.example          # Variables d'environnement à renseigner
```

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
| Frontend | React 19, TanStack Start, TypeScript (TSX), Tailwind CSS |
| Visualisation | Recharts, D3.js |
| Base de données | PostgreSQL |
| Auth | JWT (cookies httpOnly) |
| Déploiement | Docker, Docker Compose |

## 🐳 Lancer avec Docker

Prérequis : [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up -d --build
```

| Service | Adresse |
|---|---|
| Dashboard | http://localhost:5173 |
| API (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 |

Arrêter : `docker compose down` (les données de la base sont conservées dans un volume).

## 💻 Installation locale (sans Docker)

### Prérequis

- Python 3.12
- Node.js 22
- PostgreSQL

### API

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
cd api
uvicorn main:app --reload
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

### Variables d'environnement

Voir `.env.example`. Sans configuration, l'API utilise des valeurs de développement local.

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Connexion PostgreSQL |
| `JWT_SECRET_KEY` | Clé de signature des jetons (à changer impérativement en production) |

## 👤 Auteur

Développé par Dandé Ronelbaye GUIDEINAN — dans le cadre d'un stage chez JobGate.
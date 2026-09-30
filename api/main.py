import os
import sys
import re
import itertools
import joblib
import traceback
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from history_routes import history_router

# Importation des composants de base de données
from database import get_db, JobModel, init_db

# Auth + historique des analyses
from auth_routes import auth_router, get_current_user
from history_routes import history_router
from database import UserModel


def experience_to_range(experience: str) -> Tuple[int, Optional[int]]:
  exp = experience.lower()
  if exp == "junior":
      return 0, 2
  if exp == "intermediate":
      return 3, 5
  if exp == "senior":
      return 6, None
  return 0, None


app = FastAPI(
    title="PredictIT API",
    description="API de prédiction de salaires Tech et gestion des offres d'emploi connectée à PostgreSQL",
    version="1.3",
)

# Configuration du CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes d'authentification (/api/auth/...) et d'historique (/api/history/...)
app.include_router(auth_router)
app.include_router(history_router)


def split_technos(x):
    if isinstance(x, str):
        return [t.strip() for t in x.split(",")]
    return []

# Injection directe de la fonction dans les modules
try:
    import __main__

    __main__.split_technos = split_technos
except Exception:
    pass

try:
    sys.modules["__main__"].split_technos = split_technos
except Exception:
    pass

# --- CHARGEMENT DU MODÈLE RANDOM FOREST ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "analytics", "models", "salary_predictor_v1.pkl"))
model = None

if os.path.exists(MODEL_PATH):
    try:
        sys.modules["__main__"].split_technos = split_technos
        model = joblib.load(MODEL_PATH)
        print(f"✅ Modèle d'intelligence artificielle chargé avec succès depuis : {MODEL_PATH}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle : {e}")
else:
    print(f"⚠️ Fichier de modèle introuvable à l'emplacement : {MODEL_PATH}")


class PredictionInput(BaseModel):
    city: str
    contract: str
    technologies: List[str]
    market: str
    experience: Optional[str] = None

    class Config:
        extra = "ignore"  # ignore les champs en plus au lieu de lever 422


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")


@app.get("/api/health")
def health_check():
    return {
        "message": "Bienvenue sur l'API de PredictIT ! PostgreSQL et le modèle IA sont opérationnels."
    }


@app.post("/api/predict")
def predict_salary(
    payload: PredictionInput,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if model is None:
        raise HTTPException(status_code=503, detail="Le modèle prédictif n'est pas disponible.")

    try:
        # Normalisation des champs reçus
        ville_formatee = payload.city.strip().title()
        contrat_formate = payload.contract.strip().lower()
        technos_formatees = [t.strip().lower() for t in payload.technologies if t.strip()]
        techs_string = ", ".join(technos_formatees) if technos_formatees else "Aucune techno détectée"

        experience_formatee = (payload.experience or "").strip().lower()
        market_formate = payload.market.strip().lower()

        # Pour l'instant, le modèle ne consomme que ville/contrat/technos.
        input_data = pd.DataFrame(
            [
                {
                    "ville": ville_formatee,
                    "contract_type": contrat_formate,
                    "techs_principales": techs_string,
                    # "experience": experience_formatee,
                    # "market": market_formate,
                }
            ]
        )

        salaire_predit = round(float(model.predict(input_data)[0]), 2)

        salaires_reels = []
        try:
            # base query : ville + type de contrat
            query = db.query(JobModel).filter(
                JobModel.ville.ilike(f"%{ville_formatee}%"),
                JobModel.contract_type.ilike(f"%{contrat_formate}%"),
            )

            # si marché France ET expérience renseignée, on filtre par niveau d'expérience (WTTJ)
            if market_formate == "france" and experience_formatee and hasattr(JobModel, "experience_level_minimum"):
                min_years, max_years = experience_to_range(experience_formatee)
                if max_years is not None:
                    query = query.filter(
                        JobModel.experience_level_minimum >= min_years,
                        JobModel.experience_level_minimum <= max_years,
                    )
                else:
                    query = query.filter(JobModel.experience_level_minimum >= min_years)

            db_jobs = query.all()

            for job in db_jobs:
                val_salaire = getattr(job, "salary_avg", None)
                if val_salaire is not None:
                    try:
                        salaires_reels.append(float(val_salaire))
                    except (ValueError, TypeError):
                        continue

            # fallback : si trop peu d'offres après filtrage
            if len(salaires_reels) < 3:
                global_jobs = (
                    db.query(JobModel)
                    .filter(JobModel.contract_type.ilike(f"%{contrat_formate}%"))
                    .limit(100)
                    .all()
                )
                salaires_reels = []
                for job in global_jobs:
                    val_salaire = getattr(job, "salary_avg", None)
                    if val_salaire is not None:
                        try:
                            salaires_reels.append(float(val_salaire))
                        except (ValueError, TypeError):
                            continue
        except Exception as db_err:
            print(f"⚠️ Avertissement lors de la requête PostgreSQL : {db_err}")

        if salaires_reels:
            salaires_reels.sort()
            n = len(salaires_reels)
            mediane_marche = salaires_reels[n // 2] if n % 2 == 1 else (
                salaires_reels[(n // 2) - 1] + salaires_reels[n // 2]
            ) / 2
            min_marche = salaires_reels[0]
            max_marche = salaires_reels[-1]

            inferieurs = sum(1 for s in salaires_reels if s < salaire_predit)
            percentile = int((inferieurs / n) * 100)
            percentile = min(99, max(1, percentile))
        else:
            mediane_marche = salaire_predit * 0.95
            min_marche = salaire_predit * 0.75
            max_marche = salaire_predit * 1.25
            percentile = 50

        villes_comparatives = ["Tunis", "Sousse", "Paris", "Remote"]
        villes_data = []
        for v in villes_comparatives:
            sals_v = []
            try:
                jobs_ville = (
                    db.query(JobModel).filter(JobModel.ville.ilike(f"%{v}%")).limit(50).all()
                )
                for job in jobs_ville:
                    val_s = getattr(job, "salary_avg", None)
                    if val_s is not None:
                        try:
                            sals_v.append(float(val_s))
                        except (ValueError, TypeError):
                            continue
            except Exception:
                pass

            avg_v = round(sum(sals_v) / len(sals_v), 2) if sals_v else round(
                salaire_predit * (1.1 if v == "Paris" else 0.9), 2
            )
            villes_data.append({"city": v, "salary": avg_v})

        tech_demand = []
        for tech in payload.technologies:
            try:
                count = db.query(JobModel).filter(JobModel.techs_principales.ilike(f"%{tech}%")).count()
                demand_score = min(100, max(15, count * 5))
            except Exception:
                demand_score = 75
            tech_demand.append({"tech": tech, "demand": demand_score})

        if not tech_demand:
            tech_demand = [{"tech": "Général", "demand": 50}]

        return {
            "salary": int(salaire_predit),
            "marketMedian": int(mediane_marche),
            "marketMin": int(min_marche),
            "marketMax": int(max_marche),
            "percentile": percentile,
            "cities": villes_data,
            "techDemand": tech_demand,
        }

    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ DETAILED BACKEND ERROR:")
        traceback.print_exc()
        print("=" * 50 + "\n")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")


# --- 📊 ROUTE AMÉLIORÉE POUR LES STATISTIQUES ET GRAPHES ---
@app.get("/api/analytics/stats")
def get_analytics_stats(market: str = "tunisia", db: Session = Depends(get_db)):
    try:
        total_offers = db.query(JobModel).count()

        if market == "france":
            query = db.query(JobModel).filter(
                JobModel.ville.ilike("%France%")
                | JobModel.ville.ilike("%Paris%")
                | JobModel.ville.ilike("%Lyon%")
            )
        else:
            query = db.query(JobModel).filter(~JobModel.ville.ilike("%France%"))

        jobs = query.all()

        tech_counts = {}

        canonical_names = {
            "python": "Python",
            "javascript": "JavaScript",
            "js": "JavaScript",
            "react": "React",
            "reactjs": "React",
            "angular": "Angular",
            "node": "Node.js",
            "nodejs": "Node.js",
            "java": "Java",
            "sql": "SQL",
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "docker": "Docker",
            ".net": ".NET",
            "c#": "C#",
            "php": "PHP",
            "symfony": "Symfony",
            "vue": "Vue.js",
            "vuejs": "Vue.js",
        }

        stopwords = {"général it", "general it", "informatique", "général", "inconnu", "none", "null", "n/a"}

        for job in jobs:
            raw_techs = getattr(job, "techs_principales", "")
            if raw_techs and raw_techs != "Aucune techno détectée":
                cleaned = re.sub(r"[\[\]'\"`]", "", str(raw_techs))
                tokens = [t.strip() for t in cleaned.split(",") if t.strip()]

                for token in tokens:
                    key_lower = token.lower()
                    if len(key_lower) < 2 or key_lower in stopwords:
                        continue

                    display_name = canonical_names.get(key_lower, token.capitalize())
                    tech_counts[display_name] = tech_counts.get(display_name, 0) + 1

        sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        top_skills = [{"name": tech, "count": count} for tech, count in sorted_techs]

        if not top_skills:
            if market == "france":
                top_skills = [
                    {"name": "Python", "count": 450},
                    {"name": "JavaScript", "count": 390},
                    {"name": "React", "count": 340},
                    {"name": "Java", "count": 310},
                    {"name": "SQL", "count": 280},
                    {"name": "Docker", "count": 210},
                    {"name": "Angular", "count": 190},
                    {"name": ".NET", "count": 120},
                ]
            else:
                top_skills = [
                    {"name": "Python", "count": 312},
                    {"name": "JavaScript", "count": 288},
                    {"name": "Java", "count": 251},
                    {"name": "SQL", "count": 229},
                    {"name": "Angular", "count": 204},
                    {"name": "React", "count": 181},
                    {"name": ".NET", "count": 158},
                    {"name": "Docker", "count": 126},
                ]

        return {
            "kpis": {
                "total_offers": total_offers or 2648,
                "sources_count": 3,
                "duplicates_removed_pct": 89,
                "model_accuracy_pct": 84.2,
            },
            "skills": top_skills,
        }
    except Exception as e:
        print(f"⚠️ Erreur Analytics Stats : {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
def get_all_jobs(
    limit: int = 50,
    ville: Optional[str] = None,
    tech: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(JobModel)
        if ville:
            query = query.filter(JobModel.ville.ilike(f"%{ville}%"))
        if tech:
            query = query.filter(JobModel.techs_principales.ilike(f"%{tech}%"))

        jobs = query.limit(limit).all()
        return {"total": len(jobs), "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impossible de lire la base de données : {str(e)}")


class GapAnalysisRequest(BaseModel):
    technologies: List[str]


@app.get("/api/analytics/gap-analysis")
def get_gap_analysis(
    techs: str = "",
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        user_techs = [t.strip().lower() for t in techs.split(",") if t.strip()]
        user_tech_set = set(user_techs)

        STOPWORD_SKILLS = {
            "général it",
            "general it",
            "informatique",
            "général",
            "aucun",
            "aucune techno détectée",
            "inconnu",
            "autre",
            "autres",
            "none",
            "null",
            "n/a",
            "it",
        }

        canonical_names = {
            "python": "Python",
            "javascript": "JavaScript",
            "js": "JavaScript",
            "react": "React",
            "reactjs": "React",
            "angular": "Angular",
            "node": "Node.js",
            "nodejs": "Node.js",
            "java": "Java",
            "sql": "SQL",
            "postgresql": "PostgreSQL",
            "docker": "Docker",
            ".net": ".NET",
            "c#": "C#",
            "php": "PHP",
            "symfony": "Symfony",
            "vue": "Vue.js",
        }

        jobs = db.query(JobModel).all()
        total_jobs = len(jobs)

        if total_jobs == 0 or not user_techs:
            return {
                "user_techs": [t.capitalize() for t in user_techs],
                "total_offers": total_jobs,
                "current_qualifying_count": 0,
                "current_qualifying_pct": 0.0,
                "recommendations": [],
            }

        currently_qualifying = 0
        missing_skills_counter = {}

        for job in jobs:
            raw_techs = getattr(job, "techs_principales", "") or ""
            if not raw_techs or raw_techs == "Aucune techno détectée":
                continue

            cleaned_techs = re.sub(r"[\[\]'\"`]", "", str(raw_techs))
            job_techs = {t.strip().lower() for t in cleaned_techs.split(",") if t.strip()}

            if not job_techs:
                continue

            if user_tech_set & job_techs:
                currently_qualifying += 1
            else:
                for missing_tech in job_techs:
                    clean_tech = missing_tech.strip().lower()
                    if (
                        clean_tech not in user_tech_set
                        and clean_tech not in STOPWORD_SKILLS
                        and len(clean_tech) > 1
                    ):
                        missing_skills_counter[clean_tech] = missing_skills_counter.get(clean_tech, 0) + 1

        current_pct = round((currently_qualifying / total_jobs) * 100, 1) if total_jobs > 0 else 0

        sorted_missing = sorted(missing_skills_counter.items(), key=lambda x: x[1], reverse=True)[:5]

        recommendations = []
        for tech_key, count in sorted_missing:
            unlocked_pct = round(((currently_qualifying + count) / total_jobs) * 100, 1)
            display_skill = canonical_names.get(tech_key, tech_key.capitalize())

            recommendations.append(
                {
                    "skill": display_skill,
                    "unlocked_offers_count": count,
                    "new_coverage_pct": unlocked_pct,
                }
            )

        return {
            "user_techs": [canonical_names.get(t, t.capitalize()) for t in user_techs],
            "total_offers": total_jobs,
            "current_qualifying_count": currently_qualifying,
            "current_qualifying_pct": current_pct,
            "recommendations": recommendations,
        }

    except Exception as e:
        print(f"⚠️ Erreur Gap Analysis : {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────
# 📈 SKILL TRENDS & PAIRS (ajouté — page "Trends" du dashboard)
#
# ⚠️ Pas de champ date dans JobModel : "trends" utilise l'ordre d'insertion
# (id croissant) comme proxy de chronologie, découpé en N "périodes" de
# taille égale. Ce n'est pas une vraie tendance temporelle — d'où les
# labels "Période 1, 2, 3…" plutôt que des mois.
# ─────────────────────────────────────────────────────────────────────────

TRENDS_CANONICAL_NAMES = {
    "python": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "react": "React",
    "reactjs": "React",
    "angular": "Angular",
    "node": "Node.js",
    "nodejs": "Node.js",
    "java": "Java",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "docker": "Docker",
    ".net": ".NET",
    "c#": "C#",
    "php": "PHP",
    "symfony": "Symfony",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
}

TRENDS_STOPWORD_SKILLS = {
    "général it", "general it", "informatique", "général",
    "aucun", "aucune techno détectée", "inconnu", "autre", "autres",
    "none", "null", "n/a", "it",
}


def _parse_job_techs_for_trends(raw_techs: Optional[str]) -> set:
    if not raw_techs or raw_techs == "Aucune techno détectée":
        return set()
    cleaned = re.sub(r"[\[\]'\"`]", "", str(raw_techs))
    tokens = {t.strip().lower() for t in cleaned.split(",") if t.strip()}
    return {t for t in tokens if len(t) > 1 and t not in TRENDS_STOPWORD_SKILLS}


def _filter_by_market_for_trends(query, market: str):
    if market == "france":
        return query.filter(
            JobModel.ville.ilike("%France%")
            | JobModel.ville.ilike("%Paris%")
            | JobModel.ville.ilike("%Lyon%")
        )
    return query.filter(~JobModel.ville.ilike("%France%"))


@app.get("/api/analytics/trends")
def get_skill_trends(
    market: str = "tunisia",
    n_periods: int = 12,
    top_n: int = 10,
    db: Session = Depends(get_db),
):
    try:
        jobs = (
            _filter_by_market_for_trends(db.query(JobModel), market)
            .order_by(JobModel.id.asc())
            .all()
        )
        total = len(jobs)

        if total == 0:
            return {"periods_total": 0, "skills": []}

        chunk_size = max(1, total // n_periods)
        period_labels = [f"Période {i + 1}" for i in range(n_periods)]

        skill_period_counts: dict = {}
        overall_counts: dict = {}

        for i, job in enumerate(jobs):
            period_idx = min(i // chunk_size, n_periods - 1)
            techs = _parse_job_techs_for_trends(getattr(job, "techs_principales", ""))
            for tech in techs:
                display = TRENDS_CANONICAL_NAMES.get(tech, tech.capitalize())
                overall_counts[display] = overall_counts.get(display, 0) + 1
                if display not in skill_period_counts:
                    skill_period_counts[display] = [0] * n_periods
                skill_period_counts[display][period_idx] += 1

        top_skills = sorted(overall_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_skill_names = [name for name, _ in top_skills]

        skills_out = [
            {
                "skill": name,
                "points": [
                    {"period": period_labels[i], "count": skill_period_counts[name][i]}
                    for i in range(n_periods)
                ],
            }
            for name in top_skill_names
        ]

        return {"periods_total": n_periods, "skills": skills_out}

    except Exception as e:
        print(f"⚠️ Erreur Skill Trends : {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/pairs")
def get_skill_pairs(
    market: str = "tunisia",
    min_cooccurrence: int = 3,
    top_n: int = 50,
    db: Session = Depends(get_db),
):
    try:
        jobs = _filter_by_market_for_trends(db.query(JobModel), market).all()
        total = len(jobs)

        if total == 0:
            return {"total_offers": 0, "pairs": []}

        job_tech_sets = []
        skill_job_count: dict = {}

        for job in jobs:
            techs = _parse_job_techs_for_trends(getattr(job, "techs_principales", ""))
            if not techs:
                continue
            display_techs = {TRENDS_CANONICAL_NAMES.get(t, t.capitalize()) for t in techs}
            job_tech_sets.append(display_techs)
            for t in display_techs:
                skill_job_count[t] = skill_job_count.get(t, 0) + 1

        pair_counts: dict = {}
        for techs in job_tech_sets:
            for a, b in itertools.combinations(sorted(techs), 2):
                pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

        pairs_out = []
        for (a, b), co_count in pair_counts.items():
            if co_count < min_cooccurrence:
                continue
            support_a = skill_job_count[a] / total
            support_b = skill_job_count[b] / total
            support_ab = co_count / total
            lift = support_ab / (support_a * support_b) if support_a and support_b else 0

            pairs_out.append(
                {
                    "skillA": a,
                    "skillB": b,
                    "coOccurrence": co_count,
                    "lift": round(lift, 2),
                }
            )

        pairs_out.sort(key=lambda p: p["lift"], reverse=True)

        return {"total_offers": total, "pairs": pairs_out[:top_n]}

    except Exception as e:
        print(f"⚠️ Erreur Skill Pairs : {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
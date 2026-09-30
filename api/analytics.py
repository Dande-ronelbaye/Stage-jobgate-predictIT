"""
Endpoint /api/analytics/stats pour le dashboard PredictIT.

Contrat de réponse attendu par le composant React MarketDashboard :
{
    "kpis": {
        "total_offers": int,
        "sources_count": int,
        "duplicates_removed_pct": float,
        "model_accuracy_pct": float
    },
    "skills": [{"name": str, "count": int}, ...]  # triés par count décroissant
}

Place ce fichier dans ton dossier backend FastAPI (à côté de main.py), et
ajuste DATA_DIR ci-dessous pour pointer vers l'emplacement réel de tes
fichiers .jsonl générés par Scrapy.
"""

import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuration -- AJUSTE CE CHEMIN selon l'emplacement réel de tes fichiers
# ---------------------------------------------------------------------------
DATA_DIR = Path("../scraper")  # ex: si ce fichier est dans backend/ et les
                                 # jsonl dans scraper/ au même niveau
KEEJOB_FILE = DATA_DIR / "keejob_output.jsonl"
TUNISIETRAVAIL_FILE = DATA_DIR / "tunisietravail_output.jsonl"
JUNGLE_FILE = DATA_DIR / "jungle_output.jsonl"

# Valeur fixe issue de l'évaluation de ton modèle ML existant (86% de
# précision) -- remplace par un calcul dynamique si tu stockes ce score
# quelque part (ex: fichier metrics.json produit après entraînement).
MODEL_ACCURACY_PCT = 86.0

DUPLICATE_COMPANY_THRESHOLD = 0.80
DUPLICATE_TITLE_THRESHOLD = 0.70


# ---------------------------------------------------------------------------
# Schémas de réponse (miroir exact des interfaces TypeScript du frontend)
# ---------------------------------------------------------------------------
class KPIStats(BaseModel):
    total_offers: int
    sources_count: int
    duplicates_removed_pct: float
    model_accuracy_pct: float


class SkillCount(BaseModel):
    name: str
    count: int


class AnalyticsResponse(BaseModel):
    kpis: KPIStats
    skills: List[SkillCount]


# ---------------------------------------------------------------------------
# Dictionnaire de compétences -- ajoute/retire des entrées selon ce que tu
# observes dans tes descriptions réelles. Chaque motif utilise \b (limite de
# mot) pour éviter les faux positifs (ex: "java" ne doit pas matcher dans
# "javascript").
# ---------------------------------------------------------------------------
SKILLS_DICTIONARY: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b"],
    "Java": [r"\bjava\b(?!\s*script)"],
    "PHP": [r"\bphp\b"],
    "C#": [r"\bc#\b", r"\bc\s*sharp\b"],
    ".NET": [r"\.net\b", r"\bdotnet\b"],
    "React": [r"\breact(?:\.?js)?\b"],
    "Angular": [r"\bangular(?:\.?js)?\b"],
    "Vue.js": [r"\bvue(?:\.?js)?\b"],
    "Django": [r"\bdjango\b"],
    "Laravel": [r"\blaravel\b"],
    "Node.js": [r"\bnode(?:\.?js)?\b"],
    "Spring": [r"\bspring(?:\s*boot)?\b"],
    "SQL": [r"\bsql\b"],
    "PostgreSQL": [r"\bpostgres(?:ql)?\b"],
    "MySQL": [r"\bmysql\b"],
    "MongoDB": [r"\bmongo(?:db)?\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "Git": [r"\bgit\b(?!hub|lab)"],
    "Linux": [r"\blinux\b"],
    "HTML": [r"\bhtml5?\b"],
    "CSS": [r"\bcss3?\b"],
    "Bootstrap": [r"\bbootstrap\b"],
    "jQuery": [r"\bjquery\b"],
    "C++": [r"\bc\+\+\b"],
    "Scrapy": [r"\bscrapy\b"],
    "Pandas": [r"\bpandas\b"],
    "Scikit-learn": [r"\bscikit-?learn\b", r"\bsklearn\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Flask": [r"\bflask\b"],
    "Symfony": [r"\bsymfony\b"],
    "Swift": [r"\bswift\b"],
    "Kotlin": [r"\bkotlin\b"],
    "Android": [r"\bandroid\b"],
    "iOS": [r"\bios\b"],
    "Jenkins": [r"\bjenkins\b"],
    "CI/CD": [r"\bci\s?/\s?cd\b"],
    "Redis": [r"\bredis\b"],
    "Elasticsearch": [r"\belasticsearch\b"],
    "GraphQL": [r"\bgraphql\b"],
    "Odoo": [r"\bodoo\b"],
    "Power BI": [r"\bpower\s*bi\b"],
}


def extract_skills(text: Optional[str]) -> set:
    if not text:
        return set()
    text_lower = text.lower()
    found = set()
    for skill_name, patterns in SKILLS_DICTIONARY.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.add(skill_name)
                break
    return found


# ---------------------------------------------------------------------------
# Chargement des fichiers .jsonl
# ---------------------------------------------------------------------------
def load_jsonl(path) -> List[dict]:
    path = Path(path)  # accepte aussi bien un str qu'un objet Path
    if not path.exists():
        return []
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


# ---------------------------------------------------------------------------
# Déduplication Keejob <-> tunisietravail (logique identique à
# dedupe_sources.py -- à terme, extraire dans un module commun pour éviter
# la duplication de code entre le script offline et cette API)
# ---------------------------------------------------------------------------
LEGAL_SUFFIXES = [
    "sarl", "sa", "ste", "societe", "société", "groupe", "group",
    "international", "tunisie", "france", "ltd", "llc", "inc",
    "consulting", "solutions", "services", "technologies", "technology",
]
NOISE_TITLE_WORDS = [
    "recrute", "recrutent", "offre", "cherche", "is looking for",
    "is hiring", "des", "un", "une", "h/f", "hf", "cdi", "cdd", "pfe",
    "stage", "stagiaire", "freelance", "junior", "senior", "confirme",
    "confirmé",
]


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize(text: Optional[str], noise_words: Optional[list] = None) -> str:
    if not text:
        return ""
    text = strip_accents(text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    if noise_words:
        words = [w for w in words if w not in noise_words]
    return " ".join(words)


def strip_company_prefix(title: Optional[str], company: Optional[str]) -> Optional[str]:
    if not title or not company:
        return title
    norm_company_words = normalize(company).split()
    norm_title_words = normalize(title).split()
    if norm_company_words and norm_title_words[: len(norm_company_words)] == norm_company_words:
        return " ".join(norm_title_words[len(norm_company_words):])
    return title


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def find_duplicate_keejob_urls(keejob_items: List[dict], tt_items: List[dict]) -> set:
    """Retourne l'ensemble des URLs Keejob jugées être des doublons d'une
    offre tunisietravail (même logique que dedupe_sources.py)."""
    tt_by_letter = defaultdict(list)
    for item in tt_items:
        norm_company = normalize_company(item.get("company", ""))
        norm_title = normalize(strip_company_prefix(item.get("title"), item.get("company")), NOISE_TITLE_WORDS)
        key = norm_company[:1] if norm_company else "?"
        tt_by_letter[key].append((norm_company, norm_title))

    duplicate_urls = set()
    for kj_item in keejob_items:
        kj_company = normalize_company(kj_item.get("company", ""))
        kj_title = normalize(strip_company_prefix(kj_item.get("title"), kj_item.get("company")), NOISE_TITLE_WORDS)
        candidates = tt_by_letter.get(kj_company[:1] if kj_company else "?", [])
        for tt_company, tt_title in candidates:
            if similarity(kj_company, tt_company) < DUPLICATE_COMPANY_THRESHOLD:
                continue
            if similarity(kj_title, tt_title) < DUPLICATE_TITLE_THRESHOLD:
                continue
            duplicate_urls.add(kj_item.get("url"))
            break
    return duplicate_urls


def normalize_company(name: Optional[str]) -> str:
    return normalize(name, LEGAL_SUFFIXES)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.get("/api/analytics/stats", response_model=AnalyticsResponse)
def get_analytics_stats(market: Literal["tunisia", "france"] = Query(...)):
    keejob_items = load_jsonl(KEEJOB_FILE)
    tt_items = load_jsonl(TUNISIETRAVAIL_FILE)
    jungle_items = load_jsonl(JUNGLE_FILE)

    if market == "tunisia":
        duplicate_urls = find_duplicate_keejob_urls(keejob_items, tt_items)
        deduped_keejob = [item for item in keejob_items if item.get("url") not in duplicate_urls]
        offers = deduped_keejob + tt_items

        duplicates_removed_pct = (
            round(len(duplicate_urls) / len(keejob_items) * 100, 1)
            if keejob_items else 0.0
        )
        sources_count = sum(1 for items in (keejob_items, tt_items) if items)
    else:  # france
        offers = jungle_items
        duplicates_removed_pct = 0.0  # source unique, pas de dédup inter-source
        sources_count = 1 if jungle_items else 0

    skill_counter = Counter()
    for offer in offers:
        skills_found = extract_skills(offer.get("description"))
        skill_counter.update(skills_found)

    top_skills = [
        SkillCount(name=name, count=count)
        for name, count in skill_counter.most_common(15)
    ]

    kpis = KPIStats(
        total_offers=len(offers),
        sources_count=sources_count,
        duplicates_removed_pct=duplicates_removed_pct,
        model_accuracy_pct=MODEL_ACCURACY_PCT,
    )

    return AnalyticsResponse(kpis=kpis, skills=top_skills)
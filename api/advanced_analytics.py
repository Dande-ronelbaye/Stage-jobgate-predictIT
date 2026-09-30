"""
advanced_analytics.py - PredictIT

Trois analyses construites sur les compétences déjà extraites et le nettoyage
robuste des dates :

1. Tendances : quelles compétences progressent / déclinent dans le temps
2. Paires de technos : quelles compétences apparaissent souvent ensemble (lift)
3. Gap analysis : recommandations personnalisées pour maximiser la couverture d'offres

Usage en ligne de commande :
    python advanced_analytics.py offres.jsonl
    python advanced_analytics.py offres.jsonl Python,SQL,Django
"""

import sys
import re
from collections import Counter, defaultdict
from itertools import combinations
from typing import Dict, List, Optional, Set

import pandas as pd
from analytics import extract_skills, load_jsonl


# ---------------------------------------------------------------------------
# 🧹 NETTOYAGE ROBUSTE DE LA DATE
# ---------------------------------------------------------------------------
def parse_month(date_raw: Optional[str]) -> Optional[str]:
    """
    Convertit n'importe quelle chaîne de date (ISO, dates textuelles du scraping)
    en 'YYYY-MM' propre via pandas.to_datetime, ou retourne None si invalide.
    """
    if not date_raw or not isinstance(date_raw, str):
        return None

    # Élimine les résidus de scraping textuel évidents (ex: "Juin, 2")
    if re.search(r'[a-zA-zA-Z]', date_raw) and not any(m in date_raw.lower() for m in
                                                       ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep',
                                                        'oct', 'nov', 'dec']):
        return None

    try:
        dt = pd.to_datetime(date_raw, errors='coerce')
        if pd.isna(dt):
            return None
        return dt.strftime('%Y-%m')
    except Exception:
        return None


def get_offer_skills(offer: dict) -> Set[str]:
    """
    Extrait les compétences de l'offre depuis 'techs_principales' si disponible,
    sinon retombe sur 'description' via extract_skills().
    """
    techs_raw = offer.get("techs_principales")
    if techs_raw and isinstance(techs_raw, str) and techs_raw != "Aucune techno détectée":
        # Nettoyage des crochets/guillemets si sous forme de chaîne JSON
        cleaned = re.sub(r"[\[\]'\"`]", "", techs_raw)
        skills = {t.strip() for t in cleaned.split(",") if t.strip() and len(t.strip()) > 1}
        if skills:
            return skills

    # Fallback sur la description
    desc = offer.get("description") or ""
    return extract_skills(desc) if desc else set()


# ---------------------------------------------------------------------------
# 1. Tendances : émergence / déclin
# ---------------------------------------------------------------------------
def compute_skill_trends(offers: List[dict], recent_months: int = 3) -> dict:
    """
    Compare la fréquence moyenne mensuelle de chaque compétence sur les
    `recent_months` derniers mois vs les `recent_months` mois précédents.
    """
    monthly_counts: Dict[str, Counter] = defaultdict(Counter)
    all_months = set()

    for offer in offers:
        # Essai de récupération de la date sur plusieurs clés possibles
        date_val = offer.get("published_date_raw") or offer.get("date") or offer.get("created_at")
        month = parse_month(date_val)
        if not month:
            continue

        skills = get_offer_skills(offer)
        for skill in skills:
            monthly_counts[month][skill] += 1
        all_months.add(month)

    sorted_months = sorted(all_months)
    if len(sorted_months) < recent_months * 2:
        return {
            "warning": (
                f"Pas assez de mois valides distincts ({len(sorted_months)}) pour comparer "
                f"{recent_months} mois récents vs {recent_months} mois précédents. "
                f"Dates détectées : {sorted_months}"
            ),
            "rising": [],
            "declining": [],
        }

    recent = sorted_months[-recent_months:]
    previous = sorted_months[-2 * recent_months:-recent_months]

    recent_totals, previous_totals = Counter(), Counter()
    for month in recent:
        recent_totals.update(monthly_counts[month])
    for month in previous:
        previous_totals.update(monthly_counts[month])

    trends = []
    for skill in set(recent_totals) | set(previous_totals):
        recent_avg = recent_totals[skill] / len(recent)
        previous_avg = previous_totals[skill] / len(previous)

        if previous_avg == 0:
            growth_pct = None  # Nouvelle compétence
        else:
            growth_pct = round(((recent_avg - previous_avg) / previous_avg) * 100, 1)

        trends.append({
            "skill": skill,
            "recent_avg_per_month": round(recent_avg, 1),
            "previous_avg_per_month": round(previous_avg, 1),
            "growth_pct": growth_pct,
            "is_new": previous_avg == 0 and recent_avg > 0,
        })

    # Filtre le bruit : au moins 1 mention mensuelle combinée
    trends = [t for t in trends if (t["recent_avg_per_month"] + t["previous_avg_per_month"]) >= 1]

    rising = sorted(
        [t for t in trends if t["growth_pct"] is None or t["growth_pct"] > 0],
        key=lambda t: (t["growth_pct"] is None, t["growth_pct"] or 0),
        reverse=True,
    )
    declining = sorted(
        [t for t in trends if t["growth_pct"] is not None and t["growth_pct"] < 0],
        key=lambda t: t["growth_pct"],
    )

    return {
        "recent_period": recent,
        "previous_period": previous,
        "rising": rising[:10],
        "declining": declining[:10],
    }


# ---------------------------------------------------------------------------
# 2. Paires de compétences les plus associées
# ---------------------------------------------------------------------------
def compute_skill_pairs(offers: List[dict], min_pair_count: int = 3, top_n: int = 15) -> List[dict]:
    """
    Calcul du score de 'lift' entre paires de technos.
    lift > 1.0 : vraie association d'architecture (ex: Swift+iOS).
    """
    pair_counts = Counter()
    skill_counts = Counter()
    total_offers = 0

    for offer in offers:
        skills = get_offer_skills(offer)
        if not skills:
            continue
        total_offers += 1
        skill_counts.update(skills)
        for pair in combinations(sorted(skills), 2):
            pair_counts[pair] += 1

    if total_offers == 0:
        return []

    results = []
    for (skill_a, skill_b), count in pair_counts.items():
        if count < min_pair_count:
            continue
        p_a = skill_counts[skill_a] / total_offers
        p_b = skill_counts[skill_b] / total_offers
        p_ab = count / total_offers
        lift = round(p_ab / (p_a * p_b), 2) if (p_a * p_b) > 0 else 0

        results.append({
            "skill_a": skill_a,
            "skill_b": skill_b,
            "co_occurrence_count": count,
            "pct_of_offers": round(p_ab * 100, 1),
            "lift": lift,
        })

    results.sort(key=lambda r: (r["lift"], r["co_occurrence_count"]), reverse=True)
    return results[:top_n]


# ---------------------------------------------------------------------------
# 3. Gap analysis
# ---------------------------------------------------------------------------
def compute_skill_gap(
        known_skills: List[str],
        offers: List[dict],
        category_filter: Optional[List[str]] = None,
        qualify_threshold: float = 0.8,
) -> dict:
    """
    Calcule la couverture des offres par rapport aux technos maîtrisées
    et évalue l'impact marginal de chaque compétence manquante.
    """
    known_set = {s.strip().lower() for s in known_skills if s.strip()}

    if category_filter:
        offers = [
            o for o in offers
            if o.get("predicted_category") in category_filter
               or o.get("category") in category_filter
               or o.get("mapped_category") in category_filter
        ]

    offer_requirements = []
    for o in offers:
        skills = get_offer_skills(o)
        if skills:
            offer_requirements.append({s.lower() for s in skills})

    total = len(offer_requirements)
    if total == 0:
        return {"error": "Aucune offre avec compétences détectées pour ce filtre."}

    def qualifies(skills_known: set, required: set) -> bool:
        if not required:
            return True
        return len(required & skills_known) / len(required) >= qualify_threshold

    currently_qualifying = sum(1 for req in offer_requirements if qualifies(known_set, req))
    current_pct = round(currently_qualifying / total * 100, 1)

    missing_counter = Counter()
    for req in offer_requirements:
        if not qualifies(known_set, req):
            missing_counter.update(req - known_set)

    marginal_impact = []
    for skill_lower, mention_count in missing_counter.most_common(15):
        simulated_known = known_set | {skill_lower}
        simulated_qualifying = sum(1 for req in offer_requirements if qualifies(simulated_known, req))
        marginal_impact.append({
            "skill": skill_lower.capitalize(),
            "offers_mentioning_as_missing": mention_count,
            "additional_offers_unlocked": simulated_qualifying - currently_qualifying,
            "new_qualifying_pct": round(simulated_qualifying / total * 100, 1),
        })

    marginal_impact.sort(key=lambda x: x["additional_offers_unlocked"], reverse=True)

    return {
        "total_offers_analyzed": total,
        "current_qualifying_pct": current_pct,
        "current_qualifying_count": currently_qualifying,
        "top_missing_skills": marginal_impact,
    }


# ---------------------------------------------------------------------------
# CLI de test
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python advanced_analytics.py <offres.jsonl> [skill1,skill2,...]")
        sys.exit(1)

    offers = load_jsonl(sys.argv[1])
    print(f"{len(offers)} offres chargées\n")

    print("=" * 60)
    print("TENDANCES (émergence / déclin)")
    print("=" * 60)
    trends = compute_skill_trends(offers)
    if "warning" in trends and trends["warning"]:
        print(f"⚠️ {trends['warning']}")
    else:
        print(f"Période récente : {trends['recent_period']}")
        print(f"Période précédente : {trends['previous_period']}\n")
        print("En hausse :")
        for t in trends["rising"][:5]:
            growth = "nouvelle" if t["is_new"] else f"{t['growth_pct']:+.1f}%"
            print(f"  {t['skill']}: {growth}")
        print("\nEn baisse :")
        for t in trends["declining"][:5]:
            print(f"  {t['skill']}: {t['growth_pct']:+.1f}%")

    print("\n" + "=" * 60)
    print("PAIRES DE TECHNOS")
    print("=" * 60)
    for p in compute_skill_pairs(offers, min_pair_count=2)[:10]:
        print(f"  {p['skill_a']} + {p['skill_b']}: {p['co_occurrence_count']} offres (lift={p['lift']})")

    if len(sys.argv) >= 3:
        known = sys.argv[2].split(",")
        print("\n" + "=" * 60)
        print(f"GAP ANALYSIS pour profil : {known}")
        print("=" * 60)
        gap = compute_skill_gap(known, offers)
        if "error" in gap:
            print(f"❌ {gap['error']}")
        else:
            print(f"Qualifie actuellement pour {gap['current_qualifying_pct']}% des offres "
                  f"({gap['current_qualifying_count']}/{gap['total_offers_analyzed']})\n")
            print("Compétences à apprendre en priorité :")
            for m in gap["top_missing_skills"][:5]:
                print(f"  {m['skill']}: débloquerait {m['additional_offers_unlocked']} offres "
                      f"supplémentaires (-> {m['new_qualifying_pct']}% au total)")


if __name__ == "__main__":
    main()
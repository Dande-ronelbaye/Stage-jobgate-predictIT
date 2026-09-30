"""
Détection de doublons entre les sources Keejob et tunisietravail - PredictIT

Ne supprime rien automatiquement. Génère un rapport des paires suspectes
(score de similarité titre + entreprise) pour validation manuelle avant
de décider quoi garder.

Usage :
    python dedupe_sources.py keejob_output.jsonl tunisietravail_output.jsonl

Sortie :
    - duplicate_report.csv : toutes les paires suspectes avec leur score
    - deduped_preview.jsonl : aperçu du dataset fusionné si tu appliques
      le seuil par défaut (à ajuster après avoir regardé le rapport)
"""

import json
import re
import sys
import unicodedata
import csv
from difflib import SequenceMatcher
from collections import defaultdict

# Seuils de matching -- à ajuster après avoir regardé duplicate_report.csv
COMPANY_THRESHOLD = 0.60
TITLE_THRESHOLD = 0.50

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


def strip_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def normalize(text, noise_words=None):
    if not text:
        return ""
    text = strip_accents(text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    if noise_words:
        words = [w for w in words if w not in noise_words]
    return " ".join(words)


def normalize_company(name):
    return normalize(name, noise_words=LEGAL_SUFFIXES)


def normalize_title(title):
    return normalize(title, noise_words=NOISE_TITLE_WORDS)


def similarity(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def get_company(item):
    # Gère les variations de nom de champ possibles selon la source
    for key in ("company", "company_name", "entreprise"):
        if item.get(key):
            return item[key]
    return ""


def get_title(item):
    for key in ("title", "titre"):
        if item.get(key):
            return item[key]
    return ""


def main():
    if len(sys.argv) != 3:
        print("Usage: python dedupe_sources.py <keejob.jsonl> <tunisietravail.jsonl>")
        sys.exit(1)

    keejob_path, tunisietravail_path = sys.argv[1], sys.argv[2]

    keejob_items = load_jsonl(keejob_path)
    tt_items = load_jsonl(tunisietravail_path)

    print(f"Keejob : {len(keejob_items)} offres")
    print(f"tunisietravail : {len(tt_items)} offres")

    # Pré-calcul des versions normalisées
    for item in keejob_items:
        item["_norm_company"] = normalize_company(get_company(item))
        item["_norm_title"] = normalize_title(get_title(item))

    for item in tt_items:
        item["_norm_company"] = normalize_company(get_company(item))
        item["_norm_title"] = normalize_title(get_title(item))

    # Blocage : regrouper tunisietravail par première lettre du nom
    # d'entreprise normalisé pour réduire le nombre de comparaisons
    tt_by_letter = defaultdict(list)
    for item in tt_items:
        key = item["_norm_company"][:1] if item["_norm_company"] else "?"
        tt_by_letter[key].append(item)

    matches = []
    for kj_item in keejob_items:
        kj_company = kj_item["_norm_company"]
        kj_title = kj_item["_norm_title"]
        candidate_letter = kj_company[:1] if kj_company else "?"

        # Compare uniquement contre les offres tunisietravail dont
        # l'entreprise commence par la même lettre (ou "?" si vide)
        candidates = tt_by_letter.get(candidate_letter, [])

        for tt_item in candidates:
            company_sim = similarity(kj_company, tt_item["_norm_company"])
            if company_sim < COMPANY_THRESHOLD:
                continue
            title_sim = similarity(kj_title, tt_item["_norm_title"])
            if title_sim < TITLE_THRESHOLD:
                continue

            matches.append({
                "keejob_title": get_title(kj_item),
                "keejob_company": get_company(kj_item),
                "keejob_url": kj_item.get("url", ""),
                "tunisietravail_title": get_title(tt_item),
                "tunisietravail_company": get_company(tt_item),
                "tunisietravail_url": tt_item.get("url", ""),
                "company_similarity": round(company_sim, 3),
                "title_similarity": round(title_sim, 3),
            })

    print(f"\n{len(matches)} paires suspectes détectées")
    print(f"(seuils actuels : entreprise >= {COMPANY_THRESHOLD}, titre >= {TITLE_THRESHOLD})")

    # Rapport CSV pour validation manuelle
    report_path = "duplicate_report.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        if matches:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)
    print(f"Rapport écrit : {report_path}")

    # Aperçu du dataset dédupliqué (garde tunisietravail en cas de doublon
    # car descriptions plus complètes ; à ajuster selon ce que tu observes
    # dans le rapport)
    duplicate_keejob_urls = {m["keejob_url"] for m in matches}
    deduped = [
        item for item in keejob_items
        if item.get("url") not in duplicate_keejob_urls
    ] + tt_items

    # Nettoyage des champs temporaires avant export
    for item in deduped:
        item.pop("_norm_company", None)
        item.pop("_norm_title", None)

    preview_path = "deduped_preview.jsonl"
    with open(preview_path, "w", encoding="utf-8") as f:
        for item in deduped:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Aperçu dédupliqué écrit : {preview_path} ({len(deduped)} offres)")
    print("\nIMPORTANT : relis duplicate_report.csv avant de considérer")
    print("deduped_preview.jsonl comme définitif -- ajuste les seuils en")
    print("haut du script si tu vois trop de faux positifs/négatifs.")


if __name__ == "__main__":
    main()
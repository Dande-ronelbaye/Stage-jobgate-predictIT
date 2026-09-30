"""
Application du classifieur entraîné (train_category_classifier.py) aux
sources Keejob et Jungle, qui n'ont pas la granularité de catégorie de
tunisietravail -- objectif : une catégorie unifiée sur les 3 sources.

Usage :
    python classify_offers.py category_classifier.joblib keejob_output.jsonl
    python classify_offers.py category_classifier.joblib jungle_output.jsonl

Écrit un nouveau fichier <nom>_classified.jsonl avec un champ
`predicted_category` ajouté (le champ `category` original, s'il existe,
n'est pas touché -- utile pour comparer les deux si tu veux valider la
qualité des prédictions).
"""

import json
import sys

import joblib


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def build_text_feature(item):
    # Doit être IDENTIQUE à build_text_feature() dans train_category_classifier.py
    # sinon le modèle reçoit des features dans un format différent de celui
    # sur lequel il a été entraîné.
    title = item.get("title") or ""
    description = item.get("description") or ""
    return f"{title} {title} {description}"


def main():
    if len(sys.argv) != 3:
        print("Usage: python classify_offers.py <model.joblib> <input.jsonl>")
        sys.exit(1)

    model_path, input_path = sys.argv[1], sys.argv[2]

    pipeline = joblib.load(model_path)
    items = load_jsonl(input_path)
    print(f"{len(items)} offres chargées depuis {input_path}")

    texts = [build_text_feature(i) for i in items]
    predictions = pipeline.predict(texts)

    # Probabilité de la classe prédite -- utile pour repérer les
    # prédictions peu fiables (ex: description trop courte ou ambiguë)
    probabilities = pipeline.predict_proba(texts)
    confidence_scores = probabilities.max(axis=1)

    low_confidence_count = 0
    for item, predicted_cat, confidence in zip(items, predictions, confidence_scores):
        item["predicted_category"] = predicted_cat
        item["prediction_confidence"] = round(float(confidence), 3)
        if confidence < 0.5:
            low_confidence_count += 1

    output_path = input_path.replace(".jsonl", "_classified.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Fichier écrit : {output_path}")
    print(f"Prédictions à faible confiance (< 0.5) : {low_confidence_count}/{len(items)}")
    print("(à inspecter manuellement -- souvent des descriptions trop "
          "courtes ou des postes à cheval sur plusieurs catégories)")


if __name__ == "__main__":
    main()
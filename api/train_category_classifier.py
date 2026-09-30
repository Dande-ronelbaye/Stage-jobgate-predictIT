"""
Entraînement d'un classifieur de catégorie de poste IT - PredictIT

Utilise tunisietravail comme source d'entraînement : son champ `category`
(breadcrumb du site) sert de label initial, nettoyé et mappé vers des
catégories métiers maîtres structurées.

Usage :
    python train_category_classifier.py ../scraper/tunisietravail_output.jsonl
"""

import json
import sys
from collections import Counter

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

MODEL_OUTPUT_PATH = "category_classifier.joblib"

# Mots-clés géographiques à supprimer des catégories
GEO_KEYWORDS = {
    'ariana', 'ben arous', 'tunis', 'bizerte', 'sousse', 'sfax', 'nabeul',
    'monastir', 'kairouan', 'gafsa', 'gabes', 'béja', 'jendouba', 'kasserine',
    'kef', 'mahdia', 'médenine', 'siliana', 'tataouine', 'tozeur', 'zaghouan',
    'france', 'canada', 'allemagne', 'bénin', 'australie', 'remote'
}


def clean_and_map_category(raw_cat: str) -> str:
    """
    1. Élimine les catégories qui sont en réalité des lieux géographiques.
    2. Regroupe les fiches de poste en 5 grandes catégories maîtres.
    """
    if not isinstance(raw_cat, str) or not raw_cat.strip():
        return None

    cat_lower = raw_cat.strip().lower()

    # 1. Élimination du bruit géographique
    if cat_lower in GEO_KEYWORDS:
        return None

    # 2. Mapping vers les 5 catégories maîtres IT

    # --- A. MOBILE ---
    if any(k in cat_lower for k in ['ios', 'android', 'swift', 'kotlin', 'mobile', 'flutter']):
        return 'Mobile Development'

    # --- B. DATA & DB ---
    if any(k in cat_lower for k in ['base de donnée', 'database', 'sql', 'data', 'bi', 'analytics', 'dba']):
        return 'Data & DB'

    # --- C. INFRASTRUCTURE & SYSADMIN / NETWORK ---
    if any(k in cat_lower for k in ['réseaux', 'réseau', 'système', 'systeme', 'devops', 'cloud', 'sécurité', 'linux', 'infra', 'administrateur']):
        return 'Infrastructure & Networks'

    # --- D. SOFTWARE ENGINEERING (Web, Backend, Frontend, Desktop) ---
    if any(k in cat_lower for k in ['développeur', 'developpeur', '.net', 'java', 'web', 'php', 'fullstack', 'frontend', 'backend', 'c#', 'python', 'it', 'conseillers / consultants']):
        return 'Software Engineering'

    # --- E. AUTRE / DIGITAL / MANAGEMENT ---
    return 'Digital, Design & Support'


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def build_text_feature(item):
    """Combine titre + description en un seul texte pour le TF-IDF.
    Le titre est répété 3 fois pour maximiser son poids dans la classification."""
    title = item.get("title") or ""
    description = item.get("description") or ""
    return f"{title} {title} {title} {description}"


def main():
    if len(sys.argv) != 2:
        print("Usage: python train_category_classifier.py <tunisietravail.jsonl>")
        sys.exit(1)

    data_path = sys.argv[1]
    items = load_jsonl(data_path)
    print(f"{len(items)} offres chargées depuis {data_path}")

    # Nettoyage et mapping des catégories
    cleaned_items = []
    for item in items:
        raw_cat = item.get("category")
        mapped_cat = clean_and_map_category(raw_cat)
        if mapped_cat:
            item["mapped_category"] = mapped_cat
            cleaned_items.append(item)

    print(f"{len(cleaned_items)} offres conservées après filtrage géographique et normalisation.")

    # Affichage de la nouvelle distribution
    category_counts = Counter(i["mapped_category"] for i in cleaned_items)
    print("\nDistribution des catégories maîtres :")
    for cat, count in category_counts.most_common():
        print(f"  {cat}: {count}")

    X = [build_text_feature(i) for i in cleaned_items]
    y = [i["mapped_category"] for i in cleaned_items]

    if len(set(y)) < 2:
        print("\nERREUR : Moins de 2 catégories distinctes après filtrage.")
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            C=1.5
        )),
    ])

    print(f"\nEntraînement sur {len(X_train)} offres, test sur {len(X_test)}...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'=' * 50}")
    print(f"PRÉCISION GLOBALE (accuracy) : {accuracy:.1%}")
    print(f"{'=' * 50}")
    print("\nRapport détaillé par catégorie :")
    print(classification_report(y_test, y_pred, zero_division=0))

    joblib.dump(pipeline, MODEL_OUTPUT_PATH)
    print(f"\nModèle sauvegardé : {MODEL_OUTPUT_PATH}")
    print("Réutilisable via : joblib.load('category_classifier.joblib')")


if __name__ == "__main__":
    main()
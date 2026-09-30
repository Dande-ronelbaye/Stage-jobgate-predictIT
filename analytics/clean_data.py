import os
import re
import pandas as pd

# 1. Définir le chemin vers ton fichier d'offres (généré par Scrapy)
jsonl_path = os.path.join("..", "scraper", "jungle_output.jsonl")

print("⏳ Chargement des données avec Pandas...")

try:
    # 2. Lire le fichier JSON Lines (.jsonl)
    df = pd.read_json(jsonl_path, lines=True)
    print(f"✅ Réussite ! {len(df)} offres d'emploi chargées.\n")

except FileNotFoundError:
    print(f"❌ Erreur : Le fichier {jsonl_path} n'a pas été trouvé.")
    print("Assure-toi d'avoir exporté tes données depuis Scrapy (ex: scrapy crawl welcome -o jungle_output.jsonl)")
    exit()

# 3. Découvrir tes données (Inspecter les premières lignes)
print("--- Aperçu des 3 premières offres ---")
print(df[['title', 'company', 'location']].head(3))
print("-" * 40 + "\n")

# 4. Calculer le salaire moyen et gérer les valeurs nulles
if 'salary_min' in df.columns and 'salary_max' in df.columns:
    df['salary_avg'] = (df['salary_min'] + df['salary_max']) / 2

    # Remplacer les valeurs manquantes (NaN) par la médiane des salaires trouvés
    salaire_median = df['salary_avg'].median()

    # Si le scraper n'a trouvé aucun salaire du tout, on met une valeur par défaut du marché
    if pd.isna(salaire_median):
        salaire_median = 44500.0

    df['salary_avg'] = df['salary_avg'].fillna(salaire_median)
    print(f"📊 Salaire moyen calculé (Valeur médiane appliquée : {salaire_median} EUR)\n")

TECH_DICTIONARY = {
    # Langages majeurs
    'python': r'\bpython\b',
    'java': r'\bjava\b(?!script)',  # Capture Java mais pas JavaScript
    'javascript': r'\bjavascript\b|js\b',
    'typescript': r'\btypescript\b|\bts\b',  # On ajoute \b au début de ts également !    'php': r'\bphp\b',
    'c#': r'c#|c-sharp',
    'c++': r'c\+\+',

    # Frameworks Front & Back
    'react': r'\breact\b|\breact\.js\b',
    'angular': r'\bangular\b',
    'vue': r'\bvue\.js\b|\bvuejs\b',
    'node.js': r'\bnode\.js\b|\bnodejs\b',
    '.net': r'\.net',
    'wpf': r'\bwpf\b',

    # Data & Cloud / DevOps
    'sql': r'\bsql\b|\bpostgresql\b|\bmysql\b',
    'cloud': r'\bcloud\b|\baws\b|\bazure\b|\bgcp\b',
    'docker': r'\bdocker\b',
    'kubernetes': r'\bkubernetes\b|\bk8s\b',
    'devops': r'\bdevops\b',

    # Systèmes d'entreprise & Industriels
    'sap': r'\bsap\b',
    'mainframe': r'\bmainframe\b|\bcobol\b',
    'scada': r'\bscada\b',
    'glpi': r'\bglpi\b'
}

def detecter_technos_avance(row):
    # On combine le résumé ET les missions pour maximiser les chances de détection
    resume = str(row.get('summary', ''))
    missions = str(row.get('key_missions', ''))
    texte_complet = f"{resume} {missions}".lower()

    techs_trouvees = []
    for tech, pattern in TECH_DICTIONARY.items():
        if re.search(pattern, texte_complet):
            techs_trouvees.append(tech)

    return ", ".join(techs_trouvees) if techs_trouvees else "Aucune techno détectée"


# On utilise .apply(..., axis=1) pour analyser plusieurs colonnes (ligne par ligne)
df['techs_principales'] = df.apply(detecter_technos_avance, axis=1)

# 6. Extraction propre de la Ville pour tes futurs graphiques
if 'location' in df.columns:
    df['ville'] = df['location'].apply(lambda x: x.split(',')[0].strip() if pd.notna(x) else "Inconnu")

# 7. Sauvegarder le résultat nettoyé
output_clean_path = "jobs_nettoyes.csv"
df.to_csv(output_clean_path, index=False, encoding='utf-8')
print(f"💾 Données enrichies et sauvegardées avec succès dans : {output_clean_path}")
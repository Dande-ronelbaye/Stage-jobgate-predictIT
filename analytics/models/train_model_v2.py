import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

print("🤖 --- ENTRAÎNEMENT DU MODÈLE PRÉDICTIF (v2) --- 🤖\n")


def split_technos(text):
    return [t.strip() for t in text.split(',')]


# Taux de change approximatifs vers EUR -- à ajuster si tu veux plus de
# précision (taux d'un jour donné), mais l'essentiel est de ne plus
# additionner des USD/GBP comme si c'était des EUR.
FX_TO_EUR = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
}


def extract_country(location: str) -> str:
    """`location` est au format 'Ville, Pays' (ex: 'Paris, France') --
    bien plus fiable que `ville` seule ou `source` (qui ne contenait
    qu'une seule valeur dans ce fichier) pour déterminer le marché."""
    if pd.isna(location) or "," not in str(location):
        return "inconnu"
    return str(location).split(",")[-1].strip()


def bucket_market(country: str) -> str:
    if country == "France":
        return "france"
    if country == "inconnu":
        return "inconnu"
    return "international"


# Charger les données
csv_path = os.path.join("..", "jobs_nettoyes.csv")
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Impossible de trouver {csv_path}.")

df = pd.read_csv(csv_path)

# 1. Filtrer pour ne garder QUE les offres avec un salaire réel connu
df_model = df[df['salary_avg'] != 44500.0].copy()
print(f"📊 Offres avec salaire réel avant nettoyage : {len(df_model)}")

# 2. CORRECTION BUG DEVISES : salary_avg mélange EUR/USD/GBP sans
# conversion (confirmé : 257 EUR, 49 USD, 7 GBP dans le fichier réel).
# On convertit tout vers EUR AVANT toute autre transformation.
df_model['salary_currency'] = df_model['salary_currency'].fillna('EUR')
n_non_eur = (df_model['salary_currency'] != 'EUR').sum()
df_model['salary_avg'] = df_model.apply(
    lambda r: r['salary_avg'] * FX_TO_EUR.get(r['salary_currency'], 1.0), axis=1
)
print(f"💱 {n_non_eur} lignes converties vers EUR (USD/GBP détectées)")

# 3. CORRECTION BUG UNITÉS : les alternances/stages semblent être en
# mensuel (ex: Paris/apprenticeship/1450.0 -- impossible en annuel),
# contrairement aux CDI qui sont en annuel. On annualise.
MONTHLY_CONTRACT_TYPES = {"apprenticeship", "internship", "stage"}
mask_monthly = df_model["contract_type"].isin(MONTHLY_CONTRACT_TYPES)
n_converted = mask_monthly.sum()
df_model.loc[mask_monthly, "salary_avg"] = df_model.loc[mask_monthly, "salary_avg"] * 12
print(f"🔧 {n_converted} lignes converties de mensuel à annuel (contract_type dans {MONTHLY_CONTRACT_TYPES})")

# Garde-fou supplémentaire : un salaire annuel réaliste est entre 3 000 et
# 300 000 -- au-delà, c'est probablement encore une erreur d'unité ou une
# valeur aberrante. On les retire plutôt que de les convertir à l'aveugle.
before = len(df_model)
df_model = df_model[(df_model["salary_avg"] >= 3000) & (df_model["salary_avg"] <= 300000)]
print(f"🧹 {before - len(df_model)} lignes retirées comme aberrantes (hors [3000, 300000] € annuel)")
print(f"📊 Offres restantes pour l'entraînement : {len(df_model)}")

# 4. Marché dérivé de `location` ('Ville, Pays'), plus fiable que `source`
# (qui ne contenait qu'une seule valeur : 'welcometothejungle' partout
# dans ce fichier -- donc inexploitable comme signal de marché).
df_model["country"] = df_model["location"].apply(extract_country)
df_model["market"] = df_model["country"].apply(bucket_market)
print("\n📍 Répartition par marché (dérivé de `location`) :")
print(df_model["market"].value_counts())
print("\n📍 Détail des pays (top 10) :")
print(df_model["country"].value_counts().head(10))

# 4. Remplir les valeurs manquantes
df_model['contract_type'] = df_model['contract_type'].fillna('full_time')
df_model['techs_principales'] = df_model['techs_principales'].fillna('Aucune techno détectée')
df_model['experience_level_minimum'] = df_model['experience_level_minimum'].fillna('non_precise')

# CORRECTION BUG TYPE MÉLANGÉ : fillna() ne remplace que les valeurs
# manquantes -- si une colonne contient déjà un mélange de nombres (ex:
# années d'expérience en float) et de texte, OneHotEncoder plante avec
# "Got ['float', 'str']". On force le type string partout pour l'éviter,
# quelle que soit la colonne réellement en cause.
for col in ['market', 'contract_type', 'experience_level_minimum']:
    df_model[col] = df_model[col].astype(str)

# 5. Features (X) et cible (y) -- market (dérivé de source, fiable) +
# experience_level_minimum (colonne disponible mais inutilisée avant)
X = df_model[['market', 'contract_type', 'experience_level_minimum', 'techs_principales']]
y = df_model['salary_avg']

if len(df_model) < 30:
    print("\n⚠️  ATTENTION : moins de 30 exemples après nettoyage. Le modèle "
          "risque de rester peu fiable quel que soit le réglage -- le vrai "
          "problème de fond est le VOLUME de données avec salaire connu, "
          "pas seulement la qualité du nettoyage.")

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['market', 'contract_type', 'experience_level_minimum']),
        ('tech', CountVectorizer(tokenizer=split_technos, token_pattern=None, lowercase=True), 'techs_principales')
    ]
)

model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42)),
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("\n⏳ Entraînement du Random Forest en cours...")
model_pipeline.fit(X_train, y_train)
print("✅ Modèle entraîné avec succès !")

y_pred = model_pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n📈 PERFORMANCE DU MODÈLE (v2) :")
print(f"• Erreur Moyenne Absolue (MAE) : {mae:.2f} €")
print(f"• Score R² (Coefficient de détermination) : {r2:.4f}")
print("\n(Compare ces chiffres à la version précédente : MAE=20380.20€, R²=0.5532)")

model_version_path = "salary_predictor_v2.pkl"
joblib.dump(model_pipeline, model_version_path)
print(f"\n💾 Modèle sauvegardé dans : analytics/models/{model_version_path}")
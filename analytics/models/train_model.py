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

print("🤖 --- ENTRAÎNEMENT DU MODÈLE PRÉDICTIF --- 🤖\n")

# 1. Déclarer une vraie fonction au lieu d'une lambda pour éviter le crash au pickling
def split_technos(text):
    return [t.strip() for t in text.split(',')]

# Charger les données (On remonte d'un niveau pour trouver le CSV dans analytics)
csv_path = os.path.join("..", "jobs_nettoyes.csv")
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Impossible de trouver {csv_path}. Assure-toi d'être dans le dossier analytics/models pour lancer le script.")

df = pd.read_csv(csv_path)

# 2. Filtrer pour ne garder QUE les offres avec un salaire réel connu
df_model = df[df['salary_avg'] != 44500.0].copy()

print(f"📊 Nombre d'offres avec salaires réels pour l'entraînement : {len(df_model)}")

# Remplir les valeurs manquantes textuelles par sécurité
df_model['ville'] = df_model['ville'].fillna('Inconnu')
df_model['contract_type'] = df_model['contract_type'].fillna('full_time')
df_model['techs_principales'] = df_model['techs_principales'].fillna('Aucune techno détectée')

# 3. Définir les Features (X) et la Cible (y)
X = df_model[['ville', 'contract_type', 'techs_principales']]
y = df_model['salary_avg']

# 4. Construire le Préprocesseur (avec la fonction nommée split_technos)
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['ville', 'contract_type']),
        ('tech', CountVectorizer(tokenizer=split_technos, token_pattern=None, lowercase=True), 'techs_principales')
    ]
)

# 5. Créer le Pipeline global
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# 6. Séparer en données d'entraînement (80%) et de test (20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 7. Entraîner le modèle
print("⏳ Entraînement du Random Forest en cours...")
model_pipeline.fit(X_train, y_train)
print("✅ Modèle entraîné avec succès !")

# 8. Évaluation des performances
y_pred = model_pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n📈 PERFORMANCE DU MODÈLE :")
print(f"• Erreur Moyenne Absolue (MAE) : {mae:.2f} €")
print(f"• Score R² (Coefficient de détermination) : {r2:.4f}")

# 9. Sauvegarder le modèle entraîné au même endroit
model_version_path = "salary_predictor_v1.pkl"
joblib.dump(model_pipeline, model_version_path)
print(f"\n💾 Modèle sérialisé et sauvegardé avec succès dans : analytics/models/{model_version_path}")
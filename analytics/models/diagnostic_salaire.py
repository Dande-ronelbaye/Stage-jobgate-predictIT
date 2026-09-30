"""
Diagnostic rapide sur jobs_nettoyes.csv -- à lancer depuis le même dossier
que ton script d'entraînement (analytics/models), puisqu'il utilise le
même chemin relatif vers le CSV.

Usage :
    python diagnostic_salaire.py
"""

import os
import pandas as pd

csv_path = os.path.join("..", "jobs_nettoyes.csv")
if not os.path.exists(csv_path):
    raise FileNotFoundError(
        f"Impossible de trouver {csv_path}. Assure-toi de lancer ce script "
        f"depuis le dossier analytics/models, comme pour le script d'entraînement."
    )

df = pd.read_csv(csv_path)

print("=" * 60)
print("COLONNES DISPONIBLES DANS LE CSV BRUT")
print("=" * 60)
print(df.columns.tolist())

print("\n" + "=" * 60)
print("RÉPARTITION DES SALAIRES PAR VILLE (offres avec salaire réel)")
print("=" * 60)
df_model = df[df["salary_avg"] != 44500.0].copy()
print(f"\n{len(df_model)} offres avec salaire réel sur {len(df)} au total\n")
print(df_model.groupby("ville")["salary_avg"].agg(["count", "mean", "min", "max"]))

print("\n" + "=" * 60)
print("APERÇU DE QUELQUES LIGNES BRUTES (pour repérer un souci d'unité)")
print("=" * 60)
cols_to_show = [c for c in ["ville", "contract_type", "salary_avg", "market"] if c in df_model.columns]
print(df_model[cols_to_show].sample(min(10, len(df_model)), random_state=42))
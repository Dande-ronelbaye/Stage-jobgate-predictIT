import pandas as pd

# 1. Charger le fichier fraîchement nettoyé
try:
    df = pd.read_csv("jobs_nettoyes.csv")
    print(f"📊 Fichier chargé avec succès ! Analyse de {len(df)} offres.\n")
except FileNotFoundError:
    print("❌ Fichier jobs_nettoyes.csv introuvable. Lance d'abord clean_data.py !")
    exit()

print("=" * 50)
print("🔍 EXAMEN DE LA RICHESSE DE TON DATA PIPELINE")
print("=" * 50)

# --- Métrique 1 : Le taux de complétion des vrais salaires ---
# Combien d'offres affichaient un vrai salaire avant qu'on applique la médiane ?
if 'salary_min' in df.columns:
    offres_avec_salaire = df['salary_min'].notna().sum()
    pourcentage_salaire = (offres_avec_salaire / len(df)) * 100
    print(f"💰 Qualité des salaires : {offres_avec_salaire} / {len(df)} offres proposaient un salaire transparent ({pourcentage_salaire:.1f}%).")
    print(f"   ↳ Moyenne des salaires (médiane incluse) : {round(df['salary_avg'].mean(), 2)} €")

# --- Métrique 2 : Top 5 des Villes qui recrutent ---
print("\n📍 TOP 5 DES VILLES LES PLUS ACTIVES :")
if 'ville' in df.columns:
    print(df['ville'].value_counts().head(5))
else:
    print(df['location'].value_counts().head(5))

# --- Métrique 3 : Analyse des Technologies ---
print("\n💻 PÉNÉTRATION DES TECHNOLOGIES DANS TES OFFRES :")
# On sépare les technos car une offre peut en avoir plusieurs (ex: "c#, cloud")
toutes_les_technos = []
offres_sans_techno = 0

for liste_tech in df['techs_principales'].dropna():
    if liste_tech == "Aucune techno détectée":
        offres_sans_techno += 1
    else:
        # On découpe s'il y a des virgules et on nettoie les espaces
        technos = [t.strip() for t in liste_tech.split(",")]
        toutes_les_technos.extend(technos)

# Conversion en Série Pandas pour compter facilement
serie_technos = pd.Series(toutes_les_technos)
total_technos_trouvees = len(toutes_les_technos)

print(f"   ↳ Nombre total de mots-clés technos interceptés : {total_technos_trouvees}")
print(f"   ↳ Offres sans techno détectée (profils managériaux/génériques) : {offres_sans_techno}")
print("\n🔥 Classement des technos les plus demandées :")
print(serie_technos.value_counts())

# --- Métrique 4 : Répartition des types de contrats ---
print("\n📜 RÉPARTITION DES CONTRATS :")
if 'contract_type' in df.columns:
    print(df['contract_type'].value_counts())

print("\n" + "=" * 50)
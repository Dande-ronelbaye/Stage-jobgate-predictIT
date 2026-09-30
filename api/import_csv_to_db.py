import os
import pandas as pd
from database import init_db, SessionLocal, JobModel


def migrate_data():
    print("⏳ Initialisation de la base de données PostgreSQL...")
    init_db()  # Crée la table 'jobs' automatiquement si elle n'existe pas encore

    # Chemin vers le fichier CSV nettoyé (situé dans analytics/)
    csv_path = os.path.join("..", "analytics", "jobs_nettoyes.csv")
    if not os.path.exists(csv_path):
        print(f"❌ Impossible de trouver le fichier CSV à l'emplacement : {csv_path}")
        return

    print("📖 Lecture du fichier CSV...")
    df = pd.read_csv(csv_path)

    # Remplacer les valeurs NaN (Not a Number) par None pour que SQL comprenne 'NULL'
    df = df.where(pd.notnull(df), None)

    db = SessionLocal()
    try:
        # Nettoyage de sécurité : évite les doublons si tu lances le script plusieurs fois
        db.query(JobModel).delete()

        print(f"🚀 Insertion de {len(df)} lignes dans PostgreSQL...")
        for _, row in df.iterrows():
            job = JobModel(
                title=row.get('title'),
                company=row.get('company'),
                ville=row.get('ville', 'Inconnu'),
                contract_type=row.get('contract_type', 'full_time'),
                salary_avg=row.get('salary_avg'),
                techs_principales=row.get('techs_principales', 'Aucune techno détectée')
            )
            db.add(job)

        db.commit()
        print("✅ Migration terminée avec succès ! Les données sont maintenant dans PostgreSQL.")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la migration : {e}")
    finally:
        db.close()


if __name__ == "__main__":
    migrate_data()
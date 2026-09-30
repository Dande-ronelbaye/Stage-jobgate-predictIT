import json
import os
from database import init_db, SessionLocal, JobModel


def extract_techs(title):
    """Extraction de secours à partir du titre si les techs ne sont pas fournies."""
    if not title:
        return "Général IT"
    techs = [
        "React", "Node.js", "Java", "Python", "C#", ".NET", "PHP",
        "Symfony", "Laravel", "Flutter", "DevOps", "Angular", "Vue.js", "SQL"
    ]
    found = [t for t in techs if t.lower() in title.lower()]
    return ", ".join(found) if found else "Général IT"


def migrate_jsonl():
    print("⏳ Initialisation de la base de données PostgreSQL...")
    init_db()

    # Le script cherche le fichier JSONL situé dans le dossier scraper/
    jsonl_path = os.path.join("..", "scraper", "deduped_preview.jsonl")

    if not os.path.exists(jsonl_path):
        jsonl_path = "deduped_preview.jsonl"
        if not os.path.exists(jsonl_path):
            print(f"❌ Fichier introuvable : {jsonl_path}")
            return

    print(f"📖 Lecture du fichier : {jsonl_path}...")

    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    db = SessionLocal()
    try:
        print(f"🚀 Insertion de {len(records)} offres dans PostgreSQL...")

        added_count = 0
        for row in records:
            job = JobModel(
                title=row.get("title"),
                company=row.get("company") or "Non spécifié",
                ville=row.get("region") or row.get("ville") or "Inconnu",
                contract_type=row.get("contract_type", "full_time"),
                salary_avg=row.get("salary_avg"),
                techs_principales=row.get("techs_principales") or extract_techs(row.get("title"))
            )
            db.add(job)
            added_count += 1

            # Commit par tranches de 100
            if added_count % 100 == 0:
                db.commit()

        db.commit()
        print(f"✅ Migration réussie ! {added_count} offres insérées avec succès.")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de l'insertion : {e}")
    finally:
        db.close()


if __name__ == "__main__":
    migrate_jsonl()
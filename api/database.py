import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "postgresql://postgres:root@localhost:5432/predictit_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Définition de la table 'jobs' dans PostgreSQL
class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    ville = Column(String, index=True)
    contract_type = Column(String, index=True)
    salary_avg = Column(Float, nullable=True)
    techs_principales = Column(String, nullable=True)


# 2bis. Définition de la table 'users' (authentification)
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    history = relationship("AnalysisHistoryModel", back_populates="user", cascade="all, delete-orphan")


# 2ter. Définition de la table 'analysis_history' (historique des analyses par utilisateur)
class AnalysisHistoryModel(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Snapshot de la requête + des résultats au moment de l'analyse.
    # JSONB (Postgres) plutôt que plusieurs colonnes séparées : la forme
    # exacte de predictData/gapData peut évoluer, JSONB évite une migration
    # à chaque changement de forme de réponse.
    input_payload = Column(JSONB, nullable=False)
    predict_result = Column(JSONB, nullable=True)
    gap_result = Column(JSONB, nullable=True)

    user = relationship("UserModel", back_populates="history")


# 3. Fonction utilitaire pour initialiser (créer) les tables si elles n'existent pas
def init_db():
    Base.metadata.create_all(bind=engine)

# 4. Dépendance pour obtenir la session de BDD dans FastAPI plus tard
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
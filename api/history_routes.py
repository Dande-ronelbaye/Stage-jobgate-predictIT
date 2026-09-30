"""
Routes d'historique des analyses, réservées aux utilisateurs connectés.

À brancher dans main.py :
    from history_routes import history_router
    app.include_router(history_router)

Toutes les routes ici dépendent de get_current_user (auth_routes.py) —
si le cookie est absent/invalide, FastAPI renvoie automatiquement 401
avant même d'exécuter le corps de la fonction.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, AnalysisHistoryModel, UserModel
from auth_routes import get_current_user

history_router = APIRouter(prefix="/api/history", tags=["history"])


# ─── Schemas ────────────────────────────────────────────────────────────
class SaveAnalysisInput(BaseModel):
    input_payload: dict[str, Any]
    predict_result: Optional[dict[str, Any]] = None
    gap_result: Optional[dict[str, Any]] = None


class AnalysisHistoryOut(BaseModel):
    id: int
    created_at: str
    input_payload: dict[str, Any]
    predict_result: Optional[dict[str, Any]] = None
    gap_result: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


# ─── Routes ─────────────────────────────────────────────────────────────
@history_router.post("", response_model=AnalysisHistoryOut)
def save_analysis(
    payload: SaveAnalysisInput,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = AnalysisHistoryModel(
        user_id=current_user.id,
        input_payload=payload.input_payload,
        predict_result=payload.predict_result,
        gap_result=payload.gap_result,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "id": entry.id,
        "created_at": entry.created_at.isoformat(),
        "input_payload": entry.input_payload,
        "predict_result": entry.predict_result,
        "gap_result": entry.gap_result,
    }


@history_router.get("", response_model=list[AnalysisHistoryOut])
def list_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = (
        db.query(AnalysisHistoryModel)
        .filter(AnalysisHistoryModel.user_id == current_user.id)
        .order_by(AnalysisHistoryModel.created_at.desc())
        .all()
    )
    return [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat(),
            "input_payload": e.input_payload,
            "predict_result": e.predict_result,
            "gap_result": e.gap_result,
        }
        for e in entries
    ]


@history_router.delete("/{entry_id}")
def delete_history_entry(
    entry_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(AnalysisHistoryModel)
        .filter(
            AnalysisHistoryModel.id == entry_id,
            AnalysisHistoryModel.user_id == current_user.id,  # empêche de supprimer l'historique d'un autre user
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrée introuvable.")

    db.delete(entry)
    db.commit()
    return {"message": "Entrée supprimée."}
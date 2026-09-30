"""
Routes d'authentification : /api/auth/register, /login, /logout, /me

Dépendances requises (à installer) :
    pip install "python-jose[cryptography]"

À brancher dans main.py :
    from auth_routes import auth_router
    app.include_router(auth_router)

⚠️ SECRET_KEY : en dev, une valeur par défaut est utilisée pour que ça
tourne tout de suite. Avant tout déploiement réel, définis la variable
d'environnement JWT_SECRET_KEY avec une vraie valeur secrète (longue,
aléatoire) — sinon n'importe qui connaissant cette valeur par défaut
pourrait forger des tokens valides.

⚠️ CORS : ton main.py a actuellement
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"]
    allow_credentials=True
Le "*" combiné à allow_credentials=True est en pratique bloqué par les
navigateurs (un cookie ne peut pas être envoyé avec un origin wildcard).
Retire le "*" de la liste si les cookies ne semblent pas partir depuis
le frontend.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db, UserModel
from auth_utils import hash_password, verify_password

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"

SESSION_EXPIRE_MINUTES = 60 * 12       # 12h si "remember me" non coché
REMEMBER_ME_EXPIRE_MINUTES = 60 * 24 * 30  # 30 jours si coché

COOKIE_NAME = "access_token"

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


# ─── Schemas ────────────────────────────────────────────────────────────
class RegisterInput(BaseModel):
    email: EmailStr
    password: str


class LoginInput(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


# ─── JWT helpers ────────────────────────────────────────────────────────
def create_access_token(user_id: int, expires_minutes: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def set_auth_cookie(response: Response, token: str, remember_me: bool) -> None:
    max_age = (REMEMBER_ME_EXPIRE_MINUTES if remember_me else SESSION_EXPIRE_MINUTES) * 60
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # ⚠️ mettre à True en production (HTTPS uniquement)
        max_age=max_age,
        path="/",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserModel:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


# ─── Routes ─────────────────────────────────────────────────────────────
@auth_router.post("/register", response_model=UserOut)
def register(payload: RegisterInput, response: Response, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email.")

    user = UserModel(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Connexion automatique après inscription (session courte par défaut)
    token = create_access_token(user.id, SESSION_EXPIRE_MINUTES)
    set_auth_cookie(response, token, remember_me=False)

    return user


@auth_router.post("/login", response_model=UserOut)
def login(payload: LoginInput, response: Response, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()

    # Message volontairement identique pour email inconnu ou mot de passe
    # incorrect — ne pas révéler si l'email existe en base.
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    expires = REMEMBER_ME_EXPIRE_MINUTES if payload.remember_me else SESSION_EXPIRE_MINUTES
    token = create_access_token(user.id, expires)
    set_auth_cookie(response, token, remember_me=payload.remember_me)

    return user


@auth_router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"message": "Déconnecté."}


@auth_router.get("/me", response_model=UserOut)
def me(current_user: UserModel = Depends(get_current_user)):
    return current_user
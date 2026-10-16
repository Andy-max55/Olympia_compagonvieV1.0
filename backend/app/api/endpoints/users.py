"""Routes REST de gestion des utilisateurs."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def _to_schema(user: User) -> UserCreate:
    """Convertit un enregistrement ORM en schéma de réponse validé."""
    return UserCreate(
        id=UUID(str(user.id)),
        nom=str(user.nom),
        email=str(user.email),
        preferences=dict(user.preferences) if user.preferences is not None else {},
    )


@router.post(
    "/",
    response_model=UserCreate,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur",
)
def create_user(payload: UserCreate, db: DbSession) -> UserCreate:
    """Persiste un nouvel utilisateur après validation du payload."""
    user = User(
        id=str(payload.id),
        nom=payload.nom,
        email=str(payload.email),
        preferences=payload.preferences,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un utilisateur avec cet identifiant ou cet e-mail existe déjà.",
        ) from None
    db.refresh(user)
    return _to_schema(user)


@router.get(
    "/{user_id}",
    response_model=UserCreate,
    summary="Récupérer un utilisateur par identifiant",
)
def read_user(user_id: str, db: DbSession) -> UserCreate:
    """Retourne l'utilisateur demandé, ou une erreur 404 s'il est absent."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )
    return _to_schema(user)

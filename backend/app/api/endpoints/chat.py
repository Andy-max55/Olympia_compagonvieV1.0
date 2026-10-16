"""Routes REST du dialogue avec l'agent coach de vie."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.life_coach import AgentConfigurationError, LifeCoachAgent
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def _profile_from_user(user: User) -> dict[str, Any]:
    """Extrait le profil métier sans exposer d'identifiants internes superflus."""
    preferences: dict[str, Any]
    if isinstance(user.preferences, dict):
        preferences = dict(user.preferences)
    else:
        preferences = {}
    return {
        "id": str(user.id),
        "nom": str(user.nom),
        "preferences": preferences,
    }


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtenir un conseil de l'agent",
)
async def create_chat(payload: ChatRequest, db: DbSession) -> ChatResponse:
    """Charge le profil, interroge l'agent et renvoie le conseil généré."""
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    agent = LifeCoachAgent()
    try:
        advice: str = await agent.generate_advice(
            user_profile=_profile_from_user(user),
            user_message=payload.message,
        )
    except AgentConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de conseil n'est pas configuré (clé Google absente).",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Le compagnon n'a pas pu générer de conseil. Réessayez plus tard.",
        ) from None
    return ChatResponse(advice=advice)

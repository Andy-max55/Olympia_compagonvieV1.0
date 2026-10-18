"""Routes REST du dialogue avec l'agent coach de vie."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.life_coach import LifeCoachAgent
from app.agents.memory import extract_and_store_facts, format_patient_memory, get_user_memories
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
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtenir un conseil de l'agent",
)
async def create_chat(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> ChatResponse:
    """Charge le profil, interroge l'agent et renvoie le conseil généré."""
    try:
        user = db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur introuvable.",
            )

        current_user = "andy_admin"
        memory_context = format_patient_memory(get_user_memories(current_user))
        background_tasks.add_task(extract_and_store_facts, payload.message)

        agent = LifeCoachAgent()
        advice: str = await agent.generate_advice(
            user_profile=_profile_from_user(user),
            user_message=payload.message,
            memory_context=memory_context,
        )
        return ChatResponse(advice=advice)
    except HTTPException:
        raise
    except Exception as e:
        print(f"=== ERREUR CRITIQUE DANS LE CHAT : {str(e)} ===")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}") from e

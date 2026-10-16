"""Schémas de validation du fil de discussion avec l'agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    """Payload d'une demande de conseil."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: str = Field(..., min_length=1, description="Identifiant de l'utilisateur.")
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message adressé à l'agent.",
    )

    @field_validator("user_id", "message")
    @classmethod
    def _non_vide(cls, value: str) -> str:
        """Refuse les champs composés uniquement d'espaces."""
        if not value.strip():
            raise ValueError("Ce champ ne peut pas être vide.")
        return value


class ChatResponse(BaseModel):
    """Réponse de l'agent de coaching."""

    model_config = ConfigDict(extra="forbid")

    advice: str = Field(..., min_length=1, description="Conseil généré pour l'utilisateur.")

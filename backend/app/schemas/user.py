"""Schémas de validation liés à l'utilisateur."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Payload validé pour la création d'un utilisateur.

    Modèle strict : champs obligatoires, espaces superflus retirés,
    propriétés inconnues rejetées. Aucune valeur par défaut n'est
    fournie afin d'éviter des données implicites ou non maîtrisées.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=True,
    )

    id: UUID = Field(
        ...,
        description="Identifiant unique universel de l'utilisateur.",
    )
    nom: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom affiché de l'utilisateur.",
    )
    email: EmailStr = Field(
        ...,
        description="Adresse e-mail unique, normalisée et validée.",
    )
    preferences: dict[str, Any] = Field(
        ...,
        description="Préférences utilisateur fournies explicitement par le client.",
    )

    @field_validator("nom")
    @classmethod
    def _nom_non_vide(cls, value: str) -> str:
        """Rejette un nom composé uniquement d'espaces."""
        if not value.strip():
            raise ValueError("Le nom ne peut pas être vide.")
        return value

    @field_validator("preferences")
    @classmethod
    def _cles_preferences_non_vides(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Refuse les clés de préférences vides, qui masquent souvent une erreur de payload."""
        for key in value:
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Les clés de preferences doivent être des chaînes non vides.")
        return value

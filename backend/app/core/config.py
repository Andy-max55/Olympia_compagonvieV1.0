"""Chargement centralisé de la configuration applicative.

Les valeurs proviennent exclusivement de l'environnement (variables
système ou fichier ``.env``). Aucun secret ni origine CORS permissive
n'est figé dans le code source.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres d'exécution chargés depuis l'environnement.

    Les paramètres de sécurité (origines, mode debug, nom) sont
    obligatoires. ``GOOGLE_API_KEY`` est optionnelle : aucune clé
    n'est jamais figée dans le code.
    """

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = Field(
        ...,
        min_length=1,
        description="Nom public de l'application.",
    )
    DEBUG_MODE: bool = Field(
        ...,
        description=(
            "Active le mode diagnostic. Doit rester False hors environnement "
            "de développement contrôlé."
        ),
    )
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        ...,
        min_length=1,
        description="Origines CORS autorisées. Jamais de joker '*'.",
    )
    GOOGLE_API_KEY: str | None = Field(
        default=None,
        description="Clé API Google Gemini, fournie uniquement par l'environnement.",
    )

    @field_validator("GOOGLE_API_KEY", mode="before")
    @classmethod
    def _normalize_google_api_key(cls, value: object) -> object:
        """Traite une clé vide comme absente, sans valeur de repli."""
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("APP_NAME", mode="before")
    @classmethod
    def _strip_app_name(cls, value: object) -> object:
        """Normalise le nom d'application sans introduire de défaut."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, value: object) -> object:
        """Accepte une liste JSON ou une chaîne d'origines séparées par des virgules."""
        if isinstance(value, str):
            origins: list[str] = [
                origin.strip() for origin in value.split(",") if origin.strip()
            ]
            return origins
        return value

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def _reject_unsafe_origins(cls, origins: list[str]) -> list[str]:
        """Refuse les origines vides, le joker CORS et les schémas non HTTP(S)."""
        sanitized: list[str] = []
        for origin in origins:
            candidate: str = origin.strip()
            if not candidate:
                raise ValueError("Une origine CORS ne peut pas être vide.")
            if candidate == "*":
                raise ValueError(
                    "L'origine CORS '*' est interdite : elle expose l'API à tout domaine."
                )
            if not (
                candidate.startswith("https://")
                or candidate.startswith("http://localhost")
                or candidate.startswith("http://127.0.0.1")
            ):
                raise ValueError(
                    f"Origine CORS non autorisée : {candidate!r}. "
                    "Seuls HTTPS et le loopback HTTP de développement sont acceptés."
                )
            sanitized.append(candidate)
        return sanitized


settings: Settings = Settings()

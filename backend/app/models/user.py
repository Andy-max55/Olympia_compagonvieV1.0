"""Modèle ORM de l'utilisateur persistant."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import JSON, Column, String

from app.core.database import Base


class User(Base):
    """Utilisateur stocké dans la table ``users``.

    L'identifiant est un UUID sérialisé en chaîne : SQLite n'offre pas
    de type UUID natif, et cette représentation reste portable.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    preferences = Column(JSON, nullable=False)

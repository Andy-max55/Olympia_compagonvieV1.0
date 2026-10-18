"""Souvenirs durables extraits des messages de l'athlète."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class UserMemory(Base):
    """Un fait court rattaché à un utilisateur, sans compte de connexion."""

    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    fact = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

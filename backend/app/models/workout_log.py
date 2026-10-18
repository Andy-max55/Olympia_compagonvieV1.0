"""Journal des séances de sport enregistrées par Olympia."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class WorkoutLog(Base):
    """Une séance terminée, rattachée à l'utilisateur statique."""

    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    type_seance = Column(String, nullable=False)
    duree_minutes = Column(Integer, nullable=False)
    intensite = Column(String, nullable=False)
    date_seance = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

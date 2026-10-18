"""Outils que le coach peut appeler pendant la conversation."""

from __future__ import annotations

from langchain.tools import tool

from app.agents.memory import CURRENT_USER
from app.core.database import SessionLocal
from app.models.workout_log import WorkoutLog


@tool
def enregistrer_seance(type_seance: str, duree_minutes: int, intensite: str) -> str:
    """Enregistre une séance de sport que l'athlète vient de terminer.

    Appelle cet outil uniquement lorsque le type, la durée en minutes et
    l'intensité ont été donnés. Intensités attendues : Légère, Modérée, Maximale.

    Args:
        type_seance: Nature de la séance, par exemple basket, musculation ou récupération.
        duree_minutes: Durée réelle de la séance, en minutes.
        intensite: Intensité ressentie. Valeurs attendues : Légère, Modérée, Maximale.
    """
    session_type = type_seance.strip()
    level = intensite.strip()
    if not session_type or not level or duree_minutes <= 0:
        return "Séance refusée : le type, une durée positive et l'intensité sont requis."

    db = SessionLocal()
    try:
        db.add(
            WorkoutLog(
                user_id=CURRENT_USER,
                type_seance=session_type,
                duree_minutes=int(duree_minutes),
                intensite=level,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return "Séance enregistrée avec succès dans la base."

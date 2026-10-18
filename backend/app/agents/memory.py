"""Mémoire longue : lecture des faits et extraction en arrière-plan."""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user_memory import UserMemory

CURRENT_USER = "andy_admin"

_EXTRACTOR_PROMPT = (
    "Tu es un analyseur de données. Lis le message de l'utilisateur et extrais "
    "uniquement les faits médicaux, physiques, matériels ou liés à ses objectifs. "
    "Retourne chaque fait sous forme de phrase courte. S'il n'y a pas de fait "
    "pertinent, ne retourne rien."
)
_EMPTY_MARKERS = {
    "rien",
    "rien.",
    "aucun",
    "aucun.",
    "aucun fait",
    "aucun fait.",
    "néant",
    "néant.",
    "n/a",
    "pas de fait",
    "pas de fait pertinent",
}


def get_user_memories(user_id: str) -> list[str]:
    """Retourne les 10 faits les plus récents, du plus ancien au plus récent."""
    db = SessionLocal()
    try:
        rows = (
            db.query(UserMemory)
            .filter(UserMemory.user_id == user_id)
            .order_by(UserMemory.created_at.desc(), UserMemory.id.desc())
            .limit(10)
            .all()
        )
        return [str(row.fact) for row in reversed(rows)]
    finally:
        db.close()


def format_patient_memory(facts: list[str]) -> str:
    """Assemble les faits dans le bloc injecté au coach."""
    cleaned = [fact.strip() for fact in facts if fact and fact.strip()]
    if not cleaned:
        return ""
    return "MÉMOIRE DU PATIENT : " + " ; ".join(cleaned)


def _message_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "".join(parts)
    return str(content)


def _parse_facts(raw: str) -> list[str]:
    """Découpe la réponse de l'extracteur. Une réponse vide ne produit aucun fait."""
    text = raw.strip()
    if not text or text.lower() in _EMPTY_MARKERS:
        return []
    facts: list[str] = []
    for line in text.splitlines():
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line.strip().lstrip("-*•").strip())
        if not cleaned or cleaned.lower() in _EMPTY_MARKERS:
            continue
        facts.append(cleaned[:500])
    return facts


def _store_facts(user_id: str, facts: list[str]) -> None:
    db = SessionLocal()
    try:
        existing = {
            str(row.fact).strip().lower()
            for row in db.query(UserMemory.fact).filter(UserMemory.user_id == user_id).all()
        }
        for fact in facts:
            if fact.strip().lower() in existing:
                continue
            existing.add(fact.strip().lower())
            db.add(UserMemory(user_id=user_id, fact=fact.strip()))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def extract_and_store_facts(user_message: str) -> None:
    """Extrait les faits du message et les enregistre pour l'utilisateur statique.

    Les erreurs Gemini sont journalisées : cette tâche ne doit pas faire échouer le chat.
    """
    current_user = CURRENT_USER
    message = user_message.strip()
    if not message or not settings.GOOGLE_API_KEY:
        return
    try:
        extractor = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0,
            max_retries=1,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        response = await extractor.ainvoke(
            [
                SystemMessage(content=_EXTRACTOR_PROMPT),
                HumanMessage(content=message),
            ]
        )
        facts = _parse_facts(_message_text(response.content))
        if facts:
            _store_facts(current_user, facts)
    except Exception as error:
        print(f"=== EXTRACTION MÉMOIRE IGNORÉE : {error} ===")

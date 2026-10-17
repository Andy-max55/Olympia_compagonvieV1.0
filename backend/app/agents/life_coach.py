"""Agent Olympia basé sur Gemini, avec mémoire de session."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException
from google.api_core.exceptions import InternalServerError, ResourceExhausted, ServiceUnavailable
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import GoogleAPIError, GoogleRateLimitError

from app.core.config import settings

SYSTEM_INSTRUCTIONS: str = (
    "Tu es Olympia, une intelligence artificielle de coaching sportif et de "
    "préparation physique de très haut niveau. Ta mentalité est celle d'un "
    "préparateur physique d'élite (exigeant, analytique, méthodique) doublé "
    "d'une politesse extrême et d'une grande bienveillante.\n\n"
    "CONTEXTE UTILISATEUR CACHÉ : Étudiant à Torcy, joueur de basket (arrière, "
    "1m92) travaillant sa détente verticale, gérant de la fatigue due à des "
    "shifts chez Popeyes. Utilise cela pour tes analyses, mais ne récite jamais "
    "ces infos.\n\n"
    "RÈGLES FONDAMENTALES (NON NÉGOCIABLES) :\n\n"
    "RESTRICTION DE DOMAINE STRICTE : Ton expertise se limite EXCLUSIVEMENT au "
    "sport, à la préparation physique, à la récupération et à la nutrition. Si "
    "l'utilisateur te parle de programmation, de code (C#, Python, etc.) ou de "
    "tout autre sujet hors domaine, tu dois refuser très poliment et élégamment, "
    "en précisant que ton architecture est strictement dédiée à son excellence "
    "physique.\n\n"
    "TOLÉRANCE ZÉRO POUR LE HASARD : Tu es intransigeant sur la sécurité. Tu "
    "interdis formellement à l'utilisateur de tester ses capacités physiques à "
    "l'aveugle ou de faire des 'max' sans préparation. Tout effort doit être "
    "millimétré, défini et suivi.\n\n"
    "MÉTHODOLOGIE EXPERTE (POUR LES GROS PROGRAMMES) : Si l'utilisateur demande "
    "un plan complexe (programme de détente, plan nutritionnel, etc.), NE GÉNÈRE "
    "PAS un programme complet immédiatement. Tu dois D'ABORD te comporter comme "
    "un vrai coach : pose des questions sur ses métriques actuelles, ses "
    "antécédents de blessures, son équipement, et demande-lui de te fournir "
    "(si possible) des vidéos de ses mouvements (comme ses sauts ou ses squats) "
    "pour analyser sa biomécanique avant de prescrire quoi que ce soit.\n\n"
    "STYLE ET TON :\n\n"
    "Naturel et fluide (comme un humain très expert). Pas de longues listes "
    "inutiles si la réponse demande d'être courte.\n"
    "Poli, mais avec une autorité naturelle et protectrice. Ne mentionne jamais "
    "de formules marketing."
)

session_history: dict[str, list[BaseMessage]] = {}

_RETRYABLE_API_ERRORS = (
    ResourceExhausted,
    ServiceUnavailable,
    InternalServerError,
    GoogleRateLimitError,
    GoogleAPIError,
)
_SATURATED_DETAIL = (
    "Le réseau est temporairement saturé. Veuillez patienter un instant avant de réessayer."
)
_UNEXPECTED_DETAIL = "Une erreur inattendue est survenue."


class AgentConfigurationError(RuntimeError):
    """Levée lorsque Gemini ne peut pas être invoqué (configuration absente)."""


class LifeCoachAgent:
    """Génère un conseil personnalisé via Gemini, avec historique par utilisateur."""

    def __init__(self) -> None:
        self._llm: ChatGoogleGenerativeAI | None = None
        if not settings.GOOGLE_API_KEY:
            return
        self._llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0.4,
            max_retries=1,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    @staticmethod
    def _message_text(content: object) -> str:
        """Normalise le contenu d'un message Gemini en chaîne unique."""
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

    async def generate_advice(
        self,
        user_profile: dict[str, Any],
        user_message: str,
    ) -> str:
        """Invoque Gemini avec la mémoire de session de l'utilisateur."""
        if self._llm is None or not settings.GOOGLE_API_KEY:
            raise AgentConfigurationError("GOOGLE_API_KEY est manquante.")

        user_id: str = str(user_profile.get("id") or "").strip()
        if not user_id:
            raise HTTPException(status_code=500, detail=_UNEXPECTED_DETAIL)

        if user_id not in session_history:
            session_history[user_id] = [SystemMessage(content=SYSTEM_INSTRUCTIONS)]

        history = session_history[user_id]
        pending: list[BaseMessage] = [*history, HumanMessage(content=user_message)]
        response = None
        for attempt in range(3):
            try:
                response = await self._llm.ainvoke(pending)
                break
            except _RETRYABLE_API_ERRORS as error:
                if attempt == 2:
                    status_code = (
                        429
                        if isinstance(error, (ResourceExhausted, GoogleRateLimitError))
                        else 502
                    )
                    raise HTTPException(status_code=status_code, detail=_SATURATED_DETAIL) from error
                await asyncio.sleep(2 ** attempt)

        advice: str = self._message_text(response.content).strip() if response is not None else ""
        if not advice:
            raise HTTPException(status_code=500, detail=_UNEXPECTED_DETAIL)

        history.append(HumanMessage(content=user_message))
        history.append(AIMessage(content=advice))
        return advice

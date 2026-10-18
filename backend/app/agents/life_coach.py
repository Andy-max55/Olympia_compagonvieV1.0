"""Agent Olympia basé sur Gemini, avec mémoire de session."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import HTTPException
from google.api_core.exceptions import InternalServerError, ResourceExhausted, ServiceUnavailable
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import GoogleAPIError, GoogleRateLimitError

from app.agents.tools import enregistrer_seance
from app.core.config import settings

SYSTEM_INSTRUCTIONS: str = """Tu es Olympia, une intelligence artificielle de coaching sportif, de préparation physique et de bio-optimisation de classe mondiale. Ta mentalité fusionne la rigueur scientifique d'un biomécanicien d'élite, l'exigence d'un coach NBA et l'empathie d'un psychologue du sport. 

CONTEXTE UTILISATEUR CACHÉ (À utiliser pour personnaliser tes réponses, SANS JAMAIS l'énoncer explicitement) :
- Identité : Étudiant (campus Torcy), joueur de basket (arrière, 1m92).
- Objectif principal : Augmentation de la détente verticale, explosivité, mécanique de tir.
- Contrainte majeure : Charge allostatique (fatigue nerveuse et physique) élevée due à des shifts de travail réguliers chez Popeyes.
- Stratégie : Optimisation du ratio stimulus/récupération, protection des articulations.

1. INTELLIGENCE CONVERSATIONNELLE & PSYCHOLOGIE (TA SIGNATURE) :
- Écoute active et Validation : Avant de donner un conseil, valide toujours l'état de l'athlète. S'il rentre d'un shift épuisant chez Popeyes, fais preuve d'empathie, déconseille la haute intensité (pliométrie/max) et pivote vers la récupération active ou la nutrition.
- Pédagogie de l'Élite : N'ordonne pas bêtement. Explique brièvement le *pourquoi* biomécanique ou physiologique derrière chaque directive (ex: "Fais cet étirement pour libérer ton psoas, ce qui augmentera l'extension de ta hanche lors de ton saut").
- Rythme Séquentiel : Ne donne JAMAIS toutes les informations d'un coup. Sépare tes diagnostics. Si un sujet est complexe, donne la première étape, puis pose une question d'engagement ("Est-ce que cette logique te parle ?", "Prêt à voir le circuit ?").
- Adaptation du Ton : Sois tranchant et motivant quand l'athlète est en forme. Sois protecteur et clinique quand il est fatigué ou signale une douleur.

2. PROTOCOLE DE DIAGNOSTIC (MÉTHODE SOCRATIQUE) :
- L'anti-hasard : Un coach d'élite ne devine pas, il diagnostique. Face à une demande de programme, tu dois d'abord interroger l'athlète sur 3 piliers : son état de fatigue actuel, son équipement disponible, et d'éventuelles douleurs.
- Demande de feedback visuel : Pour des mouvements techniques (mécanique de saut, squats, shoot), incite l'athlète à te fournir des descriptions précises ou idéalement des vidéos (si l'interface le permet à l'avenir) avant de corriger sa technique.

3. RESTRICTION DE DOMAINE STRICTE (LE GARDE-FOU) :
- Ton expertise est absolue mais délimitée : sport, basket, préparation physique, neuro-récupération, sommeil et nutrition. 
- Si l'utilisateur aborde le code (Python, React, etc.), ses études en informatique, ou des sujets sans lien avec son corps, recadre-le avec une élégance implacable. (Ex: "Mon architecture est dédiée à la machine la plus complexe : ton corps. Laisse le code à ton ordinateur, concentrons-nous sur ta récupération.").

4. FORMATAGE ET ESTHÉTIQUE DE LA RÉPONSE :
- Lisibilité maximale : Utilise des paragraphes courts (2-3 phrases maximum).
- Mise en relief : Utilise le **gras** pour mettre en valeur les concepts clés ou les muscles ciblés.
- Listes minimalistes : Utilise des puces uniquement quand c'est strictement nécessaire pour détailler un circuit (Sets x Reps).
- Zéro marketing : Bannis totalement les phrases d'introduction robotiques ("Voici un programme..."), les formules publicitaires ou les conclusions du type "En résumé". Commence directement par la valeur.
- Fin de message : Termine toujours par une question précise, courte et orientée vers l'action ou la réflexion pour garder la balle dans son camp.

5. JOURNAL D'ENTRAÎNEMENT :
- Quand l'athlète rapporte une séance terminée et que le type, la durée en minutes et l'intensité sont connus, appelle enregistrer_seance avant ta réponse.
- N'invente jamais une durée ou une intensité manquante : demande-la.
- Après l'enregistrement, confirme-le brièvement, puis termine par une question.
"""
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
        self._llm = None
        self._agent = None
        if not settings.GOOGLE_API_KEY:
            return
        model = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0.4,
            max_retries=1,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self._llm = model.bind_tools([enregistrer_seance])
        self._agent = create_agent(model, tools=[enregistrer_seance])

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
        memory_context: str = "",
    ) -> str:
        """Invoque Gemini avec la mémoire de session et, s'il y en a, les faits durables."""
        if self._agent is None or not settings.GOOGLE_API_KEY:
            raise AgentConfigurationError("GOOGLE_API_KEY est manquante.")

        user_id: str = str(user_profile.get("id") or "").strip()
        if not user_id:
            raise HTTPException(status_code=500, detail=_UNEXPECTED_DETAIL)

        if user_id not in session_history:
            session_history[user_id] = [SystemMessage(content=SYSTEM_INSTRUCTIONS)]

        history = session_history[user_id]
        prior_turns = [message for message in history if not isinstance(message, SystemMessage)]
        system_text = SYSTEM_INSTRUCTIONS
        if memory_context.strip():
            system_text = f"{SYSTEM_INSTRUCTIONS}\n\n{memory_context.strip()}"
        pending: list[BaseMessage] = [
            SystemMessage(content=system_text),
            *prior_turns,
            HumanMessage(content=user_message),
        ]
        result = None
        for attempt in range(3):
            try:
                result = await self._agent.ainvoke({"messages": pending})
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

        advice = ""
        if isinstance(result, dict):
            for message in reversed(result.get("messages", [])):
                if isinstance(message, AIMessage):
                    advice = self._message_text(message.content).strip()
                    if advice:
                        break
        if not advice:
            raise HTTPException(status_code=500, detail=_UNEXPECTED_DETAIL)

        history.append(HumanMessage(content=user_message))
        history.append(AIMessage(content=advice))
        return advice

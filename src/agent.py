"""Définition de l'agent avec les outils et la configuration Gemini."""

from google import genai
from google.genai import types

from src.config import AGENT_MODEL, AGENT_TEMPERATURE
from src.prompt import SYSTEM_PROMPT
from src.tools import (
    check_mutuelle,
    search_slots,
    book_appointment,
    cancel_appointment,
    trigger_human_transfer,
    get_call_summary,
)

TOOLS = [
    check_mutuelle,
    search_slots,
    book_appointment,
    cancel_appointment,
    trigger_human_transfer,
    get_call_summary,
]


def create_chat(client: genai.Client) -> genai.chats.Chat:
    """Crée une session de chat avec le system prompt et les outils."""
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,
        temperature=AGENT_TEMPERATURE,
    )

    return client.chats.create(
        model=AGENT_MODEL,
        config=config,
    )

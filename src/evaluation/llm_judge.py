"""Évaluation LLM-as-judge avec Gemini."""

import json

from google import genai
from google.genai import types

from src.config import JUDGE_MODEL, JUDGE_TEMPERATURE
from src.evaluation.prompt import JUDGE_PROMPT


def evaluate_turn(
    client: genai.Client,
    user_message: str,
    reference: str,
    generated: str,
) -> dict:
    """Évalue un tour via LLM-as-judge.

    Returns:
        dict avec les 5 scores (0-5), les règles actives détectées, et la justification.
    """
    prompt = JUDGE_PROMPT.format(
        user_message=user_message,
        reference=reference,
        generated=generated,
    )

    response = client.models.generate_content(
        model=JUDGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=JUDGE_TEMPERATURE,
        ),
    )

    try:
        result = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        result = {
            "ton_professionnalisme": 0,
            "completude": 0,
            "exactitude_donnees": 0,
            "respect_regles_metier": 0,
            "concision_clarte": 0,
            "regles_actives": [],
            "justification": f"Erreur de parsing JSON: {response.text}",
        }

    return result


def evaluate_all_turns(
    client: genai.Client,
    results: list[dict],
    verbose: bool = False,
) -> list[dict]:
    """Évalue tous les tours avec le LLM-as-judge.

    Args:
        client: Client GenAI.
        results: Liste de dicts issus du dialogue runner.
        verbose: Afficher les détails.

    Returns:
        Liste de dicts enrichis avec les scores LLM.
    """
    evaluated = []
    for r in results:
        if verbose:
            print(f"  Évaluation LLM D{r['dialogue_id']} tour {r['turn_idx']}...")

        judge_result = evaluate_turn(
            client,
            r["user_message"],
            r["reference"],
            r["generated"],
        )

        enriched = {**r, "llm_judge": judge_result}
        evaluated.append(enriched)

    return evaluated

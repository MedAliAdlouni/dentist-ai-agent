"""Rejeu des dialogues de référence avec approche teacher-forcing."""

import pandas as pd

from google import genai

from src.agent import create_chat
from src.data_loader import get_dialogue_turns
from src.tools import reset_session_state
from src.tools.state import pop_tool_log


def run_dialogue(
    df: pd.DataFrame,
    dialogue_id: int,
    client=None,
    verbose: bool = False,
) -> list[dict]:
    """Rejoue un dialogue en teacher-forcing.

    Pour chaque tour SYSTEM, on génère la réponse de l'agent, mais on réinjecte
    la réponse de RÉFÉRENCE dans le contexte pour le tour suivant.

    Returns:
        Liste de dicts avec 'dialogue_id', 'turn_idx', 'reference', 'generated'.
    """
    reset_session_state()
    turns = get_dialogue_turns(df, dialogue_id)
    chat = create_chat(client)
    results = []

    # Le premier tour SYSTEM est le message d'accueil — on le skip
    # car c'est l'agent qui ouvre la conversation
    i = 0
    # Skip le premier tour SYSTEM (accueil)
    if turns and turns[0]["participant"] == "SYSTEM":
        i = 1

    while i < len(turns):
        turn = turns[i]

        if turn["participant"] == "USER":
            user_msg = turn["utterance"]
            # Chercher le tour SYSTEM suivant (la référence)
            ref_response = ""
            if i + 1 < len(turns) and turns[i + 1]["participant"] == "SYSTEM":
                ref_response = turns[i + 1]["utterance"]

            # Générer la réponse de l'agent
            generated = chat.send_message(user_msg).text or ""
            tool_calls = pop_tool_log()

            results.append(
                {
                    "dialogue_id": dialogue_id,
                    "turn_idx": turn["turn_idx"],
                    "user_message": user_msg,
                    "reference": ref_response,
                    "generated": generated,
                    "tool_calls": tool_calls,
                }
            )

            if verbose:
                print(f"\n--- D{dialogue_id} Tour {turn['turn_idx']} ---")
                print(f"USER: {user_msg}")
                print(f"REF:  {ref_response}")
                print(f"GEN:  {generated}")

            # Teacher-forcing : réinjecter la référence dans l'historique
            # On crée un nouveau message dans le chat avec la référence
            # pour que le contexte reste cohérent
            if ref_response and i + 1 < len(turns):
                # On passe au tour suivant (le SYSTEM qu'on vient de traiter)
                i += 2
            else:
                i += 1
        else:
            # Tour SYSTEM inattendu (pas le premier), on skip
            i += 1

    return results


def run_dialogues(
    df: pd.DataFrame,
    dialogue_ids: list[int],
    client=None,
    verbose: bool = False,
) -> list[dict]:
    """Rejoue plusieurs dialogues et retourne tous les résultats."""
    if client is None:
        client = genai.Client()

    all_results = []
    for did in dialogue_ids:
        if verbose:
            print(f"\n{'='*60}")
            print(f"DIALOGUE {did}")
            print(f"{'='*60}")
        results = run_dialogue(df, did, client=client, verbose=verbose)
        all_results.extend(results)

    return all_results

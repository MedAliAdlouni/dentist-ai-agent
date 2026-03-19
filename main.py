"""Point d'entrée : orchestration du rejeu des dialogues, de l'évaluation, et mode chat interactif."""

import sys

from dotenv import load_dotenv

load_dotenv()

from google import genai

from src.data_loader import load_dialogues, EVAL_IDS, DEV_IDS
from src.dialogue_runner import run_dialogues
from src.evaluation.deterministic import run_deterministic_checks
from src.evaluation.llm_judge import evaluate_all_turns
from src.evaluation.metrics import (
    compute_conformity_rate,
    compute_confusion_matrix,
    format_results,
)


def chat_mode():
    """Mode interactif : conversation texte ou voix avec le réceptionniste IA."""
    from src.agent import create_chat
    from src.tools import reset_session_state

    voice = "--voice" in sys.argv

    if voice:
        from src.voice import record_audio, transcribe, speak

    reset_session_state()
    client = genai.Client()
    chat = create_chat(client)

    mode_label = "voix" if voice else "texte"
    print(f"receptai — Mode conversation interactive ({mode_label})")
    print("=" * 60)
    if voice:
        print("Parlez dans votre microphone. Ctrl+C pour quitter.\n")
    else:
        print("Vous jouez le rôle d'un patient appelant la")
        print("Clinique Dentaire Saint-Michel.")
        print("Tapez 'quit' ou 'q' pour quitter.\n")

    # Message d'accueil de la réceptionniste
    greeting = chat.send_message("L'appel commence. Accueille le patient.").text or ""
    print(f"Réceptionniste : {greeting}\n")
    if voice:
        speak(client, greeting)

    while True:
        try:
            if voice:
                audio = record_audio()
                if not audio:
                    print("  [Aucune parole détectée, réessayez]")
                    continue
                user_input = transcribe(audio)
                if not user_input:
                    print("  [Transcription vide, réessayez]")
                    continue
                print(f"Vous : {user_input}")
            else:
                user_input = input("Vous : ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "q"):
                    print("\nFin de l'appel. Au revoir !")
                    break
        except (EOFError, KeyboardInterrupt):
            print("\n\nFin de l'appel. Au revoir !")
            break

        response = chat.send_message(user_input).text or ""
        print(f"\nRéceptionniste : {response}\n")
        if voice:
            speak(client, response)


def eval_mode():
    """Mode évaluation : rejeu des dialogues + scoring."""
    df = load_dialogues()
    print(f"Dialogues chargés : {len(df)} tours, {df['dialogue_id'].nunique()} dialogues")

    client = genai.Client()

    if "--dev" in sys.argv:
        dialogue_ids = DEV_IDS
        label = "DEV"
    else:
        dialogue_ids = EVAL_IDS
        label = "EVAL"

    verbose = "--verbose" in sys.argv
    print(f"\nExécution sur le jeu {label} : dialogues {dialogue_ids}")

    # Phase 1 : Rejeu des dialogues
    print("\n--- Phase 1 : Rejeu des dialogues (teacher-forcing) ---")
    results = run_dialogues(df, dialogue_ids, client=client, verbose=verbose)
    print(f"Tours générés : {len(results)}")

    # Phase 2 : Évaluation déterministe
    print("\n--- Phase 2 : Évaluation déterministe ---")
    context_by_dialogue: dict[int, list[str]] = {}
    for r in results:
        did = r["dialogue_id"]
        if did not in context_by_dialogue:
            context_by_dialogue[did] = []

        det_result = run_deterministic_checks(
            user_message=r["user_message"],
            generated=r["generated"],
            reference=r["reference"],
            context=context_by_dialogue[did],
            tool_calls=r.get("tool_calls", []),
        )
        r["deterministic"] = det_result

        context_by_dialogue[did].append(r["user_message"])
        context_by_dialogue[did].append(r["reference"])

        if verbose:
            tools = [c["tool"] for c in r.get("tool_calls", [])]
            print(
                f"  D{did} T{r['turn_idx']}: "
                f"règles={det_result['rules_detected']}, "
                f"outils={tools or '∅'}"
            )

    # Phase 3 : Évaluation LLM-as-judge
    print("\n--- Phase 3 : Évaluation LLM-as-judge ---")
    results = evaluate_all_turns(client, results, verbose=verbose)

    # Phase 4 : Métriques
    print("\n--- Phase 4 : Calcul des métriques ---")
    conformity = compute_conformity_rate(results)
    confusion = compute_confusion_matrix(results)

    print("\n" + format_results(conformity, confusion))


def main():
    print("receptai — Agent IA réceptionniste dentaire")
    print("=" * 60)

    if "--chat" in sys.argv or "--voice" in sys.argv:
        chat_mode()
    else:
        eval_mode()


if __name__ == "__main__":
    main()

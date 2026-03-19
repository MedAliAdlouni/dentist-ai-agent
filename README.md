# receptai

Agent IA réceptionniste pour la **Clinique Dentaire Saint-Michel**. Gère les appels patients par téléphone : prise de rendez-vous, triage douleur/urgence, vérification mutuelle et transfert humain.

## Stack

- **Google GenAI SDK** + Gemini 2.5 Flash (agent) / Gemini 2.5 Pro (LLM-judge)
- **6 outils** (function calling) : `check_mutuelle`, `search_slots`, `book_appointment`, `cancel_appointment`, `trigger_human_transfer`, `get_call_summary`
- **Mode voix** : faster-whisper (STT local) + Gemini TTS
- Python 3.12, uv

## Installation

```bash
cp .env.example .env       # Ajouter GOOGLE_API_KEY
uv sync                    # Installer les dépendances
```

## Utilisation

```bash
uv run main.py --voice     # Conversation interactive (voix)
```

## Regles metier (par priorite)

| Priorite | Regle | Declencheur | Action agent |
|----------|-------|-------------|--------------|
| 1 | R2 | Frustration / demande humain | Transfert via `trigger_human_transfer` |
| 2 | R1 | Douleur / symptomes | Echelle 1-10, urgence si >= 7 |
| 3 | R4 | Rendez-vous | Proposer 2 creneaux, reserver/annuler |
| 4 | R3 | Mutuelle | Verifier partenariat via `check_mutuelle` |
| 5 | R5 | Question generale | Reponse breve, orienter vers RDV |

Quand plusieurs regles s'appliquent, toutes sont traitees (la priorite determine l'ordre).

## Architecture

```
src/
  config.py              # Configuration centralisee (modeles, temperatures, splits)
  prompt.py              # System prompt + 5 exemples few-shot
  agent.py               # Session chat Gemini avec outils
  dialogue_runner.py     # Rejeu teacher-forcing des dialogues
  voice.py               # Enregistrement micro, STT whisper, TTS Gemini
  tools/                 # 6 outils avec logging des appels
    state.py             # Etat session + journal d'appels outils
  evaluation/
    deterministic.py     # Detection des regles par outils appeles
    llm_judge.py         # Evaluation qualitative (Gemini Pro)
    metrics.py           # Taux de conformite + matrice de confusion
data/
  dialogues.csv          # 15 dialogues de reference (97 tours)
  slots.json             # Creneaux par praticien (Martin, Dupont, Lefevre)
  mutuelles.json         # Mutuelles partenaires
```

## Evaluation

Double strategie :

- **Deterministe (40%)** : detection des regles a partir des outils appeles par l'agent (tool -> rule mapping)
- **LLM-as-judge (60%)** : 5 criteres notes de 0 a 5 (ton, completude, exactitude, regles metier, concision)

Produit un taux de conformite global + matrice de confusion par regle.

Date de reference : mercredi 11 mars 2026

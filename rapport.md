# receptai — Rapport technique

Agent conversationnel IA pour la gestion des appels téléphoniques d'un cabinet dentaire (Clinique Dentaire Saint-Michel). Le système traite les demandes de rendez-vous, urgences dentaires, vérifications de mutuelle et transferts humains via un pipeline LLM avec injection de données externes.

## 1. Architecture

Le pipeline s'articule en 4 phases séquentielles, orchestrées depuis `main.py` :

```
                          ┌─────────────────────┐
                          │   dialogues.csv      │
                          │   (15 dialogues,     │
                          │    97 tours)          │
                          └────────┬─────────────┘
                                   │ data_loader.py
                                   ▼
                ┌──────────────────────────────────────┐
                │  Phase 1 — Rejeu teacher-forcing      │
                │  dialogue_runner.py                    │
                │                                        │
                │  Pour chaque tour USER :                │
                │    → Envoi au LLM (Gemini 2.5 Flash)   │
                │    ← Réponse générée + tool_calls       │
                │    → Réinjection de la réf. dans le ctx │
                └──────────┬───────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌───────────┐  ┌──────────────┐
   │ slots.json   │  │mutuelles  │  │ 6 outils     │
   │ (créneaux)   │  │.json      │  │ (function    │
   │              │  │(partenaires)│ │  calling)    │
   └─────────────┘  └───────────┘  └──────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                                 ▼
   ┌──────────────────┐          ┌────────────────────┐
   │ Phase 2           │          │ Phase 3             │
   │ Eval déterministe │          │ LLM-as-judge        │
   │ (outils → règles) │          │ (Gemini 2.5 Pro)    │
   │ Poids : 40%       │          │ Poids : 60%         │
   └────────┬──────────┘          └────────┬────────────┘
            └──────────┬───────────────────┘
                       ▼
              ┌─────────────────┐
              │ Phase 4          │
              │ Métriques finales│
              │ (conformité,     │
              │  matrice de      │
              │  confusion)      │
              └─────────────────┘
```

**Modèle agent** : Gemini 2.5 Flash (t=0.3) avec 6 outils déclarés via le function calling natif du SDK Google GenAI : `search_slots`, `book_appointment`, `cancel_appointment`, `check_mutuelle`, `trigger_human_transfer`, `get_call_summary`. Chaque outil opère sur un état mutable partagé (`state.py`) qui simule le SI du cabinet (créneaux, réservations, mutuelles). Le **teacher-forcing** réinjecte la réponse de référence (et non la réponse générée) dans le contexte pour isoler l'évaluation tour par tour.

## 2. Méthode de prompt

Le system prompt (`src/prompt.py`, 106 lignes) repose sur quatre principes :

1. **Hiérarchie de règles explicite** — 5 règles métier (R1–R5) ordonnées par priorité. R2 (transfert humain) est prioritaire sur tout ; R1 (douleur/urgence) déclenche un protocole spécifique avec échelle de douleur 1–10 et seuil à 7 pour l'orientation urgence.

2. **Injection de contexte structuré** — Le prompt intègre la date de référence, les horaires, et le mapping praticien/spécialité (Martin → soins généraux, Dupont → orthodontie, Lefèvre → implantologie) pour que le LLM route correctement les demandes.

3. **Gestion de la douleur par seuil** — La règle R1 impose de demander systématiquement l'intensité de la douleur. Au-dessus de 7, le flag `urgency=True` est passé à `search_slots` pour filtrer les créneaux d'urgence (jour même ou lendemain). En dessous, un rendez-vous standard est proposé.

4. **Few-shot multi-règles** — 5 exemples de dialogues complets couvrant les combinaisons de règles les plus complexes (R1+R3+R4, R5+R1+R3+R4, R4+R2, etc.), sélectionnés depuis le jeu de dev pour démontrer le chaînage de plusieurs règles dans un même appel et le respect du vouvoiement.

## 3. Stratégie d'évaluation

L'évaluation hybride combine deux approches complémentaires :

**Évaluation déterministe (40%)** — Basée sur l'observation des outils appelés par l'agent. Le mapping `TOOL_TO_RULES` déduit les règles traitées : `search_slots(urgency=True)` → R1, `check_mutuelle` → R3, `trigger_human_transfer` → R2, etc. Cette approche est reproductible et sans coût additionnel, mais ne capture que le *comportement* (quel outil a été appelé), pas la *qualité* de la réponse textuelle.

**LLM-as-judge (60%)** — Un second LLM (Gemini 2.5 Pro, t=0.1) évalue chaque réponse générée sur 5 critères notés de 0 à 5 : ton/professionnalisme, complétude, exactitude des données, respect des règles métier, concision. Le juge identifie aussi les règles actives, permettant de construire une matrice de confusion par règle.

**Justification** — La pondération 40/60 reflète le fait que la conformité métier (outils corrects) est nécessaire mais insuffisante : une réponse peut appeler le bon outil mais mal formuler la proposition au patient. Le LLM-judge capture ces nuances sémantiques.

**Limites** — (1) Le juge LLM est lui-même non déterministe (scores légèrement variables entre runs). (2) L'évaluation déterministe attribue R5 par défaut quand aucun outil n'est appelé, ce qui peut masquer des erreurs de classification (ex: l'agent aurait dû appeler un outil mais ne l'a pas fait). (3) Le jeu d'évaluation (7 dialogues, 17 tours) reste modeste pour tirer des conclusions statistiques robustes.

## 4. Résultats

**Taux de conformité global : ~85%** (déterministe : 100% | LLM-judge : ~75%)

| Règle | Conformité | Precision | Recall | F1   | Analyse |
|-------|-----------|-----------|--------|------|---------|
| R1    | 84%       | 0.29      | 1.00   | 0.44 | Le juge sur-détecte R1 (FP élevés) |
| R2    | 40%       | 1.00      | 1.00   | 1.00 | Score bas car le LLM génère une réponse vide au transfert |
| R3    | 90%       | 0.50      | 1.00   | 0.67 | Bien traitée ; quelques FP du juge |
| R4    | 83%       | 0.82      | 1.00   | 0.90 | Principale source d'erreurs sémantiques |
| R5    | 94%       | 1.00      | 0.44   | 0.61 | Sous-détectée par le juge (recall faible) |

**Échecs notables :**

- **D4 (rendez-vous détartrage)** — L'agent propose des créneaux du jour même au lieu de ceux de la référence (jeudi/vendredi). Au tour suivant, il ne retrouve plus le créneau demandé par le patient. Cause : le `search_slots` renvoie les premiers créneaux disponibles sans préférence temporelle, là où la référence privilégiait des créneaux à J+1/J+2.

- **D5/D6 (urgences dentaires)** — L'agent identifie correctement l'urgence et propose des créneaux, mais au moment de la confirmation, il redemande une validation au lieu de réserver directement (`book_appointment`). La référence confirme en un tour ; l'agent en aurait besoin de deux.

- **D7 (transfert humain)** — L'agent appelle correctement `trigger_human_transfer` mais génère une réponse textuelle vide, ce qui pénalise lourdement le score LLM-judge (ton, complétude à 0). Le transfert technique fonctionne, mais le patient ne reçoit aucun message oral.

- **D11 (annulation + replanification)** — L'agent demande l'heure exacte du rendez-vous à annuler au lieu d'agir directement, ajoutant un tour de friction inutile par rapport à la référence.

## 5. Mise en production

- **Déploiement** — Conteneurisation via `Dockerfile` (Python 3.12 + `uv`). Deux options GCP pour une MEP rapide :
  - **Cloud Run** — Déploiement serverless avec autoscaling et cold starts maîtrisés
  - **Vertex AI Agent Engine** — Hosting managé d'agents avec intégration native du SDK Google GenAI et gestion du cycle de vie
- **Monitoring** — Trois axes à suivre via Cloud Monitoring / Logging :
  - **Latence P95** par tour (cible < 2s pour le temps réel téléphonique)
  - **Coût par appel** en tokens Gemini (entrée + sortie) pour anticiper la volumétrie
  - **Satisfaction patient** — Taux de transfert humain (proxy de frustration) et score CSAT post-appel
- **Fallback** — Transfert automatique vers le secrétariat humain après 3 échecs d'outil ou timeout LLM (>5s)
- **Données** — Remplacer les fichiers JSON statiques (`slots.json`, `mutuelles.json`) par des appels API au logiciel métier du cabinet pour garantir la fraîcheur des données

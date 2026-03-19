"""Détection déterministe des règles métier à partir des outils appelés par l'agent."""

# Mapping outil → règle(s)
TOOL_TO_RULES = {
    "check_mutuelle": {"R3"},
    "search_slots": {"R4"},
    "book_appointment": {"R4"},
    "cancel_appointment": {"R4"},
    "trigger_human_transfer": {"R2"},
}


def run_deterministic_checks(
    user_message: str,
    generated: str,
    reference: str,
    context: list[str] | None = None,
    tool_calls: list[dict] | None = None,
) -> dict:
    """Déduit les règles traitées à partir des outils appelés par l'agent."""
    tool_calls = tool_calls or []
    rules = set()

    for call in tool_calls:
        name = call["tool"]
        if name == "search_slots" and call["args"].get("urgency"):
            rules.add("R1")
        rules.update(TOOL_TO_RULES.get(name, set()))

    # Pas d'outil appelé → R5 (question générale / réponse sans action)
    if not rules:
        rules.add("R5")

    return {
        "rules_detected": rules,
        "tool_calls": tool_calls,
        "score": 1.0,
    }

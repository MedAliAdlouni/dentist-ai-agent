"""État mutable partagé entre les outils pour une session d'appel."""

from src.data_loader import load_slots, load_mutuelles

slots_data = load_slots()
mutuelles_data = load_mutuelles()

booked: list[dict] = []
cancelled: list[dict] = []
transfer_info: dict | None = None
tool_log: list[dict] = []


def log_tool_call(name: str, args: dict):
    """Enregistre un appel d'outil."""
    tool_log.append({"tool": name, "args": args})


def pop_tool_log() -> list[dict]:
    """Retourne et vide le journal d'appels d'outils."""
    calls = list(tool_log)
    tool_log.clear()
    return calls


def reset_session_state():
    """Réinitialise l'état entre dialogues."""
    global transfer_info
    booked.clear()
    cancelled.clear()
    transfer_info = None
    tool_log.clear()

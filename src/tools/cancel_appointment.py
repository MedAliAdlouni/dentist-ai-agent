"""Outil : annulation d'un rendez-vous."""

from src.tools import state
from src.tools.state import booked, cancelled


def cancel_appointment(
    practitioner_name: str, date: str, time: str
) -> dict:
    """Annule un rendez-vous existant.

    Args:
        practitioner_name: Nom du praticien.
        date: Date au format YYYY-MM-DD.
        time: Heure au format HH:MM.

    Returns:
        dict avec 'success' (bool) et 'message' (str).
    """
    state.log_tool_call("cancel_appointment", {"practitioner_name": practitioner_name, "date": date, "time": time})
    cancellation = {
        "praticien": practitioner_name,
        "date": date,
        "heure": time,
    }
    cancelled.append(cancellation)
    for i, b in enumerate(booked):
        if (
            practitioner_name.lower() in b["praticien"].lower()
            and b["date"] == date
            and b["heure"] == time
        ):
            booked.pop(i)
            break
    return {
        "success": True,
        "message": f"Rendez-vous avec {practitioner_name} le {date} à {time} annulé.",
    }

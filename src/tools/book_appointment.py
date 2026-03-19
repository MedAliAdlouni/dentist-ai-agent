"""Outil : réservation d'un créneau de rendez-vous."""

from src.tools import state
from src.tools.state import slots_data, booked


def book_appointment(
    practitioner_name: str,
    date: str,
    time: str,
    patient_name: str = "",
    care_type: str = "",
) -> dict:
    """Réserve un créneau de rendez-vous.

    Args:
        practitioner_name: Nom du praticien.
        date: Date au format YYYY-MM-DD.
        time: Heure au format HH:MM.
        patient_name: Nom du patient (optionnel).
        care_type: Type de soin (optionnel).

    Returns:
        dict avec 'success' (bool) et 'message' (str).
    """
    state.log_tool_call("book_appointment", {"practitioner_name": practitioner_name, "date": date, "time": time})
    for prat in slots_data["praticiens"]:
        if practitioner_name.lower() not in prat["nom"].lower():
            continue
        for slot in prat["creneaux"]:
            if slot["date"] == date and slot["heure"] == time:
                booking = {
                    "praticien": prat["nom"],
                    "date": date,
                    "heure": time,
                    "patient": patient_name,
                    "soin": care_type,
                }
                booked.append(booking)
                return {
                    "success": True,
                    "message": f"Rendez-vous confirmé avec {prat['nom']} le {date} à {time}.",
                    "details": booking,
                }

    return {
        "success": False,
        "message": f"Créneau non trouvé pour {practitioner_name} le {date} à {time}.",
    }

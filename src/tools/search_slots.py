"""Outil : recherche de créneaux disponibles."""

from src.tools import state
from src.tools.state import slots_data, booked


def search_slots(
    care_type: str = "",
    urgency: bool = False,
    practitioner_name: str = "",
    date_min: str = "",
    date_max: str = "",
    max_results: int = 2,
) -> dict:
    """Recherche des créneaux disponibles selon les critères.

    Args:
        care_type: Type de soin (ex: 'soins généraux', 'orthodontie', 'implantologie').
        urgency: Si True, filtre les créneaux de type 'urgence' du jour ou lendemain.
        practitioner_name: Nom du praticien (ex: 'Dr. Martin').
        date_min: Date minimum au format YYYY-MM-DD.
        date_max: Date maximum au format YYYY-MM-DD.
        max_results: Nombre maximum de créneaux à retourner (défaut: 2).

    Returns:
        dict avec 'creneaux' (liste) et 'nombre_total' (int).
    """
    state.log_tool_call("search_slots", {"care_type": care_type, "urgency": urgency, "practitioner_name": practitioner_name})
    results = []
    care_lower = care_type.strip().lower()
    prat_lower = practitioner_name.strip().lower()

    for prat in slots_data["praticiens"]:
        if prat_lower and prat_lower not in prat["nom"].lower():
            continue
        if care_lower and care_lower not in prat["specialite"].lower():
            continue

        for slot in prat["creneaux"]:
            if any(
                b["praticien"] == prat["nom"]
                and b["date"] == slot["date"]
                and b["heure"] == slot["heure"]
                for b in booked
            ):
                continue

            if urgency and slot["type"] != "urgence":
                continue
            if date_min and slot["date"] < date_min:
                continue
            if date_max and slot["date"] > date_max:
                continue

            results.append(
                {
                    "praticien": prat["nom"],
                    "specialite": prat["specialite"],
                    "date": slot["date"],
                    "jour": slot["jour"],
                    "heure": slot["heure"],
                    "type": slot["type"],
                }
            )

    return {
        "creneaux": results[:max_results],
        "nombre_total": len(results),
    }

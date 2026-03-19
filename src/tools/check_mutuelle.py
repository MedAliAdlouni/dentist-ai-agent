"""Outil : vérification du statut partenaire d'une mutuelle."""

from src.tools import state
from src.tools.state import mutuelles_data


def check_mutuelle(mutuelle_name: str) -> dict:
    """Vérifie si une mutuelle est partenaire pour le tiers payant.

    Args:
        mutuelle_name: Nom de la mutuelle à vérifier.

    Returns:
        dict avec 'est_partenaire' (bool), 'nom' (str), et 'message' (str).
    """
    state.log_tool_call("check_mutuelle", {"mutuelle_name": mutuelle_name})
    name_lower = mutuelle_name.strip().lower()
    for m in mutuelles_data["partenaires_tiers_payant"]:
        if name_lower in m["nom"].lower() or m["nom"].lower() in name_lower:
            return {
                "est_partenaire": True,
                "nom": m["nom"],
                "code": m["code"],
                "message": f"La mutuelle {m['nom']} est partenaire. Nous pratiquons le tiers payant. Veuillez demander le numéro de contrat au patient.",
            }
    return {
        "est_partenaire": False,
        "nom": mutuelle_name,
        "message": mutuelles_data["politique_hors_partenariat"],
    }

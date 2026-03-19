"""Outil : récapitulatif des actions de l'appel."""

from src.tools.state import booked, cancelled, transfer_info


def get_call_summary() -> dict:
    """Génère un récapitulatif des actions effectuées pendant l'appel.

    Returns:
        dict avec 'reservations', 'annulations', 'transfert'.
    """
    return {
        "reservations": list(booked),
        "annulations": list(cancelled),
        "transfert": transfer_info,
    }

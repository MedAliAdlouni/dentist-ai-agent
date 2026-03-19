"""Outil : transfert vers le secrétariat humain."""

from src.tools import state


def trigger_human_transfer(reason_summary: str, patient_sentiment: str = "") -> dict:
    """Transfère l'appel vers le secrétariat humain.

    Args:
        reason_summary: Résumé du motif de l'appel.
        patient_sentiment: Sentiment du patient (ex: 'frustré', 'neutre').

    Returns:
        dict avec 'transferred' (bool) et 'message' (str).
    """
    state.log_tool_call("trigger_human_transfer", {"reason_summary": reason_summary, "patient_sentiment": patient_sentiment})
    state.transfer_info = {
        "raison": reason_summary,
        "sentiment": patient_sentiment,
    }
    return {
        "transferred": True,
        "message": f"Transfert vers le secrétariat effectué. Motif : {reason_summary}.",
    }

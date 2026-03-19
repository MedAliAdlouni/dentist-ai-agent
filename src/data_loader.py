"""Chargement des données : dialogues CSV, créneaux JSON, mutuelles JSON."""

import json
from pathlib import Path

import pandas as pd

from src.config import DEV_IDS, EVAL_IDS  # noqa: F401 — re-exported

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_dialogues(path: Path | None = None) -> pd.DataFrame:
    """Charge les dialogues depuis le CSV et retourne un DataFrame."""
    path = path or DATA_DIR / "dialogues.csv"
    return pd.read_csv(path)


def load_slots(path: Path | None = None) -> dict:
    """Charge les créneaux depuis slots.json."""
    path = path or DATA_DIR / "slots.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_mutuelles(path: Path | None = None) -> dict:
    """Charge les mutuelles depuis mutuelles.json."""
    path = path or DATA_DIR / "mutuelles.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_dialogue_ids(df: pd.DataFrame) -> list[int]:
    """Retourne la liste triée des IDs de dialogue."""
    return sorted(df["dialogue_id"].unique().tolist())


def get_dialogue_turns(df: pd.DataFrame, dialogue_id: int) -> list[dict]:
    """Retourne les tours d'un dialogue sous forme de liste de dicts."""
    sub = df[df["dialogue_id"] == dialogue_id].sort_values("turn_idx")
    return sub.to_dict("records")

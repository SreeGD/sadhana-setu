"""Affirmation library — sastra-rooted sankalpa declarations.

These are NOT modern self-help affirmations. Each line is a short
declaration of who the chanter is in relation to Krishna, drawn from
established Vaishnava sastra and acarya literature.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

AFFIRMATIONS_FILE = Path(__file__).parent.parent.parent / "data" / "affirmations.yaml"


@dataclass(frozen=True)
class Affirmation:
    text: str
    source: str | None = None
    category: str | None = None


def _load() -> list[Affirmation]:
    if not AFFIRMATIONS_FILE.exists():
        return []
    doc = yaml.safe_load(AFFIRMATIONS_FILE.read_text()) or {}
    return [Affirmation(**row) for row in doc.get("affirmations", [])]


_ALL: list[Affirmation] = _load()


def all_affirmations() -> list[Affirmation]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> Affirmation | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

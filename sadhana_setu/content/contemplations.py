"""Contemplative micro-practice library for the pre-japa reading (spec 005, FR-005).

One short act to do before chanting — a line to sit with, a single prayer to repeat, or a
question to hold. It records nothing and is never scored (Constitution IV).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

CONTEMPLATIONS_FILE = Path(__file__).parent.parent.parent / "data" / "contemplations.yaml"


@dataclass(frozen=True)
class Contemplation:
    kind: str  # "sit_with" | "prayer" | "question"
    prompt: str
    source: str | None = None


def _load() -> list[Contemplation]:
    if not CONTEMPLATIONS_FILE.exists():
        return []
    doc = yaml.safe_load(CONTEMPLATIONS_FILE.read_text()) or {}
    return [Contemplation(**row) for row in doc.get("contemplations", [])]


_ALL: list[Contemplation] = _load()


def all_contemplations() -> list[Contemplation]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> Contemplation | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

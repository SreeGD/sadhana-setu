"""Bhajan library — Saturday rotation, 52-week cycle.

A bhajan is a devotional song from established Vaishnava collections:
Bhaktivinoda Thakura's Saranagati / Gita-mala / Kalyana-kalpa-taru,
Narottama Dasa Thakura's Prarthana, Padyavali by Rupa Gosvami, etc.

Each entry shows: title, author, one verse (IAST + translation),
and a source citation pointing to the collection.

Saturday rotation index: ISO-week-number modulo library size.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

BHAJANS_FILE = Path(__file__).parent.parent.parent / "data" / "bhajans.yaml"


@dataclass(frozen=True)
class Bhajan:
    title: str
    author: str
    verse_iast: str
    verse_translation: str
    source: str


def _load() -> list[Bhajan]:
    if not BHAJANS_FILE.exists():
        return []
    doc = yaml.safe_load(BHAJANS_FILE.read_text()) or {}
    return [Bhajan(**row) for row in doc.get("bhajans", [])]


_ALL: list[Bhajan] = _load()


def all_bhajans() -> list[Bhajan]:
    return list(_ALL)


def pick_for_week(d: date | None = None) -> Bhajan | None:
    """Pick the bhajan for the ISO week containing `d`."""
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.isocalendar().week % len(_ALL)]

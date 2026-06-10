"""Faith-verse library — Name-promise verses from sastra.

Each entry references a verse the kg-mcp server can enrich with full
Sanskrit + IAST + translation + purport via get_verse(verse_ref).
The library carries a hand-curated short summary that renders even
when the corpus is offline.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

FAITH_VERSES_FILE = Path(__file__).parent.parent.parent / "data" / "faith_verses.yaml"


@dataclass(frozen=True)
class FaithVerse:
    verse_ref: str
    summary: str
    source: str | None = None


def _load() -> list[FaithVerse]:
    if not FAITH_VERSES_FILE.exists():
        return []
    doc = yaml.safe_load(FAITH_VERSES_FILE.read_text()) or {}
    return [FaithVerse(**row) for row in doc.get("faith_verses", [])]


_ALL: list[FaithVerse] = _load()


def all_faith_verses() -> list[FaithVerse]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> FaithVerse | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

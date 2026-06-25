"""Curated tip library loader.

The tip library is read-only at runtime. The agent never generates tips on
the fly — every tip in the library has been hand-curated and reviewed.
The 'source' field cites where the teaching comes from (sastra), not a
verbatim quote.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import yaml

TIPS_FILE = Path(__file__).parent.parent.parent / "data" / "tips.yaml"


@dataclass(frozen=True)
class Tip:
    value_id: str
    tip: str
    source: str | None = None
    ekadasi_aware: bool = False


def _load() -> list[Tip]:
    if not TIPS_FILE.exists():
        return []
    doc = yaml.safe_load(TIPS_FILE.read_text()) or {}
    return [Tip(**row) for row in doc.get("tips", [])]


_ALL: list[Tip] = _load()


def all_tips() -> list[Tip]:
    return list(_ALL)


def by_value(value_id: str) -> list[Tip]:
    return [t for t in _ALL if t.value_id == value_id]


def pick_tip(
    value_ids: list[str],
    ekadasi: bool = False,
    rng: random.Random | None = None,
) -> Tip | None:
    """Pick one tip from the union of value_ids. On ekadasi, prefer ekadasi-tagged tips when any are available."""
    chooser = rng or random
    candidates = [t for t in _ALL if t.value_id in value_ids]
    if not candidates:
        return None
    if ekadasi:
        ekadasi_tips = [t for t in candidates if t.ekadasi_aware]
        if ekadasi_tips:
            return chooser.choice(ekadasi_tips)
    return chooser.choice(candidates)


def pick_for_today(d=None):
    """Deterministic one-tip-a-day (by day-of-year) for the pre-japa arc."""
    import datetime
    d = d or datetime.date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]


def reload() -> None:
    """Re-read the YAML. For tests."""
    global _ALL
    _ALL = _load()

"""Saṅkalpa pool — a pre-japa vow for the day (spec 005 blend).

A saṅkalpa is action-binding ("I will…"), not belief-shaping ("I am…"). The pre-japa view shows
ONE per day: Wednesday returns the anchor (Bhūrijana Prabhu's primary vow), other days rotate the
non-anchor pool by day-of-year. Mirrors the static build's ``todaySankalpa``
(``data/sankalpas.yaml``).
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path

import yaml

SANKALPAS_FILE = Path(__file__).parent.parent.parent / "data" / "sankalpas.yaml"
_WEDNESDAY = 2  # date.weekday(): Mon=0 … Wed=2 … Sun=6


@dataclass(frozen=True)
class Sankalpa:
    text: str
    source: str | None = None
    category: str | None = None
    anchor: bool = False


_KNOWN = {f.name for f in fields(Sankalpa)}


def _load() -> list[Sankalpa]:
    if not SANKALPAS_FILE.exists():
        return []
    doc = yaml.safe_load(SANKALPAS_FILE.read_text()) or {}
    return [Sankalpa(**{k: v for k, v in row.items() if k in _KNOWN})
            for row in doc.get("sankalpas", [])]


_ALL: list[Sankalpa] = _load()


def all_sankalpas() -> list[Sankalpa]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> Sankalpa | None:
    """Wednesday → the anchor vow; other days → a non-anchor vow rotated by day-of-year."""
    d = d or date.today()
    if not _ALL:
        return None
    anchor = next((s for s in _ALL if s.anchor), _ALL[0])
    if d.weekday() == _WEDNESDAY:
        return anchor
    pool = [s for s in _ALL if not s.anchor]
    return pool[d.timetuple().tm_yday % len(pool)] if pool else anchor

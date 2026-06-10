"""Inspiration library — micro-pastimes (2–4 sentences each) drawn from
Srimad Bhagavatam, Caitanya Caritamrta, and Vaishnava acarya biographies.

Stories are short enough to read in 20 seconds and serve as a reminder
that real beings have lived the practice.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

INSPIRATIONS_FILE = Path(__file__).parent.parent.parent / "data" / "inspirations.yaml"


@dataclass(frozen=True)
class Inspiration:
    title: str
    text: str
    source: str | None = None


def _load() -> list[Inspiration]:
    if not INSPIRATIONS_FILE.exists():
        return []
    doc = yaml.safe_load(INSPIRATIONS_FILE.read_text()) or {}
    return [Inspiration(**row) for row in doc.get("inspirations", [])]


_ALL: list[Inspiration] = _load()


def all_inspirations() -> list[Inspiration]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> Inspiration | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

"""Weekly reading library — one chapter from the Nama-Tattva book per week.

The library is intentionally larger than a quarter; weekly rotation by ISO
week index cycles through it over the year. User can expand the library
over time to fill 52 weeks of the Nama-Tattva framework.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

READINGS_FILE = Path(__file__).parent.parent.parent / "data" / "weekly_readings.yaml"


@dataclass(frozen=True)
class Reading:
    title: str
    subtitle: str
    theme: str
    reading_minutes: int
    content: str
    source: str


def _load() -> list[Reading]:
    if not READINGS_FILE.exists():
        return []
    doc = yaml.safe_load(READINGS_FILE.read_text()) or {}
    return [Reading(**row) for row in doc.get("readings", [])]


_ALL: list[Reading] = _load()


def all_readings() -> list[Reading]:
    return list(_ALL)


def pick_for_week(d: date | None = None) -> Reading | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.isocalendar().week % len(_ALL)]

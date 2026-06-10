"""Four japa methods — weekly rotation through the lineage practices.

Sources confirmed:
  - Govardhana School of Yoga (Pañca Mahābhūta Śuddhi)
  - HH Sacinandana Swami (Samādhāya Mano Hṛdi from SB 8.3.1)
  - HG Mahatma Prabhu (Attentive Chanting techniques)
  - HG Bhurijana Prabhu (4-Step Technique from VIHE retreats)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

METHODS_FILE = Path(__file__).parent.parent.parent / "data" / "japa_methods.yaml"


@dataclass(frozen=True)
class JapaStep:
    title: str
    practice: str


@dataclass(frozen=True)
class JapaMethod:
    name: str
    teacher: str
    duration_minutes: int
    one_line: str
    overview: str
    steps: tuple[JapaStep, ...]
    closing: str
    source: str


def _load() -> list[JapaMethod]:
    if not METHODS_FILE.exists():
        return []
    doc = yaml.safe_load(METHODS_FILE.read_text()) or {}
    methods: list[JapaMethod] = []
    for row in doc.get("methods", []):
        steps = tuple(JapaStep(**s) for s in row.get("steps", []))
        methods.append(
            JapaMethod(
                name=row["name"],
                teacher=row["teacher"],
                duration_minutes=row["duration_minutes"],
                one_line=row["one_line"],
                overview=row["overview"],
                steps=steps,
                closing=row.get("closing", ""),
                source=row.get("source", ""),
            )
        )
    return methods


_ALL: list[JapaMethod] = _load()


def all_methods() -> list[JapaMethod]:
    return list(_ALL)


def pick_for_week(d: date | None = None) -> JapaMethod | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.isocalendar().week % len(_ALL)]

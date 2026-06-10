"""Nama-Tattva library — 20-second teachings on the Holy Name.

Sources, in curation order:
  1. Srila Prabhupada's purports (primary — the modern bridge)
  2. Hari-nama-cintamani by Bhaktivinoda Thakura
  3. Bhajana-rahasya by Bhaktivinoda Thakura
  4. Padma Purana — the ten offenses (nama-aparadha)
  5. Siksastakam by Sri Caitanya Mahaprabhu

Topics: three stages of the Name, ten offenses, sambandha-jnana,
hearing as essence, yugala-mantra structure, anartha-nivrtti, etc.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

NAMA_TATTVA_FILE = Path(__file__).parent.parent.parent / "data" / "nama_tattva.yaml"


@dataclass(frozen=True)
class NamaTattva:
    title: str
    teaching: str
    source: str | None = None


def _load() -> list[NamaTattva]:
    if not NAMA_TATTVA_FILE.exists():
        return []
    doc = yaml.safe_load(NAMA_TATTVA_FILE.read_text()) or {}
    return [NamaTattva(**row) for row in doc.get("nama_tattva", [])]


_ALL: list[NamaTattva] = _load()


def all_teachings() -> list[NamaTattva]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> NamaTattva | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

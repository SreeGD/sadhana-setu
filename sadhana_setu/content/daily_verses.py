"""Daily-verse library — one verse a day that *brings mood for chanting* (spec 005 blend).

Optional pre-japa reading: a verse from SB/BG/CC that orients the heart for hearing/japa,
shown collapsed (tap-to-read) so it adds depth without spending the ≤2-minute budget. Mirrors
the static build's ``todayVerse`` (``data/daily_verses.yaml``). The kg-mcp server can enrich the
``verse_ref`` further; the curated IAST + translation render even when the corpus is offline.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path

import yaml

DAILY_VERSES_FILE = Path(__file__).parent.parent.parent / "data" / "daily_verses.yaml"


@dataclass(frozen=True)
class DailyVerse:
    verse_ref: str
    iast: str = ""
    translation: str = ""
    mood_brought: str | None = None
    chanting_connection: str | None = None
    category: str | None = None
    source: str | None = None


_KNOWN = {f.name for f in fields(DailyVerse)}


def _load() -> list[DailyVerse]:
    if not DAILY_VERSES_FILE.exists():
        return []
    doc = yaml.safe_load(DAILY_VERSES_FILE.read_text()) or {}
    return [DailyVerse(**{k: v for k, v in row.items() if k in _KNOWN})
            for row in doc.get("daily_verses", [])]


_ALL: list[DailyVerse] = _load()


def all_daily_verses() -> list[DailyVerse]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> DailyVerse | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

"""Practical-tip-from-the-book library — daily rotation.

These are practical *actions* drawn from the Nama-Tattva publication's
practical sections (Section 2.7 enemy control, Section 2.3 pre-japa
methods, Section 3.6 Guṇa-Tattva lifestyle). Different in shape from
the curated tips library: every entry tells the chanter what to DO
today, with a specific named technique from a named teacher or source.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

BOOK_TIPS_FILE = Path(__file__).parent.parent.parent / "data" / "book_tips.yaml"


@dataclass(frozen=True)
class BookTip:
    title: str
    instruction: str
    source: str
    addresses: str | None = None  # which enemy / aspect this targets


def _load() -> list[BookTip]:
    if not BOOK_TIPS_FILE.exists():
        return []
    doc = yaml.safe_load(BOOK_TIPS_FILE.read_text()) or {}
    return [BookTip(**row) for row in doc.get("book_tips", [])]


_ALL: list[BookTip] = _load()


def all_book_tips() -> list[BookTip]:
    return list(_ALL)


def pick_for_today(d: date | None = None) -> BookTip | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.timetuple().tm_yday % len(_ALL)]

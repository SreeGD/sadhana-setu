"""Weekly story library — long-form devotee transformation pastimes.

The Sunday read. Mirrors the Saturday Bhajan slot but on Sunday. Stories
are 200-500 words — substantial enough to feel like a real reading,
short enough to fit one sitting. Seven core devotees from SB/CC, then
deeper pastimes as the library grows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

STORIES_FILE = Path(__file__).parent.parent.parent / "data" / "weekly_stories.yaml"


@dataclass(frozen=True)
class WeeklyStory:
    title: str
    devotee: str
    one_line: str
    text: str
    key_verse: str
    scripture: str
    teaching: str


def _load() -> list[WeeklyStory]:
    if not STORIES_FILE.exists():
        return []
    doc = yaml.safe_load(STORIES_FILE.read_text()) or {}
    return [WeeklyStory(**row) for row in doc.get("stories", [])]


_ALL: list[WeeklyStory] = _load()


def all_stories() -> list[WeeklyStory]:
    return list(_ALL)


def pick_for_week(d: date | None = None) -> WeeklyStory | None:
    d = d or date.today()
    if not _ALL:
        return None
    return _ALL[d.isocalendar().week % len(_ALL)]

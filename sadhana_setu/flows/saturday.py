"""Saturday check-in flow — week-at-a-glance + persistence.

The check-in is the product's primary ritual. Two halves:
  - Half 1 (Observe): rotating sastra-rooted questions + week-at-a-glance.
  - Half 2 (Set): tone, mood/bhava, practices, tools, priorities for the
    coming week (sankalpa).

Persistence is upsert by week_start (the check-in's Saturday) — submit
the form multiple times in the same week and the row updates in place.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sadhana_setu.db.connection import connect


@dataclass(frozen=True)
class WeekSummary:
    week_start: date
    days: list[tuple[date, int | None]]
    rounds_completed_days: int
    total_rounds: int
    hearing_note_count: int


@dataclass
class WeeklyCheckin:
    week_start: str
    survey_answers: list[dict] = field(default_factory=list)
    tone: str = ""
    mood_bhava: str = ""
    practices: list[str] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)
    tools_needed: list[str] = field(default_factory=list)
    surfaced_pattern: str | None = None
    submitted_at: str = ""


def most_recent_saturday(d: date | None = None) -> date:
    """The most recent Saturday on or before `d` (default today). Saturday = weekday 5."""
    d = d or date.today()
    days_back = (d.weekday() - 5) % 7
    return d - timedelta(days=days_back)


def week_at_a_glance(saturday: date) -> WeekSummary:
    days = [saturday - timedelta(days=i) for i in range(6, -1, -1)]  # oldest -> newest
    with connect() as conn:
        rounds_rows = conn.execute(
            "SELECT date, count FROM rounds WHERE date BETWEEN ? AND ?",
            (days[0].isoformat(), days[-1].isoformat()),
        ).fetchall()
        note_count = conn.execute(
            "SELECT COUNT(*) FROM hearing_notes WHERE date BETWEEN ? AND ?",
            (days[0].isoformat(), days[-1].isoformat()),
        ).fetchone()[0]
    rounds_map = {r["date"]: r["count"] for r in rounds_rows}
    day_counts = [(d, rounds_map.get(d.isoformat())) for d in days]
    completed = sum(1 for _, c in day_counts if c is not None and c >= 16)
    total = sum(c for _, c in day_counts if c is not None)
    return WeekSummary(
        week_start=saturday,
        days=day_counts,
        rounds_completed_days=completed,
        total_rounds=total,
        hearing_note_count=note_count,
    )


def get_checkin(saturday: date) -> WeeklyCheckin | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM weekly_checkins WHERE week_start = ?",
            (saturday.isoformat(),),
        ).fetchone()
    if row is None:
        return None
    return WeeklyCheckin(
        week_start=row["week_start"],
        survey_answers=json.loads(row["survey_answers"]) if row["survey_answers"] else [],
        tone=row["tone"] or "",
        mood_bhava=row["mood_bhava"] or "",
        practices=json.loads(row["practices"]) if row["practices"] else [],
        priorities=json.loads(row["priorities"]) if row["priorities"] else [],
        tools_needed=json.loads(row["tools_needed"]) if row["tools_needed"] else [],
        surfaced_pattern=row["surfaced_pattern"],
        submitted_at=row["submitted_at"],
    )


def save_checkin(c: WeeklyCheckin) -> None:
    """Upsert. Idempotent on re-save for the same week_start."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO weekly_checkins(
                week_start, survey_answers, tone, mood_bhava,
                practices, priorities, tools_needed,
                surfaced_pattern, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_start) DO UPDATE SET
                survey_answers = excluded.survey_answers,
                tone = excluded.tone,
                mood_bhava = excluded.mood_bhava,
                practices = excluded.practices,
                priorities = excluded.priorities,
                tools_needed = excluded.tools_needed,
                surfaced_pattern = excluded.surfaced_pattern,
                submitted_at = excluded.submitted_at
            """,
            (
                c.week_start,
                json.dumps(c.survey_answers, ensure_ascii=False),
                c.tone,
                c.mood_bhava,
                json.dumps(c.practices, ensure_ascii=False),
                json.dumps(c.priorities, ensure_ascii=False),
                json.dumps(c.tools_needed, ensure_ascii=False),
                c.surfaced_pattern,
                c.submitted_at,
            ),
        )
        conn.commit()

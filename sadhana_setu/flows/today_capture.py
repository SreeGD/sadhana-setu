"""Daily capture — DB functions for rounds and hearing notes.

Rounds are keyed by date (one row per day, upsert on re-edit).
Hearing notes are append-only (multiple per day allowed).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sadhana_setu.db.connection import connect


@dataclass(frozen=True)
class Round:
    date: str
    count: int
    captured_at: str
    note: str | None = None


@dataclass(frozen=True)
class HearingNote:
    id: int
    date: str
    source: str | None
    line: str
    captured_at: str


def get_today_rounds(d: date) -> Round | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT date, count, captured_at, note FROM rounds WHERE date = ?",
            (d.isoformat(),),
        ).fetchone()
    if row is None:
        return None
    return Round(row["date"], row["count"], row["captured_at"], row["note"])


def save_rounds(d: date, count: int, note: str | None = None) -> None:
    """Upsert today's rounds. Idempotent on re-edit for the same date."""
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO rounds(date, count, captured_at, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                count = excluded.count,
                captured_at = excluded.captured_at,
                note = excluded.note
            """,
            (d.isoformat(), count, now, note),
        )
        conn.commit()


def list_hearing_notes(d: date) -> list[HearingNote]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, date, source, line, captured_at FROM hearing_notes "
            "WHERE date = ? ORDER BY id",
            (d.isoformat(),),
        ).fetchall()
    return [HearingNote(r["id"], r["date"], r["source"], r["line"], r["captured_at"]) for r in rows]


def add_hearing_note(d: date, source: str | None, line: str) -> int:
    """Append a hearing note for the day. Returns the new id."""
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO hearing_notes(date, source, line, captured_at) VALUES (?, ?, ?, ?)",
            (d.isoformat(), source, line, now),
        )
        conn.commit()
        return cur.lastrowid


def delete_hearing_note(note_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM hearing_notes WHERE id = ?", (note_id,))
        conn.commit()

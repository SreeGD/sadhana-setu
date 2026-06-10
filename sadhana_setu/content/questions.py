"""Curated weekly question library — schema + rotation selector.

The YAML file is the source of truth for question text. Runtime tracks
`last_asked` in SQLite (weekly_questions table) so rotation persists
across sessions.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from sadhana_setu.db.connection import connect

QUESTIONS_FILE = Path(__file__).parent.parent.parent / "data" / "weekly_questions.yaml"


@dataclass(frozen=True)
class Question:
    id: int
    question: str
    routes_through: str | None
    last_asked: str | None


def _load_yaml() -> list[dict]:
    if not QUESTIONS_FILE.exists():
        return []
    doc = yaml.safe_load(QUESTIONS_FILE.read_text()) or {}
    return doc.get("questions", [])


def seed_db() -> int:
    """Insert any questions from YAML that are not yet in the DB. Idempotent. Returns count of new rows."""
    rows = _load_yaml()
    inserted = 0
    with connect() as conn:
        for row in rows:
            cur = conn.execute(
                "SELECT 1 FROM weekly_questions WHERE question = ?",
                (row["question"],),
            )
            if cur.fetchone():
                continue
            conn.execute(
                "INSERT INTO weekly_questions(question, routes_through, last_asked) VALUES (?, ?, ?)",
                (row["question"], row.get("routes_through"), None),
            )
            inserted += 1
        conn.commit()
    return inserted


def all_questions() -> list[Question]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, question, routes_through, last_asked FROM weekly_questions ORDER BY id"
        ).fetchall()
    return [Question(r["id"], r["question"], r["routes_through"], r["last_asked"]) for r in rows]


def pick_questions(n: int = 3) -> list[Question]:
    """Pick n questions preferring those with the oldest (or NULL) last_asked."""
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, question, routes_through, last_asked
            FROM weekly_questions
            ORDER BY last_asked IS NULL DESC, last_asked ASC, RANDOM()
            LIMIT ?
            """,
            (n,),
        ).fetchall()
    return [Question(r["id"], r["question"], r["routes_through"], r["last_asked"]) for r in rows]


def mark_asked(question_id: int, when_iso: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE weekly_questions SET last_asked = ? WHERE id = ?",
            (when_iso, question_id),
        )
        conn.commit()

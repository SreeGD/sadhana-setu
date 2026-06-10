"""SQLite schema for Sadhana Setu. All v1 user data lives in one file."""
import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "./data/sadhana_setu.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    date TEXT PRIMARY KEY,
    count INTEGER NOT NULL,
    captured_at TEXT NOT NULL,
    note TEXT
);

CREATE TABLE IF NOT EXISTS hearing_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    source TEXT,
    line TEXT NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_checkins (
    week_start TEXT PRIMARY KEY,
    survey_answers TEXT NOT NULL,
    tone TEXT,
    mood_bhava TEXT,
    practices TEXT,
    priorities TEXT,
    tools_needed TEXT,
    surfaced_pattern TEXT,
    submitted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value_id TEXT NOT NULL,
    tip TEXT NOT NULL,
    source TEXT,
    ekadasi_aware INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS weekly_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    routes_through TEXT,
    last_asked TEXT
);

CREATE TABLE IF NOT EXISTS patterns_log (
    week_start TEXT PRIMARY KEY,
    n_observed_days INTEGER NOT NULL,
    candidates_checked TEXT NOT NULL,
    qualifying_pattern TEXT,
    statistics TEXT,
    fired_at TEXT NOT NULL
);
"""


def get_db_path() -> str:
    return os.environ.get("SADHANA_SETU_DB", DEFAULT_DB_PATH)


def migrate(db_path: str | None = None) -> str:
    db_path = db_path or get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return db_path

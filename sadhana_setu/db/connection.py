"""Database connection helper."""
import sqlite3
from contextlib import contextmanager

from sadhana_setu.db.schema import get_db_path, migrate


@contextmanager
def connect():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def ensure_initialized() -> None:
    """Idempotent. Safe to call on every app startup."""
    migrate()

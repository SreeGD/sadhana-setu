"""Audit log for pattern surfacing.

Writes one row per Saturday to patterns_log, regardless of whether the
rule fired. The log preserves what the engine saw and decided so we can
inspect rule behavior over time.
"""
from __future__ import annotations

import json
from datetime import date, datetime

from sadhana_setu.db.connection import connect
from sadhana_setu.patterns.engine import PatternResult


def log_pattern(week_start: date, result: PatternResult) -> None:
    """Upsert one patterns_log row per week_start."""
    now = datetime.now().isoformat(timespec="seconds")
    pre_registered = ["prev_day_rounds_completed", "ekadasi_today", "prev_night_sleep_time"]
    qualifying = result.headline if result.fired else None
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO patterns_log(
                week_start, n_observed_days, candidates_checked,
                qualifying_pattern, statistics, fired_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_start) DO UPDATE SET
                n_observed_days = excluded.n_observed_days,
                candidates_checked = excluded.candidates_checked,
                qualifying_pattern = excluded.qualifying_pattern,
                statistics = excluded.statistics,
                fired_at = excluded.fired_at
            """,
            (
                week_start.isoformat(),
                result.n_observed,
                json.dumps(pre_registered),
                qualifying,
                json.dumps(result.statistics, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()

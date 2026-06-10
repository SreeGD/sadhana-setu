"""Data assembly — build (predictor, outcome) pairs for analysis."""
from __future__ import annotations

from datetime import date, timedelta

from sadhana_setu.db.connection import connect
from sadhana_setu.patterns.predictors import HistoryContext, Predictor, outcome


def load_history(end_date: date, window_days: int = 90) -> HistoryContext:
    """Load rounds data for the past `window_days` ending on `end_date`."""
    start = end_date - timedelta(days=window_days - 1)
    with connect() as conn:
        rows = conn.execute(
            "SELECT date, count FROM rounds WHERE date BETWEEN ? AND ?",
            (start.isoformat(), end_date.isoformat()),
        ).fetchall()
    rounds = {r["date"]: r["count"] for r in rows}
    return HistoryContext(end_date=end_date, rounds=rounds)


def build_pairs(
    predictor: Predictor,
    ctx: HistoryContext,
    window_days: int = 90,
) -> list[tuple[float, float]]:
    """For each day in the window, (predictor_value, outcome). Drops days where either is None."""
    pairs: list[tuple[float, float]] = []
    start = ctx.end_date - timedelta(days=window_days - 1)
    for offset in range(window_days):
        d = start + timedelta(days=offset)
        x = predictor.value(d, ctx)
        y = outcome(d, ctx)
        if x is None or y is None:
            continue
        pairs.append((x, y))
    return pairs


def n_observed_days(ctx: HistoryContext, window_days: int = 90) -> int:
    """Days within window where rounds were captured (any count, including 0)."""
    start = ctx.end_date - timedelta(days=window_days - 1)
    n = 0
    for offset in range(window_days):
        d = start + timedelta(days=offset)
        if d.isoformat() in ctx.rounds:
            n += 1
    return n

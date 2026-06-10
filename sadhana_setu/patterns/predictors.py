"""Pre-registered predictors. Per PRD: ≤3 candidates per phase.

v1 candidates:
  - prev_day_rounds_completed: was yesterday's count >= 16?
  - ekadasi_today: is today ekadasi?
  - prev_night_sleep_time: placeholder — returns None until sleep tracking ships

Pre-registration matters: the multiple-comparison correction (BH-FDR)
only protects us if the candidate set is fixed BEFORE looking at data.
Don't add predictors here based on what looks interesting in the data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from sadhana_setu.calendar import is_ekadasi


@dataclass(frozen=True)
class Predictor:
    id: str
    label: str
    value: Callable[[date, "HistoryContext"], float | None]  # type: ignore[name-defined]


@dataclass
class HistoryContext:
    end_date: date
    rounds: dict[str, int]


def _prev_day_completed(d: date, ctx: HistoryContext) -> float | None:
    prev = (d - timedelta(days=1)).isoformat()
    c = ctx.rounds.get(prev)
    if c is None:
        return None
    return 1.0 if c >= 16 else 0.0


def _ekadasi_today(d: date, ctx: HistoryContext) -> float | None:
    return 1.0 if is_ekadasi(d) else 0.0


def _prev_night_sleep_time(d: date, ctx: HistoryContext) -> float | None:
    return None  # not yet tracked


PREDICTORS: tuple[Predictor, ...] = (
    Predictor("prev_day_rounds_completed", "Yesterday at vow (≥16 rounds)", _prev_day_completed),
    Predictor("ekadasi_today", "Today is Ekadasi", _ekadasi_today),
    Predictor("prev_night_sleep_time", "Previous night's sleep time", _prev_night_sleep_time),
)


def outcome(d: date, ctx: HistoryContext) -> float | None:
    """Today's rounds count. None if not captured."""
    c = ctx.rounds.get(d.isoformat())
    return None if c is None else float(c)

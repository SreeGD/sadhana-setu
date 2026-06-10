"""Unit tests for the pattern engine — verifies the five-condition rule."""
from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta

import pytest

from sadhana_setu.db.schema import migrate
from sadhana_setu.flows.today_capture import save_rounds
from sadhana_setu.patterns.assemble import load_history, n_observed_days
from sadhana_setu.patterns.engine import (
    BF_THRESHOLD,
    MIN_DAYS,
    RHO_THRESHOLD,
    surface_pattern,
)
from sadhana_setu.patterns.predictors import HistoryContext
from sadhana_setu.patterns.stats import bh_fdr, evaluate


@pytest.fixture()
def isolated_db(monkeypatch):
    path = tempfile.mktemp(suffix=".db")
    monkeypatch.setenv("SADHANA_SETU_DB", path)
    migrate(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def _seed_rounds(rounds_by_day: dict[date, int]) -> None:
    for d, count in rounds_by_day.items():
        save_rounds(d, count)


def test_silent_at_low_N(isolated_db):
    """C1: N < 21 should fire silent_low_n."""
    end_date = date(2026, 6, 13)
    _seed_rounds({end_date - timedelta(days=i): 16 for i in range(14)})
    ctx = load_history(end_date)
    result = surface_pattern(ctx)
    assert result.kind == "silent_low_n"
    assert not result.fired
    assert result.n_observed == 14


def test_silent_when_no_variance(isolated_db):
    """C3 & C4: data with no Y-variance leaves all predictors un-evaluable → silent_no_data."""
    end_date = date(2026, 6, 13)
    # All days completed at 16. Both Y and prev_day_completed have zero variance.
    _seed_rounds({end_date - timedelta(days=i): 16 for i in range(30)})
    ctx = load_history(end_date)
    result = surface_pattern(ctx)
    assert not result.fired
    assert result.n_observed >= MIN_DAYS
    assert result.kind in ("silent_no_data", "silent_no_pattern")


def test_fires_on_synthetic_positive(isolated_db):
    """Construct data where prev-day-completed strongly predicts today's count.

    Pattern: when yesterday was completed (>=16), today is also high (>=16);
    when yesterday was not, today is also low. This is a near-perfect
    autocorrelation that should pass all five conditions.
    """
    end_date = date(2026, 6, 13)
    counts: dict[date, int] = {}
    for i in range(30):
        d = end_date - timedelta(days=i)
        # Pattern: even-indexed days completed (16), odd not (10). Strong autocorrelation.
        counts[d] = 16 if i % 2 == 0 else 10
    _seed_rounds(counts)
    ctx = load_history(end_date)
    result = surface_pattern(ctx)
    # With alternating pattern, prev-day-completed is perfectly anti-correlated
    # with today-completion. That's still a strong (negative) correlation.
    assert result.fired, f"expected fire, got {result.kind}: {result.headline}"
    assert result.predictor_id == "prev_day_rounds_completed"
    assert abs(result.statistics["rho"]) >= RHO_THRESHOLD
    assert result.statistics["bf"] >= BF_THRESHOLD


def test_bh_fdr_correctness():
    """BH-FDR sanity: with one tiny p-value and others large, only the tiny one rejects."""
    rejected = bh_fdr([0.001, 0.5, 0.6], q=0.10)
    assert rejected == [True, False, False]

    # All small p-values: all reject
    rejected = bh_fdr([0.001, 0.002, 0.003], q=0.10)
    assert rejected == [True, True, True]

    # Empty
    assert bh_fdr([], q=0.10) == []


def test_evaluate_handles_zero_variance():
    """When all x are identical, correlation is undefined → return None."""
    pairs = [(1.0, 10.0), (1.0, 12.0), (1.0, 8.0), (1.0, 11.0), (1.0, 9.0)]
    assert evaluate(pairs) is None


def test_evaluate_handles_short_input():
    """Fewer than 5 pairs → return None."""
    pairs = [(0.0, 10.0), (1.0, 16.0), (0.0, 12.0)]
    assert evaluate(pairs) is None

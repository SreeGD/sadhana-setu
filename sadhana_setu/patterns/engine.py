"""Pattern surfacing rule orchestrator. The Saturday-firing rule.

Five conditions ALL must hold to fire a pattern observation:
  C1. N ≥ 21 observed days in the 90-day window
  C2. Predictor on pre-registered list (PREDICTORS)
  C3. |ρ| ≥ 0.35 AND Bayes factor ≥ 3
  C4. Survived BH-FDR at q=.10 across the evaluated set
  C5. Stable — same predictor evaluated on most recent 14 days
      still meets |ρ| ≥ 0.35

If multiple predictors qualify, surface the one with largest |ρ|.
Otherwise: silent (with an honest null result message).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from math import isfinite
from typing import Literal

from sadhana_setu.patterns.assemble import (
    HistoryContext,
    build_pairs,
    load_history,
    n_observed_days,
)
from sadhana_setu.patterns.predictors import PREDICTORS, Predictor
from sadhana_setu.patterns.stats import CorrelationResult, bh_fdr, evaluate

MIN_DAYS = 21
RHO_THRESHOLD = 0.35
BF_THRESHOLD = 3.0
FDR_Q = 0.10
STABILITY_WINDOW = 14


PatternKind = Literal["pattern", "silent_low_n", "silent_no_data", "silent_no_pattern"]


@dataclass
class PatternResult:
    kind: PatternKind
    headline: str
    detail: str
    predictor_id: str | None = None
    statistics: dict = field(default_factory=dict)
    n_observed: int = 0
    week_summary: dict = field(default_factory=dict)

    @property
    def fired(self) -> bool:
        return self.kind == "pattern"


def _evaluate_one(predictor: Predictor, ctx: HistoryContext, window_days: int) -> CorrelationResult | None:
    pairs = build_pairs(predictor, ctx, window_days=window_days)
    return evaluate(pairs)


def _format_descriptive(ctx: HistoryContext, n: int) -> str:
    # Last 7 days summary
    last7 = []
    for offset in range(6, -1, -1):
        d = ctx.end_date - timedelta(days=offset)
        c = ctx.rounds.get(d.isoformat())
        last7.append(c)
    completed = sum(1 for c in last7 if c is not None and c >= 16)
    captured = sum(1 for c in last7 if c is not None)
    return (
        f"This week's raw count: {completed}/7 days at vow (≥16). "
        f"{captured}/7 days captured. {n} total observed days in the 90-day window."
    )


def surface_pattern(ctx: HistoryContext, window_days: int = 90) -> PatternResult:
    n = n_observed_days(ctx, window_days)

    if n < MIN_DAYS:
        return PatternResult(
            kind="silent_low_n",
            headline="Too early to surface patterns.",
            detail=(
                f"Observed days so far: {n}. Patterns will start surfacing "
                f"after {MIN_DAYS} days, and only if the rule passes."
            ),
            n_observed=n,
        )

    evaluated: list[tuple[Predictor, CorrelationResult]] = []
    for predictor in PREDICTORS:
        r = _evaluate_one(predictor, ctx, window_days)
        if r is None:
            continue
        evaluated.append((predictor, r))

    if not evaluated:
        return PatternResult(
            kind="silent_no_data",
            headline="No predictor had enough data this week.",
            detail=_format_descriptive(ctx, n),
            n_observed=n,
        )

    p_vals = [r.p_value for _, r in evaluated]
    fdr_passed = bh_fdr(p_vals, q=FDR_Q)

    candidates: list[tuple[Predictor, CorrelationResult]] = []
    for (predictor, r), passed in zip(evaluated, fdr_passed):
        if not passed:
            continue
        if abs(r.rho) < RHO_THRESHOLD:
            continue
        if r.bf < BF_THRESHOLD:
            continue
        if not _is_stable(predictor, ctx):
            continue
        candidates.append((predictor, r))

    if not candidates:
        return PatternResult(
            kind="silent_no_pattern",
            headline="I checked for patterns this week and didn't find one worth naming.",
            detail=_format_descriptive(ctx, n),
            n_observed=n,
            statistics={
                "evaluated": [
                    {"predictor": p.id, "rho": round(r.rho, 3), "bf": round(r.bf, 2), "p": round(r.p_value, 4)}
                    for p, r in evaluated
                ],
                "fdr_passed_count": sum(fdr_passed),
            },
        )

    predictor, r = max(candidates, key=lambda x: abs(x[1].rho))
    sign = "moved together" if r.rho > 0 else "moved in opposite directions"
    headline = (
        f"Across the last {r.n} days, completing rounds and "
        f"“{predictor.label}” have {sign} more often than chance would predict "
        f"(ρ={r.rho:+.2f}; weak-to-moderate association, not proof of cause)."
    )
    bf_for_audit = round(r.bf, 2) if isfinite(r.bf) else 1e6
    return PatternResult(
        kind="pattern",
        headline=headline,
        detail=_format_descriptive(ctx, n),
        predictor_id=predictor.id,
        n_observed=n,
        statistics={
            "n": r.n,
            "rho": round(r.rho, 4),
            "p_value": round(r.p_value, 4),
            "bf": bf_for_audit,
        },
    )


def _is_stable(predictor: Predictor, ctx: HistoryContext) -> bool:
    pairs = build_pairs(predictor, ctx, window_days=STABILITY_WINDOW)
    r = evaluate(pairs)
    if r is None:
        return False
    return abs(r.rho) >= RHO_THRESHOLD


def surface_for_saturday(saturday: date) -> PatternResult:
    """Convenience entry — load history and run the rule for a Saturday's check-in."""
    ctx = load_history(saturday, window_days=90)
    return surface_pattern(ctx)

"""Statistics for the pattern engine.

Uses Pearson correlation (with binary predictors and continuous outcome,
this is the point-biserial correlation). Bayes factor via pingouin's
JZS prior implementation (BF10 column in pg.corr).

Spearman would be the research-preferred default per `02_research.md`,
but pingouin only computes BF10 for Pearson. For binary predictors the
two are essentially equivalent (Spearman ≈ Pearson when one variable
takes only two values). If we add continuous predictors later, revisit.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import pingouin as pg


@dataclass
class CorrelationResult:
    n: int
    rho: float
    p_value: float
    bf: float


def evaluate(pairs: list[tuple[float, float]]) -> CorrelationResult | None:
    """Compute correlation, p-value, and Bayes factor for a sequence of (x, y) pairs.

    Returns None when the pair count is too small (<5) or when either
    variable has zero variance (which makes the correlation undefined).
    """
    if len(pairs) < 5:
        return None
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    if min(xs) == max(xs) or min(ys) == max(ys):
        return None  # zero variance — correlation undefined
    result = pg.corr(xs, ys, method="pearson")
    row = result.iloc[0]
    rho = float(row["r"])
    # pingouin renamed 'p-val' to 'p_val' in 0.6. Try both for safety.
    p_val = float(row["p_val"] if "p_val" in row.index else row["p-val"])
    bf_raw = row.get("BF10")
    try:
        bf = float(bf_raw)
        if bf != bf:  # NaN
            bf = 0.0
        elif bf == float("-inf") or bf < 0:
            bf = 0.0
        # Positive infinity is allowed — it's the strongest possible BF.
    except (TypeError, ValueError):
        bf = 0.0
    return CorrelationResult(n=len(pairs), rho=rho, p_value=p_val, bf=bf)


def bh_fdr(p_values: list[float], q: float = 0.10) -> list[bool]:
    """Benjamini-Hochberg FDR correction.

    Returns a list of booleans aligned with `p_values`. True means the
    null is rejected (i.e., this test passes the FDR control at level q).
    """
    n = len(p_values)
    if n == 0:
        return []
    sorted_idx = sorted(range(n), key=lambda i: p_values[i])
    largest_k = 0
    for k, idx in enumerate(sorted_idx, start=1):
        if p_values[idx] <= q * k / n:
            largest_k = k
    rejected = [False] * n
    for k in range(largest_k):
        rejected[sorted_idx[k]] = True
    return rejected

"""
Statistical testing utilities.

Provides Wilcoxon signed-rank test and summary statistics for comparing
algorithm performance across multiple runs.
"""
from __future__ import annotations

import math
from typing import Sequence


def mean_std(values: Sequence[float]) -> tuple[float, float]:
    """Return (mean, std) for a list of floats."""
    if not values:
        return 0.0, 0.0
    n = len(values)
    mu = sum(values) / n
    if n < 2:
        return mu, 0.0
    var = sum((v - mu) ** 2 for v in values) / (n - 1)
    return mu, math.sqrt(var)


def confidence_interval_95(values: Sequence[float]) -> tuple[float, float]:
    """Return 95% CI (lower, upper) assuming approximate normality."""
    mu, sd = mean_std(values)
    n = len(values)
    if n < 2:
        return mu, mu
    # t-value for 95% CI with small n ≈ 2.0 (conservative)
    t = 2.776 if n <= 5 else 2.262 if n <= 10 else 1.96
    margin = t * sd / math.sqrt(n)
    return round(mu - margin, 4), round(mu + margin, 4)


def wilcoxon_signed_rank(x: Sequence[float], y: Sequence[float]) -> dict:
    """
    Simplified Wilcoxon signed-rank test (two-sided).

    Returns dict with 'statistic', 'p_value', 'significant' (at α=0.05),
    and 'effect_size_r'.

    Falls back to a simple sign-test approximation when scipy is unavailable.
    """
    try:
        from scipy.stats import wilcoxon as scipy_wilcoxon

        stat, p = scipy_wilcoxon(x, y, alternative="two-sided")
        n = len(x)
        r = abs(stat - n * (n + 1) / 4) / math.sqrt(n * (n + 1) * (2 * n + 1) / 24) if n > 0 else 0
        return {
            "statistic": float(stat),
            "p_value": float(p),
            "significant": p < 0.05,
            "effect_size_r": round(r, 4),
        }
    except ImportError:
        # Fallback: simple sign test
        diffs = [xi - yi for xi, yi in zip(x, y)]
        pos = sum(1 for d in diffs if d > 0)
        neg = sum(1 for d in diffs if d < 0)
        n = pos + neg
        return {
            "statistic": float(min(pos, neg)),
            "p_value": -1.0,  # Cannot compute exact p without scipy
            "significant": False,
            "effect_size_r": 0.0,
            "note": "scipy not available; sign-test fallback used",
        }


def summary_table(
    results: list[dict],
    metric_keys: list[str],
    group_by: str = "algorithm",
) -> list[dict]:
    """
    Aggregate results into a summary table.

    Groups by *group_by* and computes mean ± std for each metric.
    """
    from collections import defaultdict

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        groups[r[group_by]].append(r)

    table = []
    for name, rows in groups.items():
        row = {group_by: name, "n": len(rows)}
        for key in metric_keys:
            vals = [r[key] for r in rows if key in r]
            mu, sd = mean_std(vals)
            row[f"{key}_mean"] = round(mu, 2)
            row[f"{key}_std"] = round(sd, 2)
            ci = confidence_interval_95(vals)
            row[f"{key}_ci95"] = ci
        table.append(row)
    return table

"""
Drift monitoring — detect distribution shifts in predictions over time.

Compares recent predictions against a historical baseline using:
  - Chi-squared test for class distribution drift
  - Kolmogorov-Smirnov test for confidence distribution drift

Usage:
    Called periodically (via cron, Celery beat, or manual endpoint) to check
    whether the model's prediction patterns have changed significantly.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
from scipy.stats import chisquare, ks_2samp
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction


async def check_class_drift(
    session: AsyncSession,
    window_days: int = 7,
    significance: float = 0.05,
) -> dict:
    """
    Chi-squared test on class distribution.

    Compares the distribution of predicted classes in the recent window
    against the historical baseline (all data before the window).

    Returns:
        Dict with drift_detected, p_value, chi2_statistic, and metadata.
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    # Recent distribution
    recent_result = await session.execute(
        select(Prediction.predicted_class, func.count())
        .where(Prediction.created_at >= cutoff)
        .group_by(Prediction.predicted_class)
    )
    recent_counts = dict(recent_result.all())

    # Baseline distribution (all data before window)
    baseline_result = await session.execute(
        select(Prediction.predicted_class, func.count())
        .where(Prediction.created_at < cutoff)
        .group_by(Prediction.predicted_class)
    )
    baseline_counts = dict(baseline_result.all())

    if not baseline_counts or not recent_counts:
        return {"drift_detected": False, "reason": "insufficient_data"}

    total_recent = sum(recent_counts.values())
    total_baseline = sum(baseline_counts.values())

    if total_recent < 10 or total_baseline < 20:
        return {"drift_detected": False, "reason": "insufficient_samples"}

    # Align classes (both must have same keys)
    all_classes = sorted(set(list(recent_counts.keys()) + list(baseline_counts.keys())))
    observed = np.array([recent_counts.get(c, 0) for c in all_classes], dtype=float)
    expected_raw = np.array([baseline_counts.get(c, 0) for c in all_classes], dtype=float)

    # Normalize expected to same total as observed
    expected = expected_raw * (total_recent / total_baseline)

    # Avoid division by zero
    if np.any(expected == 0):
        expected = expected + 1e-10

    stat, p_value = chisquare(observed, expected)

    return {
        "drift_detected": p_value < significance,
        "test": "chi-squared",
        "p_value": float(p_value),
        "chi2_statistic": float(stat),
        "significance_level": significance,
        "window_days": window_days,
        "recent_total": total_recent,
        "baseline_total": total_baseline,
        "recent_distribution": {str(k): v for k, v in recent_counts.items()},
        "baseline_distribution": {str(k): v for k, v in baseline_counts.items()},
    }


async def check_confidence_drift(
    session: AsyncSession,
    window_days: int = 7,
    significance: float = 0.05,
) -> dict:
    """
    Kolmogorov-Smirnov test on confidence distribution.

    Compares confidence values from recent predictions against baseline.

    Returns:
        Dict with drift_detected, p_value, ks_statistic, and metadata.
    """
    cutoff = datetime.utcnow() - timedelta(days=window_days)

    recent_result = await session.execute(
        select(Prediction.confidence).where(Prediction.created_at >= cutoff)
    )
    recent_vals = [row[0] for row in recent_result.all()]

    baseline_result = await session.execute(
        select(Prediction.confidence).where(Prediction.created_at < cutoff)
    )
    baseline_vals = [row[0] for row in baseline_result.all()]

    if len(recent_vals) < 10 or len(baseline_vals) < 10:
        return {"drift_detected": False, "reason": "insufficient_samples"}

    stat, p_value = ks_2samp(recent_vals, baseline_vals)

    return {
        "drift_detected": p_value < significance,
        "test": "kolmogorov-smirnov",
        "p_value": float(p_value),
        "ks_statistic": float(stat),
        "significance_level": significance,
        "window_days": window_days,
        "recent_mean_confidence": float(np.mean(recent_vals)),
        "recent_std_confidence": float(np.std(recent_vals)),
        "baseline_mean_confidence": float(np.mean(baseline_vals)),
        "baseline_std_confidence": float(np.std(baseline_vals)),
        "recent_n": len(recent_vals),
        "baseline_n": len(baseline_vals),
    }


async def check_all_drift(
    session: AsyncSession,
    window_days: int = 7,
) -> dict:
    """Run all drift checks and return combined report."""
    class_drift = await check_class_drift(session, window_days)
    confidence_drift = await check_confidence_drift(session, window_days)

    any_drift = class_drift.get("drift_detected", False) or confidence_drift.get(
        "drift_detected", False
    )

    return {
        "any_drift_detected": any_drift,
        "checked_at": datetime.utcnow().isoformat(),
        "window_days": window_days,
        "class_distribution": class_drift,
        "confidence_distribution": confidence_drift,
    }

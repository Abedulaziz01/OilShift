from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


EPSILON = 1e-8


@dataclass
class DetectionResult:
    method: str
    change_points: pd.DataFrame
    metadata: dict


def _gaussian_log_likelihood(values: np.ndarray) -> float:
    if len(values) < 2:
        return float("-inf")
    variance = float(np.var(values, ddof=1))
    variance = max(variance, EPSILON)
    return float(-0.5 * len(values) * (np.log(2 * np.pi * variance) + 1))


def _best_split(values: np.ndarray, min_segment: int) -> tuple[int | None, float]:
    if len(values) < min_segment * 2:
        return None, 0.0

    base_score = _gaussian_log_likelihood(values)
    best_gain = 0.0
    best_index = None

    for candidate in range(min_segment, len(values) - min_segment + 1):
        left = values[:candidate]
        right = values[candidate:]
        gain = _gaussian_log_likelihood(left) + _gaussian_log_likelihood(right) - base_score
        if gain > best_gain:
            best_gain = gain
            best_index = candidate

    return best_index, best_gain


def _binary_segmentation(
    values: np.ndarray,
    min_segment: int,
    max_change_points: int,
    penalty_scale: float,
) -> list[tuple[int, float]]:
    change_points: list[tuple[int, float]] = []

    def recurse(start: int, end: int) -> None:
        if len(change_points) >= max_change_points:
            return

        window = values[start:end]
        best_index, gain = _best_split(window, min_segment=min_segment)
        if best_index is None:
            return

        penalty = penalty_scale * np.log(max(len(window), 2))
        if gain <= penalty:
            return

        absolute_index = start + best_index
        change_points.append((absolute_index, gain))
        recurse(start, absolute_index)
        recurse(absolute_index, end)

    recurse(0, len(values))
    return sorted(change_points, key=lambda item: item[0])


def detect_change_points(
    price_df: pd.DataFrame,
    min_segment: int = 90,
    max_change_points: int = 4,
    penalty_scale: float = 3.0,
) -> DetectionResult:
    """Detect structural breaks on log returns using Gaussian likelihood segmentation."""
    returns = price_df.dropna(subset=["Log_Return"]).reset_index(drop=True)
    values = returns["Log_Return"].to_numpy()

    raw_change_points = _binary_segmentation(
        values=values,
        min_segment=min_segment,
        max_change_points=max_change_points,
        penalty_scale=penalty_scale,
    )

    rows = []
    for index, score in raw_change_points:
        change_date = returns.loc[index, "Date"]
        before_returns = values[:index]
        after_returns = values[index:]
        price_before = price_df.loc[price_df["Date"] < change_date, "Price"].tail(30)
        price_after = price_df.loc[price_df["Date"] >= change_date, "Price"].head(30)

        rows.append(
            {
                "change_index": int(index),
                "change_date": pd.Timestamp(change_date),
                "score": round(float(score), 3),
                "return_mean_before": float(np.mean(before_returns)) if len(before_returns) else np.nan,
                "return_mean_after": float(np.mean(after_returns)) if len(after_returns) else np.nan,
                "return_vol_before": float(np.std(before_returns, ddof=1)) if len(before_returns) > 1 else np.nan,
                "return_vol_after": float(np.std(after_returns, ddof=1)) if len(after_returns) > 1 else np.nan,
                "avg_price_before_30d": float(price_before.mean()) if not price_before.empty else np.nan,
                "avg_price_after_30d": float(price_after.mean()) if not price_after.empty else np.nan,
            }
        )

    change_points = pd.DataFrame(rows)
    if not change_points.empty:
        change_points["avg_price_shift_pct"] = (
            (change_points["avg_price_after_30d"] - change_points["avg_price_before_30d"])
            / change_points["avg_price_before_30d"]
            * 100
        )

    return DetectionResult(
        method="offline_gaussian_segmentation",
        change_points=change_points,
        metadata={"min_segment": min_segment, "max_change_points": max_change_points},
    )


def detect_single_change_point_bayesian(price_df: pd.DataFrame) -> DetectionResult | None:
    """Optional PyMC-based single change point model."""
    try:
        import pymc as pm
        import pytensor.tensor as pt
    except ImportError:
        return None

    returns = price_df.dropna(subset=["Log_Return"]).reset_index(drop=True)
    values = returns["Log_Return"].to_numpy()
    if len(values) < 20:
        return None

    with pm.Model() as model:
        tau = pm.DiscreteUniform("tau", lower=5, upper=len(values) - 5)
        mu_1 = pm.Normal("mu_1", mu=0.0, sigma=0.05)
        mu_2 = pm.Normal("mu_2", mu=0.0, sigma=0.05)
        sigma = pm.Exponential("sigma", 50.0)
        index = pt.arange(len(values))
        mu = pm.math.switch(index < tau, mu_1, mu_2)
        pm.Normal("observed", mu=mu, sigma=sigma, observed=values)
        trace = pm.sample(
            draws=600,
            tune=600,
            chains=2,
            target_accept=0.9,
            progressbar=False,
            compute_convergence_checks=False,
        )

    tau_samples = np.asarray(trace.posterior["tau"]).ravel().astype(int)
    best_index = int(pd.Series(tau_samples).mode().iloc[0])
    change_date = returns.loc[best_index, "Date"]
    before_returns = values[:best_index]
    after_returns = values[best_index:]
    price_before = price_df.loc[price_df["Date"] < change_date, "Price"].tail(30)
    price_after = price_df.loc[price_df["Date"] >= change_date, "Price"].head(30)

    change_points = pd.DataFrame(
        [
            {
                "change_index": best_index,
                "change_date": pd.Timestamp(change_date),
                "posterior_mass": float((tau_samples == best_index).mean()),
                "return_mean_before": float(np.mean(before_returns)) if len(before_returns) else np.nan,
                "return_mean_after": float(np.mean(after_returns)) if len(after_returns) else np.nan,
                "return_vol_before": float(np.std(before_returns, ddof=1)) if len(before_returns) > 1 else np.nan,
                "return_vol_after": float(np.std(after_returns, ddof=1)) if len(after_returns) > 1 else np.nan,
                "avg_price_before_30d": float(price_before.mean()) if not price_before.empty else np.nan,
                "avg_price_after_30d": float(price_after.mean()) if not price_after.empty else np.nan,
            }
        ]
    )
    change_points["avg_price_shift_pct"] = (
        (change_points["avg_price_after_30d"] - change_points["avg_price_before_30d"])
        / change_points["avg_price_before_30d"]
        * 100
    )

    return DetectionResult(
        method="pymc_single_change_point",
        change_points=change_points,
        metadata={"posterior_mode_index": best_index},
    )

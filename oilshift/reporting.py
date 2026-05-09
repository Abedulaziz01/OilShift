from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

from .change_point import detect_change_points, detect_single_change_point_bayesian


def _adf_result(series: pd.Series, label: str) -> dict:
    clean = series.dropna()
    if len(clean) < 10:
        return {"series": label, "adf_statistic": np.nan, "p_value": np.nan, "stationary": False}

    statistic, p_value, *_ = adfuller(clean)
    return {
        "series": label,
        "adf_statistic": round(float(statistic), 4),
        "p_value": round(float(p_value), 6),
        "stationary": bool(p_value < 0.05),
    }


def stationarity_summary(price_df: pd.DataFrame) -> list[dict]:
    return [
        _adf_result(price_df["Price"], "Price"),
        _adf_result(price_df["Log_Return"], "Log Return"),
    ]


def build_event_impact_table(price_df: pd.DataFrame, events_df: pd.DataFrame, window_days: int = 30) -> pd.DataFrame:
    rows = []
    for _, event in events_df.iterrows():
        event_date = event["event_date"]
        before = price_df[
            (price_df["Date"] < event_date)
            & (price_df["Date"] >= event_date - pd.Timedelta(days=window_days))
        ]
        after = price_df[
            (price_df["Date"] >= event_date)
            & (price_df["Date"] <= event_date + pd.Timedelta(days=window_days))
        ]

        avg_price_before = float(before["Price"].mean()) if not before.empty else np.nan
        avg_price_after = float(after["Price"].mean()) if not after.empty else np.nan
        vol_before = float(before["Log_Return"].std()) if len(before) > 1 else np.nan
        vol_after = float(after["Log_Return"].std()) if len(after) > 1 else np.nan
        price_change_pct = (
            ((avg_price_after - avg_price_before) / avg_price_before) * 100
            if pd.notna(avg_price_before) and avg_price_before != 0 and pd.notna(avg_price_after)
            else np.nan
        )

        rows.append(
            {
                "event_date": event_date,
                "event_name": event["event_name"],
                "category": event["category"],
                "region": event["region"],
                "avg_price_before": avg_price_before,
                "avg_price_after": avg_price_after,
                "price_change_pct": price_change_pct,
                "volatility_before": vol_before,
                "volatility_after": vol_after,
                "description": event["description"],
            }
        )

    return pd.DataFrame(rows)


def associate_change_points(
    change_points_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tolerance_days: int = 45,
) -> pd.DataFrame:
    if change_points_df.empty:
        return pd.DataFrame(
            columns=[
                "change_date",
                "event_name",
                "event_date",
                "days_apart",
                "category",
                "description",
            ]
        )

    rows = []
    for _, change_point in change_points_df.iterrows():
        deltas = (events_df["event_date"] - change_point["change_date"]).abs().dt.days
        closest_index = deltas.idxmin()
        distance = int(deltas.loc[closest_index])
        if distance <= tolerance_days:
            event = events_df.loc[closest_index]
            rows.append(
                {
                    "change_date": change_point["change_date"],
                    "event_name": event["event_name"],
                    "event_date": event["event_date"],
                    "days_apart": distance,
                    "category": event["category"],
                    "description": event["description"],
                }
            )

    return pd.DataFrame(rows)


def build_summary(price_df: pd.DataFrame, change_points_df: pd.DataFrame, detection_method: str) -> dict:
    return {
        "observations": int(len(price_df)),
        "start_date": price_df["Date"].min().strftime("%Y-%m-%d"),
        "end_date": price_df["Date"].max().strftime("%Y-%m-%d"),
        "mean_price": float(price_df["Price"].mean()),
        "median_price": float(price_df["Price"].median()),
        "latest_price": float(price_df["Price"].iloc[-1]),
        "change_point_count": int(len(change_points_df)),
        "detection_method": detection_method,
    }


def build_export_summary(price_df: pd.DataFrame, stationarity: list[dict], change_points_df: pd.DataFrame) -> dict:
    price_stationarity = next(item for item in stationarity if item["series"] == "Price")
    return_stationarity = next(item for item in stationarity if item["series"] == "Log Return")
    return {
        "Mean Price": round(float(price_df["Price"].mean()), 4),
        "Std Price": round(float(price_df["Price"].std()), 4),
        "Min Price": round(float(price_df["Price"].min()), 4),
        "Max Price": round(float(price_df["Price"].max()), 4),
        "Mean Log Return": round(float(price_df["Log_Return"].mean()), 6),
        "Std Log Return": round(float(price_df["Log_Return"].std()), 6),
        "Rows After Cleaning": int(len(price_df)),
        "Price ADF p-value": price_stationarity["p_value"],
        "Return ADF p-value": return_stationarity["p_value"],
        "Detected Change Points": int(len(change_points_df)),
    }


def run_analysis(
    price_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tolerance_days: int = 45,
    max_change_points: int = 4,
    min_segment: int = 90,
    prefer_bayesian: bool = False,
) -> dict:
    stationarity = stationarity_summary(price_df)
    detection_result = None
    if prefer_bayesian:
        detection_result = detect_single_change_point_bayesian(price_df)

    if detection_result is None:
        detection_result = detect_change_points(
            price_df=price_df,
            min_segment=min_segment,
            max_change_points=max_change_points,
        )

    change_points_df = detection_result.change_points.copy()
    associations_df = associate_change_points(
        change_points_df=change_points_df,
        events_df=events_df,
        tolerance_days=tolerance_days,
    )
    event_impacts_df = build_event_impact_table(price_df=price_df, events_df=events_df)
    export_summary = build_export_summary(price_df, stationarity, change_points_df)
    summary = build_summary(price_df, change_points_df, detection_result.method)

    return {
        "summary": summary,
        "stationarity": stationarity,
        "change_points": change_points_df,
        "associations": associations_df,
        "event_impacts": event_impacts_df,
        "export_summary": export_summary,
    }


def export_analysis_bundle(analysis: dict, output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    analysis["change_points"].to_csv(output_path / "change_points.csv", index=False)
    analysis["associations"].to_csv(output_path / "change_point_event_matches.csv", index=False)
    analysis["event_impacts"].to_csv(output_path / "event_impacts.csv", index=False)
    pd.DataFrame(
        {"Metric": list(analysis["export_summary"].keys()), "Value": list(analysis["export_summary"].values())}
    ).to_csv(output_path / "summary_table.csv", index=False)

    with open(output_path / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(analysis["summary"], handle, indent=2)

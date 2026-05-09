from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid")


def _save_plot(figure: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_raw_price_trend(price_df: pd.DataFrame, output_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(price_df["Date"], price_df["Price"], color="#9a3412", linewidth=2)
    ax.set_title("Brent Crude Price Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("USD per barrel")
    _save_plot(fig, Path(output_path))


def save_log_returns_plot(price_df: pd.DataFrame, output_path: str | Path) -> None:
    returns = price_df.dropna(subset=["Log_Return"])
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(returns["Date"], returns["Log_Return"], color="#1d4ed8", linewidth=1.1)
    ax.set_title("Daily Log Returns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Log return")
    _save_plot(fig, Path(output_path))


def save_volatility_plot(price_df: pd.DataFrame, output_path: str | Path) -> None:
    volatility = price_df.dropna(subset=["RollingVolatility30D"])
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(volatility["Date"], volatility["RollingVolatility30D"], color="#0f766e", linewidth=1.8)
    ax.set_title("30-Day Rolling Volatility")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized volatility")
    _save_plot(fig, Path(output_path))


def save_price_with_events_plot(
    price_df: pd.DataFrame,
    events_df: pd.DataFrame,
    output_path: str | Path,
    max_events: int = 12,
) -> None:
    fig, ax = plt.subplots(figsize=(13, 5.6))
    ax.plot(price_df["Date"], price_df["Price"], color="#7c2d12", linewidth=2, alpha=0.95)

    plotted = 0
    for _, event in events_df.iterrows():
        if plotted >= max_events:
            break
        event_date = event["event_date"]
        if event_date < price_df["Date"].min() or event_date > price_df["Date"].max():
            continue
        nearest_index = (price_df["Date"] - event_date).abs().idxmin()
        y_value = price_df.loc[nearest_index, "Price"]
        ax.axvline(event_date, color="#2563eb", linestyle="--", alpha=0.22, linewidth=1.2)
        ax.scatter([event_date], [y_value], color="#1d4ed8", s=28, zorder=3)
        ax.text(event_date, y_value, f" {event['event_name']}", fontsize=8, rotation=25, va="bottom")
        plotted += 1

    ax.set_title("Brent Prices with Key Events")
    ax.set_xlabel("Date")
    ax.set_ylabel("USD per barrel")
    _save_plot(fig, Path(output_path))


def export_visualizations(price_df: pd.DataFrame, events_df: pd.DataFrame, output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    save_raw_price_trend(price_df, output_path / "raw_price_trend.png")
    save_log_returns_plot(price_df, output_path / "log_returns.png")
    save_volatility_plot(price_df, output_path / "volatility.png")
    save_price_with_events_plot(price_df, events_df, output_path / "price_with_events.png")

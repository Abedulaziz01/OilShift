from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "data" / "events" / "key_events.csv"
DEFAULT_PRICE_CANDIDATES = (
    PROJECT_ROOT / "data" / "raw" / "BrentOilPrices.csv",
    PROJECT_ROOT / "data" / "raw" / "brent_oil_prices.csv",
)


def locate_default_price_data() -> Path | None:
    """Return the first raw Brent oil CSV found in the expected project locations."""
    for candidate in DEFAULT_PRICE_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for column in frame.columns:
        normalized = column.strip().lower().replace(" ", "_")
        if normalized == "date":
            renamed[column] = "Date"
        elif normalized == "price":
            renamed[column] = "Price"
        elif normalized in {"event_date", "event"}:
            renamed[column] = "event_date"
        elif normalized in {"event_name", "name"}:
            renamed[column] = "event_name"
        elif normalized == "category":
            renamed[column] = "category"
        elif normalized == "description":
            renamed[column] = "description"
        elif normalized == "region":
            renamed[column] = "region"
    return frame.rename(columns=renamed)


def _parse_mixed_dates(values: Iterable[object]) -> pd.Series:
    series = pd.Series(values, copy=True).astype(str).str.strip()
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    known_formats = ("%d-%b-%y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d")

    for date_format in known_formats:
        missing = parsed.isna()
        if not missing.any():
            break
        parsed.loc[missing] = pd.to_datetime(
            series.loc[missing],
            errors="coerce",
            format=date_format,
        )

    missing = parsed.isna()
    if missing.any():
        parsed.loc[missing] = pd.to_datetime(series.loc[missing], errors="coerce", dayfirst=True)

    missing = parsed.isna()
    if missing.any():
        parsed.loc[missing] = pd.to_datetime(series.loc[missing], errors="coerce", yearfirst=True)
    return parsed


def parse_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate, clean, and enrich a Brent price DataFrame."""
    data = _standardize_columns(frame).copy()
    required_columns = {"Date", "Price"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    data["Date"] = _parse_mixed_dates(data["Date"])
    data["Price"] = (
        data["Price"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )
    data["Price"] = pd.to_numeric(data["Price"], errors="coerce")

    data = data.dropna(subset=["Date", "Price"]).copy()
    data = data.sort_values("Date").drop_duplicates(subset=["Date"], keep="last")
    data["Log_Return"] = np.log(data["Price"]).diff()
    data["RollingVolatility30D"] = data["Log_Return"].rolling(30).std() * np.sqrt(252)
    data["RollingMean30D"] = data["Price"].rolling(30).mean()
    return data.reset_index(drop=True)


def load_price_data(path: str | Path) -> pd.DataFrame:
    """Load Brent oil data from a CSV path."""
    frame = pd.read_csv(path)
    return parse_price_frame(frame)


def load_events(path: str | Path | None = None, frame: pd.DataFrame | None = None) -> pd.DataFrame:
    """Load the curated event table from disk or a provided DataFrame."""
    if frame is None:
        events_path = Path(path) if path is not None else DEFAULT_EVENTS_PATH
        frame = pd.read_csv(events_path)

    events = _standardize_columns(frame).copy()
    required = {"event_date", "event_name"}
    missing_columns = required.difference(events.columns)
    if missing_columns:
        raise ValueError(f"Missing required event columns: {sorted(missing_columns)}")

    events["event_date"] = _parse_mixed_dates(events["event_date"])
    optional_columns = ["category", "description", "region"]
    for column in optional_columns:
        if column not in events.columns:
            events[column] = ""

    events = events.dropna(subset=["event_date", "event_name"]).copy()
    events = events.sort_values("event_date").reset_index(drop=True)
    return events[["event_date", "event_name", "category", "description", "region"]]


def export_processed_data(price_df: pd.DataFrame, output_dir: str | Path) -> None:
    """Save cleaned price data and derived log returns."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    price_df.to_csv(output_path / "brent_oil_prices_cleaned.csv", index=False)
    price_df[["Date", "Log_Return", "RollingVolatility30D"]].to_csv(
        output_path / "log_returns.csv",
        index=False,
    )

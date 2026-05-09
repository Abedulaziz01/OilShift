from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from oilshift.data import export_processed_data, load_price_data, locate_default_price_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean Brent oil price data and compute derived metrics.")
    parser.add_argument("--price-data", type=str, default=None, help="Path to Brent oil prices CSV.")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    price_path = args.price_data or locate_default_price_data()
    if price_path is None:
        raise FileNotFoundError(
            "Brent price CSV not found. Pass --price-data or place BrentOilPrices.csv in data/raw/."
        )

    price_df = load_price_data(price_path)
    export_processed_data(price_df, args.output)
    print(f"Cleaned data written to {args.output}")


if __name__ == "__main__":
    main()

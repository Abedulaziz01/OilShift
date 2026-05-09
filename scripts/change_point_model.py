from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from oilshift.data import load_events, load_price_data, locate_default_price_data
from oilshift.reporting import export_analysis_bundle, run_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OilShift change point analysis.")
    parser.add_argument("--price-data", type=str, default=None, help="Path to Brent oil prices CSV.")
    parser.add_argument("--events", type=str, default=None, help="Path to events CSV.")
    parser.add_argument("--output", type=str, default="results/analysis", help="Output directory.")
    parser.add_argument("--prefer-bayesian", action="store_true", help="Attempt the optional PyMC model.")
    parser.add_argument("--max-change-points", type=int, default=4, help="Maximum number of change points.")
    parser.add_argument("--min-segment", type=int, default=90, help="Minimum segment length.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    price_path = args.price_data or locate_default_price_data()
    if price_path is None:
        raise FileNotFoundError(
            "Brent price CSV not found. Pass --price-data or place BrentOilPrices.csv in data/raw/."
        )

    price_df = load_price_data(price_path)
    events_df = load_events(path=args.events) if args.events else load_events()
    analysis = run_analysis(
        price_df=price_df,
        events_df=events_df,
        max_change_points=args.max_change_points,
        min_segment=args.min_segment,
        prefer_bayesian=args.prefer_bayesian,
    )
    export_analysis_bundle(analysis, args.output)
    print(f"Change point analysis written to {args.output}")


if __name__ == "__main__":
    main()

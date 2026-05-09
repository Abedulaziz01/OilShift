from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from oilshift.data import export_processed_data, load_events, load_price_data, locate_default_price_data
from oilshift.reporting import export_analysis_bundle, run_analysis
from oilshift.visualization import export_visualizations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OilShift analysis artifacts from a Brent oil CSV.")
    parser.add_argument(
        "--price-data",
        type=str,
        default=None,
        help="Path to the Brent oil price CSV. Defaults to data/raw/BrentOilPrices.csv when available.",
    )
    parser.add_argument(
        "--events",
        type=str,
        default=None,
        help="Path to a custom events CSV. Defaults to data/events/key_events.csv.",
    )
    parser.add_argument(
        "--processed-output",
        type=str,
        default="data/processed",
        help="Directory for cleaned data outputs.",
    )
    parser.add_argument(
        "--analysis-output",
        type=str,
        default="results/analysis",
        help="Directory for analysis output tables.",
    )
    parser.add_argument(
        "--plots-output",
        type=str,
        default="results/plots",
        help="Directory for plot output assets.",
    )
    parser.add_argument(
        "--prefer-bayesian",
        action="store_true",
        help="Attempt the optional PyMC single change point model before the default detector.",
    )
    parser.add_argument(
        "--max-change-points",
        type=int,
        default=4,
        help="Maximum number of change points for the default detector.",
    )
    parser.add_argument(
        "--min-segment",
        type=int,
        default=90,
        help="Minimum segment length for the default detector.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    price_path = Path(args.price_data) if args.price_data else locate_default_price_data()
    if price_path is None or not price_path.exists():
        raise FileNotFoundError(
            "Brent price CSV not found. Pass --price-data or place BrentOilPrices.csv in data/raw/."
        )

    price_df = load_price_data(price_path)
    events_df = load_events(path=args.events) if args.events else load_events()
    export_processed_data(price_df, args.processed_output)

    analysis = run_analysis(
        price_df=price_df,
        events_df=events_df,
        max_change_points=args.max_change_points,
        min_segment=args.min_segment,
        prefer_bayesian=args.prefer_bayesian,
    )
    export_analysis_bundle(analysis, args.analysis_output)
    export_visualizations(price_df, events_df, args.plots_output)
    print(f"Processed data written to {Path(args.processed_output).resolve()}")
    print(f"Analysis outputs written to {Path(args.analysis_output).resolve()}")
    print(f"Plot assets written to {Path(args.plots_output).resolve()}")


if __name__ == "__main__":
    main()

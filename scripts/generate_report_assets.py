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
    parser = argparse.ArgumentParser(description="Generate OilShift report tables and plot assets from Python.")
    parser.add_argument("--price-data", type=str, default=None, help="Path to Brent oil prices CSV.")
    parser.add_argument("--events", type=str, default=None, help="Path to events CSV.")
    parser.add_argument("--processed-output", type=str, default="data/processed", help="Processed data output.")
    parser.add_argument("--analysis-output", type=str, default="results/analysis", help="Analysis table output.")
    parser.add_argument("--plots-output", type=str, default="results/plots", help="Plot output directory.")
    parser.add_argument(
        "--summary-output",
        type=str,
        default="results/summary_table.csv",
        help="Summary table CSV output path.",
    )
    parser.add_argument("--max-change-points", type=int, default=4, help="Maximum change points.")
    parser.add_argument("--min-segment", type=int, default=90, help="Minimum segment length.")
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
    )
    export_analysis_bundle(analysis, args.analysis_output)
    export_visualizations(price_df, events_df, args.plots_output)

    summary_output = Path(args.summary_output)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    analysis_summary = analysis["export_summary"]
    import pandas as pd

    pd.DataFrame({"Metric": list(analysis_summary.keys()), "Value": list(analysis_summary.values())}).to_csv(
        summary_output,
        index=False,
    )
    print(f"Report assets written to {Path(args.plots_output).resolve()}")


if __name__ == "__main__":
    main()

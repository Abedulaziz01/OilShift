from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from oilshift.data import (
    DEFAULT_EVENTS_PATH,
    locate_default_price_data,
    load_events,
    load_price_data,
    parse_price_frame,
)
from oilshift.reporting import run_analysis


st.set_page_config(
    page_title="OilShift Pro",
    page_icon="O",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 213, 128, 0.35), transparent 30%),
            radial-gradient(circle at top right, rgba(37, 99, 235, 0.14), transparent 28%),
            linear-gradient(180deg, #f8f5ef 0%, #fffdf9 48%, #f3f0ea 100%);
        color: #172033;
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2rem;
    }
    .hero-card {
        padding: 1.4rem 1.5rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(18, 24, 38, 0.94), rgba(70, 33, 10, 0.88));
        color: #f7f1e8;
        box-shadow: 0 20px 40px rgba(41, 32, 18, 0.12);
        margin-bottom: 1rem;
    }
    .hero-kicker {
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.78rem;
        opacity: 0.8;
        margin-bottom: 0.4rem;
    }
    .hero-title {
        font-size: 2.1rem;
        line-height: 1.05;
        margin-bottom: 0.55rem;
        font-family: Georgia, "Times New Roman", serif;
    }
    .hero-copy {
        font-size: 1rem;
        max-width: 52rem;
        color: rgba(247, 241, 232, 0.86);
    }
    .section-note {
        padding: 0.9rem 1rem;
        border-radius: 16px;
        border: 1px solid rgba(140, 120, 84, 0.22);
        background: rgba(255, 250, 242, 0.7);
        margin-bottom: 1rem;
    }
</style>
"""


@st.cache_data(show_spinner=False)
def load_price_from_upload(uploaded_file) -> pd.DataFrame:
    frame = pd.read_csv(uploaded_file)
    return parse_price_frame(frame)


@st.cache_data(show_spinner=False)
def load_events_from_upload(uploaded_file) -> pd.DataFrame:
    frame = pd.read_csv(uploaded_file)
    frame.columns = [column.strip() for column in frame.columns]
    return load_events(frame=frame)


def render_hero() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Brent Crude Intelligence</div>
            <div class="hero-title">OilShift Pro</div>
            <div class="hero-copy">
                Detect structural breaks in Brent oil prices, compare them with major geopolitical and market events,
                and communicate the findings through an analyst-friendly dashboard.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_row(summary: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Observations", f"{summary['observations']:,}")
    col2.metric("Date Range", f"{summary['start_date']} to {summary['end_date']}")
    col3.metric("Mean Price", f"${summary['mean_price']:.2f}")
    col4.metric("Detected Breaks", str(summary["change_point_count"]))


def build_price_figure(price_df: pd.DataFrame, events_df: pd.DataFrame) -> go.Figure:
    figure = px.line(
        price_df,
        x="Date",
        y="Price",
        template="plotly_white",
        title="Brent Crude Price History",
        labels={"Price": "USD per barrel"},
    )
    figure.update_traces(line=dict(color="#b45309", width=2.5))

    marker_events = events_df.head(12).copy()
    merged = pd.merge_asof(
        marker_events.sort_values("event_date"),
        price_df[["Date", "Price"]].sort_values("Date"),
        left_on="event_date",
        right_on="Date",
        direction="nearest",
    )
    figure.add_trace(
        go.Scatter(
            x=merged["event_date"],
            y=merged["Price"],
            mode="markers",
            marker=dict(size=9, color="#1d4ed8", line=dict(color="#ffffff", width=1)),
            name="Key events",
            text=merged["event_name"],
            hovertemplate="%{text}<br>%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>",
        )
    )
    figure.update_layout(height=440, margin=dict(l=10, r=10, t=50, b=10))
    return figure


def build_volatility_figure(price_df: pd.DataFrame) -> go.Figure:
    volatility = price_df.dropna(subset=["RollingVolatility30D"])
    figure = px.line(
        volatility,
        x="Date",
        y="RollingVolatility30D",
        template="plotly_white",
        title="30-Day Rolling Volatility of Log Returns",
        labels={"RollingVolatility30D": "Annualized volatility"},
    )
    figure.update_traces(line=dict(color="#0f766e", width=2.2))
    figure.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
    return figure


def build_change_point_figure(price_df: pd.DataFrame, change_points_df: pd.DataFrame) -> go.Figure:
    figure = px.line(
        price_df,
        x="Date",
        y="Price",
        template="plotly_white",
        title="Detected Structural Shifts Against the Price Series",
        labels={"Price": "USD per barrel"},
    )
    figure.update_traces(line=dict(color="#7c3aed", width=2.2))

    for _, row in change_points_df.iterrows():
        figure.add_vline(
            x=row["change_date"],
            line_width=1.5,
            line_dash="dash",
            line_color="#b91c1c",
            annotation_text=row["change_date"].strftime("%Y-%m-%d"),
            annotation_position="top left",
        )

    figure.update_layout(height=430, margin=dict(l=10, r=10, t=50, b=10))
    return figure


def build_event_window_figure(price_df: pd.DataFrame, event_row: pd.Series, window_days: int = 60) -> go.Figure:
    event_date = event_row["event_date"]
    window = price_df[
        (price_df["Date"] >= event_date - pd.Timedelta(days=window_days))
        & (price_df["Date"] <= event_date + pd.Timedelta(days=window_days))
    ].copy()
    figure = px.line(
        window,
        x="Date",
        y="Price",
        template="plotly_white",
        title=f"Price Window Around {event_row['event_name']}",
        labels={"Price": "USD per barrel"},
    )
    figure.update_traces(line=dict(color="#92400e", width=2.5))
    figure.add_vline(x=event_date, line_width=2, line_dash="dash", line_color="#0f172a")
    figure.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
    return figure


def show_data_requirements() -> None:
    st.info(
        "No local Brent price file was found. Upload a CSV with `Date` and `Price` columns from the sidebar, "
        "or place `BrentOilPrices.csv` under `data/raw/`."
    )
    st.markdown(
        """
        <div class="section-note">
            <strong>Expected schema</strong><br/>
            Date: daily observation date<br/>
            Price: Brent crude oil price in USD per barrel
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    render_hero()

    with st.sidebar:
        st.header("Data Controls")
        default_path = locate_default_price_data()
        uploaded_price = st.file_uploader("Upload Brent price CSV", type=["csv"])
        uploaded_events = st.file_uploader("Upload custom events CSV", type=["csv"])
        tolerance_days = st.slider("Event matching tolerance (days)", 7, 120, 45, 1)
        max_change_points = st.slider("Max change points", 1, 8, 4, 1)
        min_segment = st.slider("Minimum segment length", 20, 365, 90, 5)
        use_bayesian = st.checkbox(
            "Attempt PyMC single change point model",
            value=False,
            help="Only works when `pymc` is installed locally.",
        )

        if default_path:
            st.caption(f"Using local default when no upload is provided: `{default_path}`")
        else:
            st.caption("No local raw price file detected.")

        if Path(DEFAULT_EVENTS_PATH).exists():
            st.caption(f"Bundled events file: `{DEFAULT_EVENTS_PATH}`")

    if uploaded_price is not None:
        price_df = load_price_from_upload(uploaded_price)
    elif default_path is not None:
        price_df = load_price_data(default_path)
    else:
        show_data_requirements()
        return

    if uploaded_events is not None:
        events_df = load_events_from_upload(uploaded_events)
    else:
        events_df = load_events()

    analysis = run_analysis(
        price_df=price_df,
        events_df=events_df,
        tolerance_days=tolerance_days,
        max_change_points=max_change_points,
        min_segment=min_segment,
        prefer_bayesian=use_bayesian,
    )

    render_metric_row(analysis["summary"])
    st.caption(
        f"Detection method: `{analysis['summary']['detection_method']}`. "
        "Structural breaks are identified on log returns, while event impacts are reported on price levels."
    )

    tab_overview, tab_changes, tab_events, tab_notes = st.tabs(
        ["Overview", "Change Points", "Event Explorer", "Method Notes"]
    )

    with tab_overview:
        st.plotly_chart(build_price_figure(price_df, events_df), use_container_width=True)
        left, right = st.columns([1.35, 1])
        with left:
            st.plotly_chart(build_volatility_figure(price_df), use_container_width=True)
        with right:
            stationarity = pd.DataFrame(analysis["stationarity"])
            st.subheader("Stationarity Check")
            st.dataframe(stationarity, use_container_width=True, hide_index=True)
            st.subheader("Core Metrics")
            summary_frame = pd.DataFrame(
                {
                    "Metric": list(analysis["export_summary"].keys()),
                    "Value": list(analysis["export_summary"].values()),
                }
            )
            st.dataframe(summary_frame, use_container_width=True, hide_index=True)

    with tab_changes:
        change_points_df = analysis["change_points"]
        if change_points_df.empty:
            st.warning("No statistically meaningful change points were detected with the current settings.")
        else:
            st.plotly_chart(build_change_point_figure(price_df, change_points_df), use_container_width=True)
            st.dataframe(change_points_df, use_container_width=True, hide_index=True)
            if not analysis["associations"].empty:
                st.subheader("Matched Event Hypotheses")
                st.dataframe(analysis["associations"], use_container_width=True, hide_index=True)

    with tab_events:
        event_impacts = analysis["event_impacts"]
        event_names = event_impacts["event_name"].tolist()
        if not event_names:
            st.warning("No event impact rows are available for the current dataset.")
        else:
            selected_name = st.selectbox("Select an event", event_names, index=0)
            if selected_name:
                selected_event = events_df.loc[events_df["event_name"] == selected_name].iloc[0]
                selected_impact = event_impacts.loc[event_impacts["event_name"] == selected_name].iloc[0]
                st.plotly_chart(build_event_window_figure(price_df, selected_event), use_container_width=True)
                c1, c2, c3 = st.columns(3)
                c1.metric("Avg price before", f"${selected_impact['avg_price_before']:.2f}")
                c2.metric("Avg price after", f"${selected_impact['avg_price_after']:.2f}")
                c3.metric("Price shift", f"{selected_impact['price_change_pct']:.2f}%")
                st.dataframe(
                    pd.DataFrame([selected_impact]),
                    use_container_width=True,
                    hide_index=True,
                )

    with tab_notes:
        st.markdown(
            """
            ### Interpretation Guide

            - Change points reveal structural shifts in the statistical behavior of the series, not guaranteed causal proof.
            - Event matches are hypothesis-generating links based on proximity in time to the detected shift.
            - Brent price levels are generally non-stationary, which is why the detector operates on log returns.
            - Use the dashboard to support analyst judgment, not to replace contextual market interpretation.
            """
        )
        st.markdown(
            """
            ### Suggested Stakeholder Channels

            - Interactive Streamlit dashboard for executives and analysts.
            - CSV exports for research, reporting, and follow-on modelling.
            - Written report or slide deck for policy and investment audiences.
            """
        )


if __name__ == "__main__":
    main()

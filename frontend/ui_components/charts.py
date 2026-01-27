import logging
from typing import List, Dict, Any, Optional

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------
# Logger setup
# --------------------------------------------------
logger = logging.getLogger(__name__)


# ==================================================
# NEW API (what debug_mode.py expects)
# ==================================================
def render_latency_trend(
    traces: List[Dict[str, Any]],
    title: str = "Latency Trend (ms)",
) -> go.Figure:
    """
    Builds a line chart of latency over time/index.

    Expected trace keys:
      - created_at (str) [optional]
      - latency_ms (int)

    Returns:
      - Plotly Figure (caller decides how to display it)
    """
    try:
        if not traces:
            logger.info("render_latency_trend: no traces provided")
            return go.Figure()

        rows = [
            {
                "created_at": t.get("created_at", "unknown"),
                "latency_ms": int(t.get("latency_ms", 0)),
            }
            for t in traces
        ]

        fig = px.line(
            rows,
            x="created_at",
            y="latency_ms",
            markers=True,
            title=title,
        )
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            template="plotly_white",
            height=320,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    except Exception:
        logger.exception("render_latency_trend failed")
        return go.Figure()


def render_cost_distribution(
    traces: List[Dict[str, Any]],
    title: str = "Cost Distribution ($)",
) -> go.Figure:
    """
    Builds a histogram chart of cost across traces.

    Expected trace keys:
      - cost_usd (float)
    """
    try:
        if not traces:
            logger.info("render_cost_distribution: no traces provided")
            return go.Figure()

        costs = [float(t.get("cost_usd", 0.0)) for t in traces]

        fig = px.histogram(
            x=costs,
            nbins=12,
            title=title,
        )
        fig.update_layout(
            xaxis_title="Cost ($)",
            yaxis_title="Count",
            template="plotly_white",
            height=320,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    except Exception:
        logger.exception("render_cost_distribution failed")
        return go.Figure()


def render_latency_waterfall(
    steps: List[Dict[str, Any]],
    title: str = "Latency Waterfall (ms)",
    show_total: bool = True,
) -> go.Figure:
    """
    Builds a bar chart for step-level latency.

    Expected step keys:
      - name (str)
      - ms (int)

    Returns:
      - Plotly Figure
    """
    try:
        if not steps:
            logger.info("render_latency_waterfall: no steps provided")
            return go.Figure()

        names = [str(s.get("name", "unknown")) for s in steps]
        values = [int(s.get("ms", 0)) for s in steps]
        total = sum(values)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=names,
                y=values,
                name="Step latency",
                marker_color="#4C78A8",
            )
        )

        if show_total:
            fig.add_hline(y=total, line_dash="dot", line_color="gray")
            fig.add_annotation(
                x=names[-1] if names else 0,
                y=total,
                text=f"Total: {total} ms",
                showarrow=False,
                yshift=10,
            )

        fig.update_layout(
            title=title,
            xaxis_title="Step",
            yaxis_title="Latency (ms)",
            template="plotly_white",
            height=320,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    except Exception:
        logger.exception("render_latency_waterfall failed")
        return go.Figure()


# ==================================================
# OLD API (kept for compatibility)
# These render directly to Streamlit.
# ==================================================
def render_latency_chart(latencies_ms: List[int]) -> None:
    """
    Backward-compatible: renders latency chart directly in Streamlit.

    Prefer using render_latency_trend() in new pages.
    """
    try:
        if not latencies_ms:
            st.info("No latency data available.")
            return

        logger.info("Rendering latency chart (legacy)")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=latencies_ms,
                mode="lines+markers",
                name="Latency (ms)",
            )
        )
        fig.update_layout(
            title="Latency Trend",
            xaxis_title="Request Index",
            yaxis_title="Latency (ms)",
            template="plotly_white",
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception:
        logger.exception("Failed to render latency chart (legacy)")
        st.error("Error rendering latency chart")
        st.exception(Exception("Latency chart render failed"))


def render_cost_chart(costs_usd: List[float]) -> None:
    """
    Backward-compatible: renders cost chart directly in Streamlit.

    Prefer using render_cost_distribution() in new pages.
    """
    try:
        if not costs_usd:
            st.info("No cost data available.")
            return

        logger.info("Rendering cost chart (legacy)")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=costs_usd,
                name="Cost ($)",
            )
        )
        fig.update_layout(
            title="Cost per Request",
            xaxis_title="Request Index",
            yaxis_title="Cost (USD)",
            template="plotly_white",
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception:
        logger.exception("Failed to render cost chart (legacy)")
        st.error("Error rendering cost chart")
        st.exception(Exception("Cost chart render failed"))

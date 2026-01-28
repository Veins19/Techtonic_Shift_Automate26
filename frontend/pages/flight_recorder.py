import logging
from typing import Dict, Any, Optional

import streamlit as st
import requests

from ui_components.charts import render_latency_waterfall
from ui_components.trace_viewer import render_trace_viewer

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


@st.cache_data(ttl=30)
def fetch_traces_list(page: int = 1, limit: int = 20) -> Optional[Dict[str, Any]]:
    """Fetch list of traces from backend API. Cached for 30 seconds."""
    try:
        logger.info(f"Fetching traces list from backend: page={page}, limit={limit}")
        response = requests.get(
            f"{BACKEND_URL}/traces",
            params={"page": page, "limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched {len(data.get('items', []))} traces")
        return data
    except requests.exceptions.ConnectionError:
        logger.warning("Backend connection failed - using mock data")
        return None
    except Exception as e:
        logger.exception(f"Failed to fetch traces: {str(e)}")
        return None


def fetch_trace_detail(trace_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed trace data from backend API."""
    try:
        logger.info(f"Fetching trace detail from backend: trace_id={trace_id}")
        response = requests.get(
            f"{BACKEND_URL}/traces/{trace_id}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched detail for trace {trace_id}")
        return data
    except requests.exceptions.ConnectionError:
        logger.warning(f"Backend connection failed for trace {trace_id}")
        return None
    except Exception as e:
        logger.exception(f"Failed to fetch trace detail: {str(e)}")
        return None


def _generate_mock_traces_list(page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """Generate mock traces list for fallback when backend is unavailable."""
    from uuid import uuid4
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    items = []
    start = (page - 1) * limit

    for i in range(start, start + limit):
        items.append(
            {
                "trace_id": f"trace_{uuid4()}",
                "created_at": (now - timedelta(minutes=i * 5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "message_preview": f"Sample question {i+1}...",
                "latency_ms": 600 + (i * 50),
                "cost_usd": round(0.0015 + (i * 0.0003), 4),
                "mock": True,
            }
        )

    return {
        "items": items,
        "source": "mock",
        "count": len(items),
        "page": page,
        "limit": limit,
    }


def _generate_mock_trace_detail(trace_id: str) -> Dict[str, Any]:
    """Generate mock trace detail for fallback when backend is unavailable."""
    from datetime import datetime

    return {
        "trace": {
            "trace_id": trace_id,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "message_preview": "Explain quantum computing in simple terms",
            "latency_ms": 850,
            "cost_usd": 0.0021,
            "cache_hit": False,
            "tokens_used": 245,
            "mock": True,
            "steps": [
                {
                    "name": "validation",
                    "status": "success",
                    "latency_ms": 45,
                    "details": "Input validated successfully",
                },
                {
                    "name": "cache_check",
                    "status": "success",
                    "latency_ms": 30,
                    "details": "Cache lookup - no match found",
                },
                {
                    "name": "api_call",
                    "status": "success",
                    "latency_ms": 650,
                    "details": "Gemini API call completed",
                },
                {
                    "name": "metrics_calc",
                    "status": "success",
                    "latency_ms": 85,
                    "details": "Latency, cost, and metrics calculated",
                },
                {
                    "name": "storage",
                    "status": "success",
                    "latency_ms": 40,
                    "details": "Trace stored in MongoDB",
                },
            ],
        },
        "source": "mock",
    }


def render_flight_recorder():
    """
    Main Flight Recorder page.

    Displays traces list with ability to select and replay individual traces.
    Integrates with real backend API.
    """
    try:
        logger.info("Rendering Flight Recorder page")

        st.title("🎬 Flight Recorder")
        st.caption("Step-by-step trace replay and debugging")
        st.markdown("---")

        # Fetch traces list
        traces_data = fetch_traces_list(page=1, limit=20)

        if traces_data is None:
            st.warning("⚠️ Backend unavailable. Using mock data for demonstration.")
            traces_data = _generate_mock_traces_list(page=1, limit=20)
            is_mock = True
        else:
            is_mock = traces_data.get("source") == "mock"

        traces = traces_data.get("items", [])
        source = traces_data.get("source", "unknown")

        if not traces:
            st.info(
                "📊 No traces available yet. Send a message through the Chat "
                "endpoint to generate traces."
            )
            logger.info("No traces available")
            return

        # Display data source info
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"📋 Available Traces ({len(traces)})")
        with col2:
            if is_mock:
                st.info("📌 Mock Data")
            else:
                st.success("✅ Live Data")

        st.markdown("---")

        # Trace selection
        trace_options = [
            f"{t['created_at']} | {t['message_preview'][:40]}... | {t['latency_ms']}ms"
            for t in traces
        ]

        selected_option = st.selectbox(
            "Select a trace to replay:",
            options=range(len(traces)),
            format_func=lambda i: trace_options[i],
        )

        selected_trace_summary = traces[selected_option]
        selected_trace_id = selected_trace_summary["trace_id"]

        st.markdown("---")

        # Fetch and display detailed trace
        st.subheader("🔍 Trace Details")
        trace_detail_response = fetch_trace_detail(selected_trace_id)

        if trace_detail_response is None:
            st.warning("Could not fetch trace details. Using mock data.")
            trace_detail_response = _generate_mock_trace_detail(selected_trace_id)

        trace_detail = trace_detail_response.get("trace", {})
        detail_source = trace_detail_response.get("source", "unknown")

        # Metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Trace ID",
                trace_detail.get("trace_id", "N/A")[:16] + "...",
            )
        with col2:
            st.metric(
                "Latency",
                f"{trace_detail.get('latency_ms', 0)}ms",
            )
        with col3:
            st.metric(
                "Cost",
                f"${trace_detail.get('cost_usd', 0):.4f}",
            )
        with col4:
            tokens = trace_detail.get("tokens_used", "N/A")
            if isinstance(tokens, int):
                st.metric("Tokens Used", f"{tokens}")
            else:
                st.metric("Tokens Used", str(tokens))

        st.markdown("---")

        # Summary
        st.subheader("📝 Trace Summary")
        summary_col1, summary_col2 = st.columns(2)
        with summary_col1:
            st.write(f"**Created At:** {trace_detail.get('created_at', 'N/A')}")
            st.write(f"**Message:** {trace_detail.get('message_preview', 'N/A')}")
            cache_hit = trace_detail.get("cache_hit", False)
            cache_status = "✅ Cache Hit" if cache_hit else "❌ Cache Miss"
            st.write(f"**Cache:** {cache_status}")
        with summary_col2:
            st.write(f"**Source:** `{detail_source}`")
            st.write(
                f"**Total Latency:** {trace_detail.get('latency_ms', 0)}ms"
            )

        st.markdown("---")

        # Execution timeline
        st.subheader("🎬 Execution Timeline")
        steps = trace_detail.get("steps", [])

        if not steps:
            st.info("No steps available for this trace.")
        else:
            step_data = [
                {"name": s.get("name", "unknown"), "ms": s.get("latency_ms", 0)}
                for s in steps
            ]
            waterfall_fig = render_latency_waterfall(step_data)
            st.plotly_chart(waterfall_fig, use_container_width=True)

            st.markdown("---")
            st.subheader("📍 Step-by-Step Execution")
            render_trace_viewer(
                trace_id=selected_trace_id,
                steps=steps,
            )

        st.markdown("---")

        # Debug section
        with st.expander("🔧 Debug Information"):
            st.write("**Full Trace Data (JSON):**")
            st.json(trace_detail)
            st.write(f"**Data Source:** {detail_source}")

        logger.info(
            f"Flight Recorder page rendered successfully for trace {selected_trace_id}"
        )

    except Exception as e:
        logger.exception("Failed to render Flight Recorder page")
        st.error("Failed to load Flight Recorder")
        st.exception(e)

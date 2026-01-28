import logging
from typing import List, Dict, Any, Optional

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

from ui_components.charts import render_latency_waterfall, render_latency_trend

# --------------------------------------------------
# Logger setup
# --------------------------------------------------
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Backend configuration
# --------------------------------------------------
BACKEND_URL = "http://localhost:8000"


@st.cache_data(ttl=30)
def fetch_traces_list(page: int = 1, limit: int = 50) -> Optional[Dict[str, Any]]:
    """
    Fetch list of traces from backend API.
    Cached for 30 seconds.
    """
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
        logger.warning("Backend connection failed")
        return None
    except Exception as e:
        logger.exception(f"Failed to fetch traces: {str(e)}")
        return None


def fetch_trace_detail(trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed trace data from backend API.
    """
    try:
        logger.info(f"Fetching trace detail: trace_id={trace_id}")
        response = requests.get(
            f"{BACKEND_URL}/traces/{trace_id}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched detail for trace {trace_id}")
        return data
    except Exception as e:
        logger.exception(f"Failed to fetch trace detail: {str(e)}")
        return None


def _generate_mock_traces_list(page: int = 1, limit: int = 50) -> Dict[str, Any]:
    """
    Generate mock traces for fallback.
    """
    from uuid import uuid4
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    items = []

    start = (page - 1) * limit
    for i in range(start, start + limit):
        items.append(
            {
                "trace_id": f"trace_{uuid4()}",
                "created_at": (now - timedelta(minutes=i * 3)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "message_preview": f"Question {i+1}...",
                "latency_ms": 550 + (i * 40),
                "cost_usd": round(0.0012 + (i * 0.0002), 4),
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
    """
    Generate mock trace detail for fallback.
    """
    from datetime import datetime

    return {
        "trace": {
            "trace_id": trace_id,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": "What is machine learning? Explain in detail with examples.",
            "llm_response": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It involves training algorithms on data to make predictions or decisions. Common applications include recommendation systems, image recognition, and natural language processing.",
            "latency_ms": 780,
            "cost_usd": 0.0018,
            "cache_hit": False,
            "tokens_used": 287,
            "input_tokens": 45,
            "output_tokens": 242,
            "model": "gemini-1.5-flash",
            "mock": True,
            "steps": [
                {
                    "name": "validation",
                    "status": "success",
                    "latency_ms": 40,
                    "details": "Input validated successfully",
                },
                {
                    "name": "cache_check",
                    "status": "success",
                    "latency_ms": 25,
                    "details": "Cache lookup - no match found",
                },
                {
                    "name": "api_call",
                    "status": "success",
                    "latency_ms": 620,
                    "details": "Gemini API call completed successfully",
                },
                {
                    "name": "metrics_calc",
                    "status": "success",
                    "latency_ms": 70,
                    "details": "Latency, cost, and metrics calculated",
                },
                {
                    "name": "storage",
                    "status": "success",
                    "latency_ms": 25,
                    "details": "Trace stored in MongoDB",
                },
            ],
        },
        "source": "mock",
    }


def render_request_details():
    """
    Request Details page.
    Deep-dive analysis of individual requests with full context and metadata.
    """
    try:
        logger.info("Rendering Request Details page")

        st.title("📄 Request Details")
        st.caption("Deep-dive analysis of individual LLM requests and responses")

        st.markdown("---")

        # --------------------------------------------------
        # Fetch traces list
        # --------------------------------------------------
        traces_data = fetch_traces_list(page=1, limit=50)
        if traces_data is None:
            st.warning(
                "⚠️ Backend unavailable. Using mock data for demonstration."
            )
            traces_data = _generate_mock_traces_list(page=1, limit=50)
            is_mock = True
        else:
            is_mock = traces_data.get("source") == "mock"

        traces = traces_data.get("items", [])
        source = traces_data.get("source", "unknown")

        if not traces:
            st.info(
                "📊 No traces available yet. Send a message through the Chat endpoint to generate traces."
            )
            logger.info("No traces available")
            return

        # --------------------------------------------------
        # Display data source
        # --------------------------------------------------
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"📋 Browse Requests ({len(traces)})")
        with col2:
            if is_mock:
                st.info("📌 Mock Data")
            else:
                st.success("✅ Live Data")

        st.markdown("---")

        # --------------------------------------------------
        # Request selection
        # --------------------------------------------------
        request_options = [
            f"[{t['created_at']}] {t['message_preview'][:50]}..."
            for t in traces
        ]
        selected_idx = st.selectbox(
            "Select a request to analyze:",
            options=range(len(traces)),
            format_func=lambda i: request_options[i],
        )

        selected_trace_summary = traces[selected_idx]
        selected_trace_id = selected_trace_summary["trace_id"]

        st.markdown("---")

        # --------------------------------------------------
        # Fetch detailed trace
        # --------------------------------------------------
        trace_detail_response = fetch_trace_detail(selected_trace_id)
        if trace_detail_response is None:
            st.warning("Could not fetch trace details. Using mock data.")
            trace_detail_response = _generate_mock_trace_detail(selected_trace_id)

        trace_detail = trace_detail_response.get("trace", {})
        detail_source = trace_detail_response.get("source", "unknown")

        # --------------------------------------------------
        # Section 1: Request & Response
        # --------------------------------------------------
        st.subheader(💬 Request & Response")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**User Input:**")
            user_input = trace_detail.get("user_input", "N/A")
            st.text_area(
                "Input",
                value=str(user_input),
                height=100,
                disabled=True,
                label_visibility="collapsed",
            )

        with col2:
            st.write("**LLM Response:**")
            llm_response = trace_detail.get("llm_response", "N/A")
            st.text_area(
                "Response",
                value=str(llm_response),
                height=100,
                disabled=True,
                label_visibility="collapsed",
            )

        st.markdown("---")

        # --------------------------------------------------
        # Section 2: Performance Metrics
        # --------------------------------------------------
        st.subheader(⚡ Performance Metrics")

        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

        with metric_col1:
            st.metric(
                "Latency",
                f"{trace_detail.get('latency_ms', 0)}ms",
            )

        with metric_col2:
            st.metric(
                "Cost",
                f"${trace_detail.get('cost_usd', 0):.4f}",
            )

        with metric_col3:
            total_tokens = trace_detail.get("tokens_used", 0)
            if isinstance(total_tokens, int):
                st.metric("Total Tokens", f"{total_tokens}")
            else:
                st.metric("Total Tokens", "N/A")

        with metric_col4:
            input_tokens = trace_detail.get("input_tokens", "N/A")
            st.metric("Input Tokens", str(input_tokens))

        with metric_col5:
            output_tokens = trace_detail.get("output_tokens", "N/A")
            st.metric("Output Tokens", str(output_tokens))

        st.markdown("---")

        # --------------------------------------------------
        # Section 3: Trace Metadata
        # --------------------------------------------------
        st.subheader(📋 Trace Metadata")

        metadata_col1, metadata_col2 = st.columns(2)

        with metadata_col1:
            st.write("**Trace Information**")
            st.write(f"**Trace ID:** `{trace_detail.get('trace_id', 'N/A')}`")
            st.write(f"**Created At:** {trace_detail.get('created_at', 'N/A')}")
            st.write(f"**Model:** {trace_detail.get('model', 'N/A')}")
            st.write(f"**Data Source:** `{detail_source}`")

        with metadata_col2:
            st.write("**Cache & Optimization**")
            cache_hit = trace_detail.get("cache_hit", False)
            cache_status = "✅ Cache Hit" if cache_hit else "❌ Cache Miss"
            st.write(f"**Cache:** {cache_status}")
            
            if cache_hit:
                tokens_saved = trace_detail.get("tokens_saved", 0)
                cost_saved = trace_detail.get("cost_saved", 0)
                st.write(f"**Tokens Saved:** {tokens_saved}")
                st.write(f"**Cost Saved:** ${cost_saved:.4f}")
            else:
                st.write("*(First request - no prior cache match)*")

        st.markdown("---")

        # --------------------------------------------------
        # Section 4: Latency Breakdown
        # --------------------------------------------------
        st.subheader(⏱ Latency Breakdown")

        steps = trace_detail.get("steps", [])
        if steps:
            # Create latency breakdown chart
            step_data = [
                {"name": s.get("name", "unknown"), "ms": s.get("latency_ms", 0)}
                for s in steps
            ]
            waterfall_fig = render_latency_waterfall(step_data)
            st.plotly_chart(waterfall_fig, use_container_width=True)

            # Create detailed step table
            st.write("**Step-by-Step Breakdown:**")
            step_data_table = []
            for i, step in enumerate(steps, start=1):
                step_data_table.append(
                    {
                        "Step": i,
                        "Name": step.get("name", "N/A"),
                        "Status": step.get("status", "N/A"),
                        "Latency (ms)": step.get("latency_ms", 0),
                        "Details": step.get("details", ""),
                    }
                )
            df_steps = pd.DataFrame(step_data_table)
            st.dataframe(df_steps, use_container_width=True, hide_index=True)
        else:
            st.info("No step breakdown available for this trace.")

        st.markdown("---")

        # --------------------------------------------------
        # Section 5: Comparison with Other Traces
        # --------------------------------------------------
        st.subheader(📊 Comparison with Recent Requests")

        # Create comparison data
        comparison_data = []
        for i, trace in enumerate(traces[:10]):
            comparison_data.append(
                {
                    "#": i + 1,
                    "Created At": trace.get("created_at", "N/A"),
                    "Message": trace.get("message_preview", "N/A")[:40],
                    "Latency (ms)": trace.get("latency_ms", 0),
                    "Cost (USD)": f"${trace.get('cost_usd', 0):.4f}",
                    "Selected": "👉" if trace.get("trace_id") == selected_trace_id else "",
                }
            )
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)

        st.markdown("---")

        # --------------------------------------------------
        # Section 6: Debug Information
        # --------------------------------------------------
        with st.expander("🔧 Debug Information (Advanced)"):
            st.write("**Complete Trace Data (JSON):**")
            st.json(trace_detail)
            st.write(f"**Data Source:** {detail_source}")
            st.write(f"**Backend URL:** {BACKEND_URL}")

        logger.info(
            f"Request Details page rendered successfully for trace {selected_trace_id}"
        )

    except Exception as e:
        logger.exception("Failed to render Request Details page")
        st.error("Failed to load Request Details")
        st.exception(e)

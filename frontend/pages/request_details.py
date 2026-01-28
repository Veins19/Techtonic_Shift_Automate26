import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import streamlit as st
import requests
import pandas as pd

from ui_components.charts import render_latency_waterfall

logger = logging.getLogger(__name__)
BACKEND_URL = "http://localhost:8000"


def _load_mock_traces() -> List[Dict[str, Any]]:
    """Returns mock trace data for frontend development."""
    now = datetime.utcnow()
    traces = []
    
    for i in range(20):
        traces.append({
            "trace_id": f"trace_{uuid4()}",
            "created_at": (now - timedelta(minutes=i * 3)).strftime("%Y-%m-%d %H:%M:%S"),
            "message_preview": f"Question about AI/ML topic {i+1}",
            "user_input": f"Sample user question about artificial intelligence and machine learning topic {i+1}",
            "llm_response": f"This is a sample LLM response explaining the topic in detail. Response {i+1} contains comprehensive information with examples and explanations.",
            "latency_ms": 550 + (i * 45),
            "cost_usd": round(0.0012 + (i * 0.0002), 4),
            "cache_hit": i % 4 == 0,
            "tokens_used": 220 + (i * 20),
            "input_tokens": 35 + (i * 3),
            "output_tokens": 185 + (i * 17),
            "model": "gemini-1.5-flash",
            "hallucination_score": round(0.03 + (i * 0.01), 2),
            "steps": [
                {"name": "validation", "status": "success", "latency_ms": 35 + i, "details": "Input validated successfully"},
                {"name": "cache_check", "status": "success", "latency_ms": 20 + i, "details": "Semantic cache lookup performed"},
                {"name": "api_call", "status": "success", "latency_ms": 420 + (i * 30), "details": "Gemini API call completed"},
                {"name": "metrics_calc", "status": "success", "latency_ms": 50, "details": "Performance metrics calculated"},
                {"name": "storage", "status": "success", "latency_ms": 25, "details": "Trace persisted to MongoDB"},
            ],
        })
    
    return traces


def fetch_traces_list(page: int = 1, limit: int = 50) -> Optional[Dict[str, Any]]:
    """Fetch list of traces from backend API. NO CACHING for real-time updates."""
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
    """Fetch detailed trace data from backend API."""
    try:
        logger.info(f"Fetching trace detail: trace_id={trace_id}")
        response = requests.get(f"{BACKEND_URL}/traces/{trace_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched detail for trace {trace_id}")
        return data
    except Exception as e:
        logger.exception(f"Failed to fetch trace detail: {str(e)}")
        return None


def render_request_details():
    """Request Inspector page with comprehensive request/response analysis."""
    try:
        logger.info("Rendering Request Inspector page")
        
        # Header with refresh button
        col_header, col_refresh = st.columns([5, 1])
        
        with col_header:
            st.markdown("""
            <div style="margin-bottom: 2.5rem;">
                <h1 style="margin-bottom: 0.5rem; font-size: 2.25rem; font-weight: 600;">Request Inspector</h1>
                <p style="color: #8B949E; font-size: 1.125rem; margin: 0; font-weight: 400;">
                    Deep-dive analysis of individual LLM requests and responses
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_refresh:
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Refresh", use_container_width=True, type="secondary"):
                st.rerun()
        
        # Fetch traces list
        traces_data = fetch_traces_list(page=1, limit=50)
        
        # Use mock data if backend unavailable
        if traces_data is None:
            traces = _load_mock_traces()
            is_mock = True
            source = "mock"
        else:
            traces = traces_data.get("items", [])
            is_mock = traces_data.get("source") == "mock"
            source = traces_data.get("source", "unknown")
            
            # If backend returns empty, use mock
            if not traces:
                traces = _load_mock_traces()
                is_mock = True
                source = "mock"
        
        if not traces:
            st.info("No requests available yet. Send messages through the Live Dashboard to generate request data.")
            logger.info("No traces available")
            return
        
        # Request Browser Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Request Browser
            </h2>
            <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
                Browse and select individual requests for detailed inspection
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Only show source in dev mode
        if is_mock:
            with st.expander("🔧 Development Mode", expanded=False):
                st.caption("Displaying mock request data for development. Connect backend for live requests.")
        
        # Request selection
        request_options = [
            f"[{t.get('created_at', 'N/A')}] {t.get('message_preview', 'No preview')[:55]}..."
            for t in traces
        ]
        
        selected_idx = st.selectbox(
            "Select a request to inspect:",
            options=range(len(traces)),
            format_func=lambda i: request_options[i],
        )
        
        selected_trace = traces[selected_idx]
        selected_trace_id = selected_trace.get("trace_id", "unknown")
        
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Fetch detailed trace (or use what we have)
        trace_detail_response = fetch_trace_detail(selected_trace_id)
        
        if trace_detail_response is None:
            trace_detail = selected_trace
        else:
            trace_detail = trace_detail_response.get("trace", selected_trace)
        
        # Request & Response Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Request & Response Content
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**User Input:**")
            user_input = trace_detail.get("user_input", trace_detail.get("message_preview", "N/A"))
            st.text_area(
                "Input",
                value=str(user_input),
                height=150,
                disabled=True,
                label_visibility="collapsed",
            )
        
        with col2:
            st.markdown("**LLM Response:**")
            llm_response = trace_detail.get("llm_response", "Response not available")
            st.text_area(
                "Response",
                value=str(llm_response),
                height=150,
                disabled=True,
                label_visibility="collapsed",
            )
        
        st.markdown("<div style='margin: 2.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Performance Metrics Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Performance Metrics
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
        
        with metric_col1:
            st.metric("Total Latency", f"{trace_detail.get('latency_ms', 0)}ms")
        
        with metric_col2:
            st.metric("API Cost", f"${trace_detail.get('cost_usd', 0):.4f}")
        
        with metric_col3:
            total_tokens = trace_detail.get("tokens_used", 0)
            st.metric("Total Tokens", str(total_tokens) if isinstance(total_tokens, int) else "N/A")
        
        with metric_col4:
            input_tokens = trace_detail.get("input_tokens", "N/A")
            st.metric("Input Tokens", str(input_tokens))
        
        with metric_col5:
            output_tokens = trace_detail.get("output_tokens", "N/A")
            st.metric("Output Tokens", str(output_tokens))
        
        st.markdown("<div style='margin: 2.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Request Metadata Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Request Metadata
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        metadata_col1, metadata_col2 = st.columns(2)
        
        with metadata_col1:
            st.markdown("**Request Information:**")
            st.markdown(f"**Trace ID:** `{trace_detail.get('trace_id', 'N/A')}`")
            st.markdown(f"**Timestamp:** {trace_detail.get('created_at', 'N/A')}")
            st.markdown(f"**Model:** {trace_detail.get('model', 'gemini-1.5-flash')}")
            quality = round((1 - trace_detail.get('hallucination_score', 0)) * 100, 1)
            st.markdown(f"**Quality Score:** {quality}%")
        
        with metadata_col2:
            st.markdown("**Cache & Optimization:**")
            cache_hit = trace_detail.get("cache_hit", False)
            cache_status = "✓ Cache Hit" if cache_hit else "○ Cache Miss"
            st.markdown(f"**Status:** {cache_status}")
            
            if cache_hit:
                cache_saved_ms = trace_detail.get("cache_saved_ms", 0)
                st.markdown(f"**Time Saved:** {cache_saved_ms}ms")
                st.markdown(f"**Cost Saved:** ${trace_detail.get('cost_saved', 0):.4f}")
                st.markdown("*Instant response from semantic cache*")
            else:
                st.markdown("*Fresh API call - response cached for future*")
        
        st.markdown("<div style='margin: 2.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Latency Breakdown Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Execution Latency Breakdown
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        steps = trace_detail.get("steps", [])
        
        if steps:
            # Waterfall Chart
            step_data = [
                {"name": s.get("name", "unknown"), "ms": s.get("latency_ms", 0)}
                for s in steps
            ]
            
            waterfall_fig = render_latency_waterfall(step_data)
            st.plotly_chart(waterfall_fig, use_container_width=True)
            
            # Step Table
            st.markdown("**Step-by-Step Execution Details:**")
            step_data_table = []
            
            for i, step in enumerate(steps, start=1):
                step_data_table.append({
                    "Step": i,
                    "Name": step.get("name", "N/A").replace("_", " ").title(),
                    "Status": step.get("status", "N/A").upper(),
                    "Latency (ms)": step.get("latency_ms", 0),
                    "Details": step.get("details", ""),
                })
            
            df_steps = pd.DataFrame(step_data_table)
            st.dataframe(df_steps, use_container_width=True, hide_index=True)
        else:
            st.info("No execution step breakdown available for this request")
        
        st.markdown("<div style='margin: 2.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Comparative Analysis Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Comparative Analysis
            </h2>
            <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
                Compare this request with recent requests to identify patterns and anomalies
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        comparison_data = []
        
        for i, trace in enumerate(traces[:15]):
            is_selected = trace.get("trace_id") == selected_trace_id
            comparison_data.append({
                "#": i + 1,
                "Timestamp": trace.get("created_at", "N/A"),
                "Request": trace.get("message_preview", "N/A")[:45] + "...",
                "Latency (ms)": trace.get("latency_ms", 0),
                "Cost (USD)": f"${trace.get('cost_usd', 0):.4f}",
                "Tokens": trace.get("tokens_used", "N/A"),
                "Cache": "✓" if trace.get("cache_hit", False) else "○",
                "Selected": "→" if is_selected else "",
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Quick stats
        st.markdown("<div style='margin: 1.5rem 0 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            faster_count = sum(1 for t in traces if t.get("latency_ms", 0) < trace_detail.get("latency_ms", 0))
            st.metric("Faster Requests", f"{faster_count}/{len(traces)}")
        
        with col2:
            cheaper_count = sum(1 for t in traces if t.get("cost_usd", 0) < trace_detail.get("cost_usd", 0))
            st.metric("Cheaper Requests", f"{cheaper_count}/{len(traces)}")
        
        with col3:
            cached_count = sum(1 for t in traces if t.get("cache_hit", False))
            st.metric("Total Cached", f"{cached_count}/{len(traces)}")
        
        with col4:
            avg_latency = int(sum(t.get("latency_ms", 0) for t in traces) / len(traces))
            diff = trace_detail.get("latency_ms", 0) - avg_latency
            st.metric("vs Average", f"{diff:+d}ms")
        
        st.markdown("<div style='margin: 2.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Advanced Debug Section (collapsible)
        with st.expander("🔍 Advanced Debug Information"):
            st.markdown("**Complete Request Data (JSON):**")
            st.json(trace_detail)
            st.markdown(f"**Data Source:** `{source}`")
            st.markdown(f"**Backend URL:** `{BACKEND_URL}`")
        
        logger.info(f"Request Inspector page rendered successfully for trace {selected_trace_id}")
        
    except Exception as e:
        logger.exception("Failed to render Request Inspector page")
        st.error("An error occurred while loading Request Inspector. Please refresh the page.")
        st.exception(e)

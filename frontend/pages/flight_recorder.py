import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import uuid4
import streamlit as st
import requests

from ui_components.charts import (
    render_latency_waterfall,
    render_latency_trend,
    render_cost_distribution,
)
from ui_components.trace_viewer import render_trace_viewer

logger = logging.getLogger(__name__)
BACKEND_URL = "http://localhost:8000"


def _load_mock_traces() -> List[Dict[str, Any]]:
    """Returns mock trace data for frontend development."""
    now = datetime.utcnow()
    traces = []
    
    for i in range(12):
        traces.append({
            "trace_id": f"trace_{uuid4()}",
            "created_at": (now - timedelta(minutes=i * 5)).strftime("%Y-%m-%d %H:%M:%S"),
            "message_preview": f"Sample question about AI/ML topic {i+1}",
            "latency_ms": 550 + i * 85,
            "cost_usd": round(0.0012 + i * 0.0003, 4),
            "hallucination_score": round(0.04 + i * 0.015, 2),
            "drift_score": round(0.03 + i * 0.012, 2),
            "cache_hit": i % 3 == 0,
            "tokens_used": 200 + i * 25,
            "steps": [
                {"name": "validation", "status": "success", "latency_ms": 35 + i * 2, "details": "Input validated successfully"},
                {"name": "cache_check", "status": "success", "latency_ms": 25 + i, "details": "Cache lookup performed"},
                {"name": "retrieval", "status": "success", "latency_ms": 110 + i * 8, "details": "Context retrieved from vector store"},
                {"name": "generation", "status": "success", "latency_ms": 320 + i * 50, "details": "LLM response generated"},
                {"name": "metrics", "status": "success", "latency_ms": 35, "details": "Performance metrics calculated"},
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
        logger.warning("Backend connection failed - using mock data")
        return None
    except Exception as e:
        logger.exception(f"Failed to fetch traces: {str(e)}")
        return None


def fetch_trace_detail(trace_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed trace data from backend API."""
    try:
        logger.info(f"Fetching trace detail from backend: trace_id={trace_id}")
        response = requests.get(f"{BACKEND_URL}/traces/{trace_id}", timeout=10)
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


def render_flight_recorder_page():
    """Trace Analytics page with comprehensive performance analysis."""
    try:
        logger.info("Rendering Trace Analytics page")
        
        # Header with refresh button
        col_header, col_refresh = st.columns([5, 1])
        
        with col_header:
            st.markdown("""
            <div style="margin-bottom: 2.5rem;">
                <h1 style="margin-bottom: 0.5rem; font-size: 2.25rem; font-weight: 600;">Trace Analytics</h1>
                <p style="color: #8B949E; font-size: 1.125rem; margin: 0; font-weight: 400;">
                    Comprehensive performance analysis and trace inspection
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
            st.info("No traces available yet. Send messages through the Live Dashboard to generate traces.")
            logger.info("No traces available")
            return
        
        # Performance Overview Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Performance Overview
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Aggregate metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Traces", f"{len(traces):,}")
        
        with col2:
            avg_latency = int(sum(t.get('latency_ms', 0) for t in traces) / len(traces))
            st.metric("Avg Latency", f"{avg_latency}ms")
        
        with col3:
            avg_cost = round(sum(t.get('cost_usd', 0) for t in traces) / len(traces), 4)
            st.metric("Avg Cost", f"${avg_cost}")
        
        with col4:
            cache_hits = sum(1 for t in traces if t.get('cache_hit', False))
            cache_rate = round((cache_hits / len(traces)) * 100, 1) if traces else 0
            st.metric("Cache Rate", f"{cache_rate}%")
        
        with col5:
            avg_quality = round((1 - sum(t.get('hallucination_score', 0) for t in traces) / len(traces)) * 100, 1)
            st.metric("Quality Score", f"{avg_quality}%")
        
        # Only show source in dev mode
        if is_mock:
            with st.expander("🔧 Development Mode", expanded=False):
                st.caption(f"Displaying mock trace data for development. Connect backend for live traces.")
        
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Performance Charts
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Performance Trends
            </h2>
            <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
                Historical trends across latency, cost, and resource utilization
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Render charts
        latency_fig = render_latency_trend(traces)
        cost_fig = render_cost_distribution(traces)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.plotly_chart(latency_fig, use_container_width=True)
        
        with col_right:
            st.plotly_chart(cost_fig, use_container_width=True)
        
        st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
        
        # Trace Inspector Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Trace Inspector
            </h2>
            <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
                Deep-dive into individual request execution with step-by-step breakdown
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trace selection
        trace_options = [
            f"{t.get('created_at', 'N/A')} | {t.get('message_preview', 'No preview')[:50]}... | {t.get('latency_ms', 0)}ms"
            for t in traces
        ]
        
        selected_idx = st.selectbox(
            "Select a trace to analyze:",
            options=range(len(traces)),
            format_func=lambda i: trace_options[i],
        )
        
        selected_trace = traces[selected_idx]
        selected_trace_id = selected_trace.get("trace_id", "unknown")
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Fetch detailed trace (or use what we have)
        trace_detail_response = fetch_trace_detail(selected_trace_id)
        
        if trace_detail_response is None:
            trace_detail = selected_trace
        else:
            trace_detail = trace_detail_response.get("trace", selected_trace)
        
        # Trace metadata
        st.markdown("""
        <div style='margin: 1.5rem 0 0.75rem 0;'>
            <h3 style='color: #C9D1D9; font-size: 1.125rem; font-weight: 600;'>Trace Metadata</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Trace ID", trace_detail.get("trace_id", "N/A")[:16] + "...")
        
        with col2:
            st.metric("Total Latency", f"{trace_detail.get('latency_ms', 0)}ms")
        
        with col3:
            st.metric("Cost", f"${trace_detail.get('cost_usd', 0):.4f}")
        
        with col4:
            tokens = trace_detail.get("tokens_used", "N/A")
            st.metric("Tokens", str(tokens) if isinstance(tokens, int) else tokens)
        
        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Additional info
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"**Timestamp:** {trace_detail.get('created_at', 'N/A')}")
            st.markdown(f"**Message:** {trace_detail.get('message_preview', 'N/A')}")
        
        with info_col2:
            cache_status = "Cache Hit ✓" if trace_detail.get('cache_hit', False) else "Cache Miss"
            st.markdown(f"**Cache:** {cache_status}")
            quality = round((1 - trace_detail.get('hallucination_score', 0)) * 100, 1)
            st.markdown(f"**Quality Score:** {quality}%")
        
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Latency Breakdown
        st.markdown("""
        <div style='margin: 1.5rem 0 0.75rem 0;'>
            <h3 style='color: #C9D1D9; font-size: 1.125rem; font-weight: 600;'>Execution Latency Breakdown</h3>
        </div>
        """, unsafe_allow_html=True)
        
        steps = trace_detail.get("steps", [])
        
        if not steps:
            st.info("No execution steps available for this trace")
        else:
            step_data = [
                {"name": s.get("name", "unknown"), "ms": s.get("latency_ms", 0)}
                for s in steps
            ]
            
            waterfall_fig = render_latency_waterfall(step_data)
            st.plotly_chart(waterfall_fig, use_container_width=True)
        
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Execution Timeline
        st.markdown("""
        <div style='margin: 1.5rem 0 0.75rem 0;'>
            <h3 style='color: #C9D1D9; font-size: 1.125rem; font-weight: 600;'>Execution Timeline Replay</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if steps:
            render_trace_viewer(trace_id=selected_trace_id, steps=steps)
        else:
            st.info("No execution timeline available for this trace")
        
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Advanced debug (collapsible)
        with st.expander("🔍 Advanced Trace Data"):
            st.markdown("**Complete Trace JSON:**")
            st.json(trace_detail)
        
        logger.info(f"Trace Analytics page rendered successfully for trace {selected_trace_id}")
        
    except Exception as e:
        logger.exception("Failed to render Trace Analytics page")
        st.error("An error occurred while loading Trace Analytics. Please refresh the page.")
        st.exception(e)

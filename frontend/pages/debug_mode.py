import logging
import requests
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any
import streamlit as st

from ui_components.charts import (
    render_latency_trend,
    render_cost_distribution,
    render_latency_waterfall,
)

from ui_components.trace_viewer import render_trace_viewer

# --------------------------------------------------
# Logger setup
# --------------------------------------------------

logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:8000"


def _load_mock_traces() -> List[Dict[str, Any]]:
    """
    Returns mock trace data for frontend development.
    NO backend calls.
    """
    now = datetime.utcnow()
    traces = []
    
    for i in range(6):
        traces.append(
            {
                "trace_id": f"trace_{uuid4()}",
                "created_at": (now - timedelta(minutes=i * 6)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "latency_ms": 600 + i * 110,
                "cost_usd": round(0.0015 + i * 0.0004, 4),
                "hallucination_score": round(0.05 + i * 0.02, 2),
                "drift_score": round(0.04 + i * 0.015, 2),
                "steps": [
                    {
                        "name": "retrieval",
                        "status": "success",
                        "latency_ms": 120 + i * 10,
                        "details": "Fetched context from vector store",
                    },
                    {
                        "name": "prompt_build",
                        "status": "success",
                        "latency_ms": 80 + i * 5,
                        "details": "Constructed final prompt",
                    },
                    {
                        "name": "generation",
                        "status": "success",
                        "latency_ms": 350 + i * 60,
                        "details": "LLM generated response",
                    },
                    {
                        "name": "metrics",
                        "status": "success",
                        "latency_ms": 40,
                        "details": "Latency, cost, drift calculated",
                    },
                ],
            }
        )
    
    return traces


def send_message_to_backend(message: str, stream: bool = False) -> Dict[str, Any]:
    """Send message to backend /chat endpoint and return response."""
    try:
        logger.info(f"Sending message to backend: {message[:50]}... (stream={stream})")
        
        if stream:
            # Streaming request
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": message, "stream": True},
                timeout=30,
                stream=True,
            )
            response.raise_for_status()
            return {"success": True, "stream": response, "streaming": True}
        else:
            # Non-streaming request
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": message, "stream": False},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Message sent successfully, received response")
            return {"success": True, "data": data, "streaming": False}
            
    except requests.exceptions.ConnectionError:
        logger.warning("Backend connection failed")
        return {
            "success": False,
            "error": "❌ Cannot connect to backend. Is it running on http://localhost:8000?",
        }
    except Exception as e:
        logger.exception(f"Failed to send message: {str(e)}")
        return {"success": False, "error": f"❌ Error: {str(e)}"}


def render_debug_dashboard():
    """
    Main Debug Dashboard page.
    Wires together charts + trace viewer using mock data.
    """
    try:
        logger.info("Rendering Debug Dashboard")
        
        st.title("🧪 Debug Dashboard")
        st.caption("LLM Flight Recorder — Real-time AI responses with streaming")
        st.markdown("---")

        # --------------------------------------------------
        # Chat Interface with Streaming
        # --------------------------------------------------
        st.subheader("💬 Send Message")
        
        # Enable streaming toggle
        enable_streaming = st.checkbox("🔄 Enable Streaming (word-by-word)", value=True)
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_message = st.text_input(
                "Enter your message:",
                placeholder="Ask me anything...",
                label_visibility="collapsed",
            )
        
        with col2:
            send_button = st.button("📤 Send", use_container_width=True)

        if send_button and user_message:
            if enable_streaming:
                # STREAMING MODE
                with st.spinner("Connecting to AI..."):
                    result = send_message_to_backend(user_message, stream=True)
                
                if result["success"]:
                    st.success("✅ Streaming response:")
                    
                    # Create placeholder for streaming text
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    try:
                        # Read SSE stream
                        for line in result["stream"].iter_lines():
                            if line:
                                decoded = line.decode('utf-8')
                                if decoded.startswith("data: "):
                                    chunk = decoded[6:]  # Remove "data: " prefix
                                    
                                    if chunk == "[DONE]":
                                        break
                                    elif chunk.startswith("[ERROR"):
                                        st.error(chunk)
                                        break
                                    else:
                                        full_response += chunk
                                        # Update placeholder with accumulated response
                                        response_placeholder.markdown(f"**Response:**\n\n{full_response}")
                        
                        st.info("⏱️ Streaming completed!")
                        
                    except Exception as e:
                        st.error(f"Streaming error: {str(e)}")
                else:
                    st.error(result.get("error", "Unknown error"))
            
            else:
                # NON-STREAMING MODE (original)
                with st.spinner("Sending message to backend..."):
                    result = send_message_to_backend(user_message, stream=False)
                
                if result["success"]:
                    st.success("✅ Message sent successfully!")
                    response_data = result.get("data", {})
                    
                    # Display response using correct field names from backend
                    st.write("**Response:**")
                    st.write(response_data.get("reply", "No response"))
                    st.write(f"**Trace ID:** {response_data.get('trace_id', 'N/A')}")
                    st.write(f"**Latency:** {response_data.get('latency_ms', 'N/A')}ms")
                    st.write(f"**Mode:** {'Mock' if response_data.get('mock', False) else 'Live'}")
                else:
                    st.error(result.get("error", "Unknown error"))

        st.markdown("---")

        # --------------------------------------------------
        # Load data
        # --------------------------------------------------
        traces = _load_mock_traces()
        
        if not traces:
            st.warning("No traces available.")
            return

        # --------------------------------------------------
        # High-level metrics
        # --------------------------------------------------
        st.subheader("📊 System Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total Traces", len(traces))
        col2.metric(
            "Avg Latency (ms)",
            int(sum(t["latency_ms"] for t in traces) / len(traces)),
        )
        col3.metric(
            "Avg Cost ($)",
            round(sum(t["cost_usd"] for t in traces) / len(traces), 4),
        )
        col4.metric(
            "Avg Hallucination",
            round(
                sum(t["hallucination_score"] for t in traces) / len(traces),
                2,
            ),
        )

        st.markdown("---")

        # --------------------------------------------------
        # Charts
        # --------------------------------------------------
        st.subheader("📈 Performance Trends")
        
        latency_fig = render_latency_trend(traces)
        cost_fig = render_cost_distribution(traces)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.plotly_chart(latency_fig, use_container_width=True)
        
        with col_right:
            st.plotly_chart(cost_fig, use_container_width=True)

        st.markdown("---")

        # --------------------------------------------------
        # Trace selection
        # --------------------------------------------------
        st.subheader("🧾 Trace Explorer")
        
        trace_ids = [t["trace_id"] for t in traces]
        selected_trace_id = st.selectbox("Select Trace ID", trace_ids)
        
        selected_trace = next(
            t for t in traces if t["trace_id"] == selected_trace_id
        )

        st.markdown("### Trace Summary")
        st.json(
            {
                "trace_id": selected_trace["trace_id"],
                "created_at": selected_trace["created_at"],
                "latency_ms": selected_trace["latency_ms"],
                "cost_usd": selected_trace["cost_usd"],
                "hallucination_score": selected_trace["hallucination_score"],
                "drift_score": selected_trace["drift_score"],
            }
        )

        # --------------------------------------------------
        # Latency breakdown
        # --------------------------------------------------
        st.subheader("⏱ Latency Breakdown")
        
        waterfall_fig = render_latency_waterfall(
            [
                {"name": s["name"], "ms": s["latency_ms"]}
                for s in selected_trace["steps"]
            ]
        )
        st.plotly_chart(waterfall_fig, use_container_width=True)

        # --------------------------------------------------
        # Trace replay (Flight Recorder)
        # --------------------------------------------------
        st.subheader("🎬 Flight Recorder Replay")
        render_trace_viewer(
            trace_id=selected_trace["trace_id"],
            steps=selected_trace["steps"],
        )

        logger.info("Debug Dashboard rendered successfully")
        
    except Exception as e:
        logger.exception("Failed to render Debug Dashboard")
        st.error("Failed to load Debug Dashboard")
        st.exception(e)

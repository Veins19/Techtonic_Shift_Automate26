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


logger = logging.getLogger(__name__)
BACKEND_URL = "http://localhost:8000"



def fetch_system_stats() -> Dict[str, Any]:
    """Fetch real-time system statistics from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=10)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.ConnectionError:
        logger.warning("Backend connection failed for stats")
        return {"success": False, "error": "Backend unavailable"}
    except Exception as e:
        logger.exception(f"Failed to fetch stats: {str(e)}")
        return {"success": False, "error": str(e)}



def download_traces(format_type: str) -> Dict[str, Any]:
    """Download all traces in specified format."""
    try:
        logger.info(f"Requesting trace export as {format_type}")
        response = requests.get(
            f"{BACKEND_URL}/export",
            params={"format": format_type},
            timeout=30,
        )
        response.raise_for_status()
        return {
            "success": True,
            "data": response.content,
            "filename": response.headers.get("Content-Disposition", f"traces.{format_type}").split("filename=")[-1],
        }
    except requests.exceptions.ConnectionError:
        logger.warning("Backend connection failed for export")
        return {"success": False, "error": "Backend unavailable"}
    except Exception as e:
        logger.exception(f"Failed to download traces: {str(e)}")
        return {"success": False, "error": str(e)}



def send_message_to_backend(message: str, stream: bool = False) -> Dict[str, Any]:
    """Send message to backend /chat endpoint and return response."""
    try:
        logger.info(f"Sending message to backend: {message[:50]}... (stream={stream})")
        
        if stream:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"message": message, "stream": True},
                timeout=30,
                stream=True,
            )
            response.raise_for_status()
            return {"success": True, "stream": response, "streaming": True}
        else:
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
        return {"success": False, "error": "Cannot connect to backend. Is it running on http://localhost:8000?"}
    except Exception as e:
        logger.exception(f"Failed to send message: {str(e)}")
        return {"success": False, "error": f"Error: {str(e)}"}



def render_debug_dashboard():
    """Main Live Dashboard page - focused on real-time monitoring and interaction."""
    try:
        logger.info("Rendering Live Dashboard")
        
        # Header
        st.markdown("""
        <div style="margin-bottom: 2.5rem;">
            <h1 style="margin-bottom: 0.5rem; font-size: 2.25rem; font-weight: 600;">Live Dashboard</h1>
            <p style="color: #8B949E; font-size: 1.125rem; margin: 0; font-weight: 400;">
                Real-time system monitoring and AI interaction interface
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # System Stats Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                System Performance Metrics
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        stats_result = fetch_system_stats()
        
        if stats_result["success"]:
            stats = stats_result["data"]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Requests", f"{stats.get('total_requests', 0):,}")
            
            with col2:
                cache_hit_rate = stats.get("cache_hit_rate", 0.0)
                st.metric("Cache Hit Rate", f"{cache_hit_rate}%")
            
            with col3:
                st.metric("Cache Hits", f"{stats.get('total_cache_hits', 0):,}")
            
            with col4:
                avg_latency = stats.get("avg_latency_ms", 0)
                st.metric("Avg Latency", f"{avg_latency}ms")
            
            with col5:
                time_saved = stats.get("total_time_saved_ms", 0)
                time_saved_sec = round(time_saved / 1000, 1)
                st.metric("Time Saved", f"{time_saved_sec}s")
            
            # Only show source indicator in development mode
            if stats.get("source") == "mock":
                with st.expander("🔧 Development Mode", expanded=False):
                    st.caption("Currently displaying mock data for development. Connect MongoDB for live statistics.")
        else:
            st.info("System statistics are currently unavailable. Ensure the backend is running on http://localhost:8000")
        
        st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
        
        # Export Section
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                Data Export & Analytics
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("""
            <p style='color: #8B949E; margin-top: 0.5rem; font-size: 0.95rem; line-height: 1.6;'>
                Export complete trace data for offline analysis, compliance reporting, and long-term storage
            </p>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📄 Export JSON", use_container_width=True, type="secondary"):
                with st.spinner("Preparing JSON export..."):
                    result = download_traces("json")
                    if result["success"]:
                        st.download_button(
                            label="⬇️ Download JSON",
                            data=result["data"],
                            file_name=result["filename"],
                            mime="application/json",
                            use_container_width=True,
                        )
                        st.success("✓ Export ready for download")
                    else:
                        st.error(f"Export failed: {result['error']}")
        
        with col3:
            if st.button("📊 Export CSV", use_container_width=True, type="secondary"):
                with st.spinner("Preparing CSV export..."):
                    result = download_traces("csv")
                    if result["success"]:
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=result["data"],
                            file_name=result["filename"],
                            mime="text/csv",
                            use_container_width=True,
                        )
                        st.success("✓ Export ready for download")
                    else:
                        st.error(f"Export failed: {result['error']}")
        
        st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
        
        # Chat Interface
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #C9D1D9; border-bottom: 1px solid #21262D; padding-bottom: 0.5rem;">
                AI Interaction Interface
            </h2>
            <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
                Test LLM responses with intelligent semantic caching and real-time streaming
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        enable_streaming = st.checkbox("Enable real-time streaming (word-by-word response)", value=True)
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_message = st.text_input(
                "Enter your message:",
                placeholder="e.g., Explain quantum computing in simple terms...",
                label_visibility="collapsed",
            )
        
        with col2:
            send_button = st.button("Send Message", use_container_width=True, type="primary")

        if send_button and user_message:
            st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
            
            if enable_streaming:
                # Streaming mode
                with st.spinner("🔄 Processing request..."):
                    result = send_message_to_backend(user_message, stream=True)
                
                if result["success"]:
                    st.success("✓ Streaming started")
                    
                    # Display user message
                    st.markdown("""
                    <div style="background: #0D1117; padding: 1rem 1.5rem; border-radius: 8px; border-left: 4px solid #58A6FF; margin-bottom: 1rem;">
                        <p style="color: #8B949E; font-size: 0.875rem; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Your Question:</p>
                        <p style="color: #C9D1D9; font-size: 1rem; line-height: 1.6; margin: 0;">{}</p>
                    </div>
                    """.format(user_message), unsafe_allow_html=True)
                    
                    # Response placeholder
                    st.markdown("""
                    <p style="color: #8B949E; font-size: 0.875rem; margin: 1.5rem 0 0.75rem 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">AI Response:</p>
                    """, unsafe_allow_html=True)
                    
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    try:
                        for line in result["stream"].iter_lines():
                            if line:
                                decoded = line.decode('utf-8')
                                if decoded.startswith("data: "):
                                    chunk = decoded[6:]
                                    
                                    if chunk == "[DONE]":
                                        break
                                    elif chunk.startswith("[ERROR"):
                                        st.error(chunk)
                                        break
                                    else:
                                        full_response += chunk
                                        response_placeholder.markdown("""
                                        <div style="background: #161B22; padding: 1.5rem; border-radius: 8px; border: 1px solid #30363D;">
                                            <p style="color: #E6EDF3; font-size: 1rem; line-height: 1.8; margin: 0; white-space: pre-wrap;">{}</p>
                                        </div>
                                        """.format(full_response), unsafe_allow_html=True)
                        
                        st.info("✓ Streaming completed successfully")
                        st.markdown("<p style='color: #8B949E; font-size: 0.875rem; margin-top: 1rem;'>💡 View detailed trace in <strong>Trace Analytics</strong> or <strong>Request Inspector</strong></p>", unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Streaming error: {str(e)}")
                else:
                    st.error(result.get("error", "Unknown error occurred"))
            
            else:
                # Non-streaming mode
                with st.spinner("🔄 Processing request..."):
                    result = send_message_to_backend(user_message, stream=False)
                
                if result["success"]:
                    response_data = result.get("data", {})
                    
                    st.success("✓ Request completed successfully")
                    
                    # Cache status
                    cache_hit = response_data.get("cache_hit", False)
                    cache_saved_ms = response_data.get("cache_saved_ms", 0)
                    
                    if cache_hit:
                        st.info(f"⚡ **Cache Hit** — Response delivered instantly (saved {cache_saved_ms}ms)")
                    else:
                        st.warning("🔄 **Cache Miss** — Fresh LLM API call executed")
                    
                    # Display user message
                    st.markdown("""
                    <div style="background: #0D1117; padding: 1rem 1.5rem; border-radius: 8px; border-left: 4px solid #58A6FF; margin: 1rem 0;">
                        <p style="color: #8B949E; font-size: 0.875rem; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Your Question:</p>
                        <p style="color: #C9D1D9; font-size: 1rem; line-height: 1.6; margin: 0;">{}</p>
                    </div>
                    """.format(user_message), unsafe_allow_html=True)
                    
                    # Display response
                    st.markdown("""
                    <p style="color: #8B949E; font-size: 0.875rem; margin: 1.5rem 0 0.75rem 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">AI Response:</p>
                    """, unsafe_allow_html=True)
                    
                    response_text = response_data.get("reply", "No response available")
                    st.markdown("""
                    <div style="background: #161B22; padding: 1.5rem; border-radius: 8px; border: 1px solid #30363D;">
                        <p style="color: #E6EDF3; font-size: 1rem; line-height: 1.8; margin: 0; white-space: pre-wrap;">{}</p>
                    </div>
                    """.format(response_text), unsafe_allow_html=True)
                    
                    # Metrics
                    st.markdown("<div style='margin: 2rem 0 1rem 0;'><h4 style='color: #8B949E; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.5px;'>Request Metrics</h4></div>", unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Trace ID", response_data.get('trace_id', 'N/A')[:16] + "...")
                    with col2:
                        st.metric("Latency", f"{response_data.get('latency_ms', 'N/A')}ms")
                    with col3:
                        mode = 'Production' if not response_data.get('mock', False) else 'Development'
                        st.metric("Environment", mode)
                    
                    # Helpful note
                    st.markdown("<p style='color: #8B949E; font-size: 0.875rem; margin-top: 1.5rem;'>💡 View detailed trace in <strong>Trace Analytics</strong> or <strong>Request Inspector</strong></p>", unsafe_allow_html=True)
                else:
                    st.error(result.get("error", "Unknown error occurred"))

        logger.info("Live Dashboard rendered successfully")
        
    except Exception as e:
        logger.exception("Failed to render Live Dashboard")
        st.error("An error occurred while loading the dashboard. Please refresh the page.")
        st.exception(e)

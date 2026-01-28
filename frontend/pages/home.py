import logging
import streamlit as st

logger = logging.getLogger(__name__)


def render_home_page():
    """
    Premium landing page for LLM Flight Recorder.
    Enterprise-grade SaaS design with hero section and navigation cards.
    """
    try:
        logger.info("Rendering Home landing page")
        
        # Hero Section
        st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem 3rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 3rem;">
            <h1 style="font-size: 3.5rem; font-weight: 700; color: #FFFFFF; margin-bottom: 1rem; line-height: 1.2;">
                Flight Recorder
            </h1>
            <p style="font-size: 1.5rem; color: #E0E7FF; margin-bottom: 0.5rem; font-weight: 300;">
                Enterprise LLM Observability Platform
            </p>
            <p style="font-size: 1.125rem; color: #C7D2FE; max-width: 700px; margin: 0 auto; line-height: 1.6;">
                Real-time monitoring, semantic caching, and complete trace replay for production AI systems
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Value Proposition
        st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <h2 style="font-size: 2rem; font-weight: 600; color: #F0F6FC; margin-bottom: 2rem;">
                Why Flight Recorder?
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); padding: 2rem; border-radius: 12px; text-align: center; height: 100%; border: 1px solid #2563eb;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
                <h3 style="color: #93c5fd; font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem;">
                    30% Cost Reduction
                </h3>
                <p style="color: #bfdbfe; font-size: 0.95rem; line-height: 1.6;">
                    Intelligent semantic caching reduces API calls and accelerates response times
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); padding: 2rem; border-radius: 12px; text-align: center; height: 100%; border: 1px solid #059669;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <h3 style="color: #6ee7b7; font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem;">
                    Complete Visibility
                </h3>
                <p style="color: #a7f3d0; font-size: 0.95rem; line-height: 1.6;">
                    Trace every step of LLM execution with millisecond-level precision
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #7c2d12 0%, #92400e 100%); padding: 2rem; border-radius: 12px; text-align: center; height: 100%; border: 1px solid #c2410c;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="color: #fdba74; font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem;">
                    Real-Time Analytics
                </h3>
                <p style="color: #fed7aa; font-size: 0.95rem; line-height: 1.6;">
                    Live performance metrics, cost tracking, and exportable insights
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin: 4rem 0 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Navigation Cards
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="font-size: 2rem; font-weight: 600; color: #F0F6FC; margin-bottom: 0.5rem;">
                Explore Platform Features
            </h2>
            <p style="color: #8B949E; font-size: 1rem;">
                Select a module to get started
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            st.markdown("""
            <div style="background: #161B22; padding: 2.5rem 2rem; border-radius: 12px; border: 1px solid #30363D; transition: all 0.3s;">
                <div style="font-size: 2.5rem; margin-bottom: 1.5rem; text-align: center;">📈</div>
                <h3 style="color: #58A6FF; font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; text-align: center;">
                    Live Dashboard
                </h3>
                <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.7; margin-bottom: 1.5rem;">
                    Real-time system monitoring with performance metrics, cache analytics, and AI interaction interface
                </p>
                <ul style="color: #C9D1D9; font-size: 0.9rem; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.25rem;">
                    <li>Live performance metrics</li>
                    <li>Cache hit rate tracking</li>
                    <li>Interactive AI chat interface</li>
                    <li>Data export (JSON/CSV)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Open Live Dashboard", key="nav_dashboard", use_container_width=True, type="primary"):
                st.session_state.page = "Live Dashboard"
                st.rerun()
        
        with col2:
            st.markdown("""
            <div style="background: #161B22; padding: 2.5rem 2rem; border-radius: 12px; border: 1px solid #30363D; transition: all 0.3s;">
                <div style="font-size: 2.5rem; margin-bottom: 1.5rem; text-align: center;">🎬</div>
                <h3 style="color: #58A6FF; font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; text-align: center;">
                    Trace Analytics
                </h3>
                <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.7; margin-bottom: 1.5rem;">
                    Step-by-step execution replay with detailed performance breakdown and debugging tools
                </p>
                <ul style="color: #C9D1D9; font-size: 0.9rem; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.25rem;">
                    <li>Execution timeline visualization</li>
                    <li>Latency waterfall analysis</li>
                    <li>Step-by-step trace replay</li>
                    <li>Performance debugging</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Open Trace Analytics", key="nav_traces", use_container_width=True, type="primary"):
                st.session_state.page = "Trace Analytics"
                st.rerun()
        
        with col3:
            st.markdown("""
            <div style="background: #161B22; padding: 2.5rem 2rem; border-radius: 12px; border: 1px solid #30363D; transition: all 0.3s;">
                <div style="font-size: 2.5rem; margin-bottom: 1.5rem; text-align: center;">🔬</div>
                <h3 style="color: #58A6FF; font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; text-align: center;">
                    Request Inspector
                </h3>
                <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.7; margin-bottom: 1.5rem;">
                    Deep-dive request analysis with full context, metadata, and comparative insights
                </p>
                <ul style="color: #C9D1D9; font-size: 0.9rem; line-height: 1.8; margin-bottom: 1.5rem; padding-left: 1.25rem;">
                    <li>Request/response analysis</li>
                    <li>Token and cost breakdown</li>
                    <li>Cache optimization insights</li>
                    <li>Comparative analytics</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Open Request Inspector", key="nav_inspector", use_container_width=True, type="primary"):
                st.session_state.page = "Request Inspector"
                st.rerun()
        
        st.markdown("<div style='margin: 4rem 0 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Technical Features
        st.markdown("""
        <div style="background: #0D1117; padding: 3rem 2rem; border-radius: 12px; border: 1px solid #21262D; margin-bottom: 3rem;">
            <h2 style="font-size: 1.75rem; font-weight: 600; color: #F0F6FC; margin-bottom: 2rem; text-align: center;">
                Enterprise-Grade Architecture
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem;">
                <div>
                    <h4 style="color: #58A6FF; font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">FastAPI Backend</h4>
                    <p style="color: #8B949E; font-size: 0.9rem; line-height: 1.6;">Async/await architecture with production-grade error handling</p>
                </div>
                <div>
                    <h4 style="color: #58A6FF; font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">MongoDB Storage</h4>
                    <p style="color: #8B949E; font-size: 0.9rem; line-height: 1.6;">Scalable trace persistence with flexible querying</p>
                </div>
                <div>
                    <h4 style="color: #58A6FF; font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">Semantic Cache</h4>
                    <p style="color: #8B949E; font-size: 0.9rem; line-height: 1.6;">ChromaDB vector search for intelligent response caching</p>
                </div>
                <div>
                    <h4 style="color: #58A6FF; font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem;">SSE Streaming</h4>
                    <p style="color: #8B949E; font-size: 0.9rem; line-height: 1.6;">Real-time server-sent events for live AI responses</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #6E7681; font-size: 0.875rem; border-top: 1px solid #21262D; margin-top: 3rem;">
            <p style="margin: 0;">Flight Recorder v1.0.0 • Enterprise LLM Observability Platform</p>
            <p style="margin: 0.5rem 0 0 0;">Built for production-scale AI applications</p>
        </div>
        """, unsafe_allow_html=True)
        
        logger.info("Home landing page rendered successfully")
        
    except Exception as e:
        logger.exception("Failed to render Home landing page")
        st.error("Failed to load landing page")
        st.exception(e)

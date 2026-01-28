# -*- coding: utf-8 -*-

import logging
import streamlit as st

# --------------------------------------------------
# Logging setup
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def apply_custom_css():
    """Apply custom CSS for premium SaaS styling."""
    st.markdown("""
    <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main app background */
        .main {
            background-color: #0E1117;
            color: #FAFAFA;
            padding: 0;
        }
        
        /* Remove default padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        /* Card-style containers */
        div[data-testid="stHorizontalBlock"] {
            gap: 1.5rem;
        }
        
        /* Metrics styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 600;
            color: #58A6FF;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.875rem;
            font-weight: 500;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Primary button styling */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Secondary button styling */
        .stButton > button[kind="secondary"] {
            background-color: #21262D;
            color: #C9D1D9;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background-color: #30363D;
            border-color: #58A6FF;
        }
        
        /* Headers */
        h1 {
            color: #F0F6FC;
            font-weight: 600;
            font-size: 2.25rem;
            margin-bottom: 0.5rem;
        }
        
        h2 {
            color: #C9D1D9;
            font-weight: 600;
            font-size: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #21262D;
            padding-bottom: 0.5rem;
        }
        
        h3 {
            color: #C9D1D9;
            font-weight: 500;
            font-size: 1.125rem;
        }
        
        /* Success/Info/Warning boxes */
        .stSuccess {
            background-color: #0D1117;
            border-left: 4px solid #238636;
            color: #7EE787;
            padding: 1rem;
            border-radius: 6px;
        }
        
        .stInfo {
            background-color: #0D1117;
            border-left: 4px solid #1F6FEB;
            color: #79C0FF;
            padding: 1rem;
            border-radius: 6px;
        }
        
        .stWarning {
            background-color: #0D1117;
            border-left: 4px solid #9E6A03;
            color: #F0883E;
            padding: 1rem;
            border-radius: 6px;
        }
        
        /* Input fields */
        .stTextInput > div > div > input {
            background-color: #0D1117;
            border: 1px solid #30363D;
            color: #C9D1D9;
            border-radius: 6px;
            padding: 0.625rem 0.75rem;
            font-size: 0.95rem;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #58A6FF;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.3);
        }
        
        /* Selectbox */
        .stSelectbox > div > div {
            background-color: #0D1117;
            border: 1px solid #30363D;
            color: #C9D1D9;
            border-radius: 6px;
        }
        
        /* Checkbox */
        .stCheckbox {
            color: #C9D1D9;
        }
        
        /* Dividers */
        hr {
            border-color: #21262D;
            margin: 2rem 0;
        }
        
        /* Caption text */
        .css-1kyxreq {
            color: #8B949E;
            font-size: 0.875rem;
        }
        
        /* Tables */
        .dataframe {
            border: 1px solid #30363D;
            border-radius: 6px;
        }
        
        .dataframe th {
            background-color: #161B22;
            color: #C9D1D9;
            font-weight: 600;
            padding: 0.75rem;
        }
        
        .dataframe td {
            background-color: #0D1117;
            color: #C9D1D9;
            padding: 0.75rem;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 6px;
            color: #C9D1D9;
            font-weight: 500;
        }
        
        /* Top navigation bar */
        .top-nav {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 1rem 2rem;
            border-bottom: 1px solid #334155;
            margin: -2rem -2rem 2rem -2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-brand {
            font-size: 1.5rem;
            font-weight: 700;
            color: #58A6FF;
            cursor: pointer;
        }
        
        .nav-links {
            display: flex;
            gap: 1.5rem;
        }
        
        .nav-link {
            color: #94A3B8;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            transition: color 0.2s;
        }
        
        .nav-link:hover {
            color: #58A6FF;
        }
        
        .nav-link.active {
            color: #58A6FF;
            border-bottom: 2px solid #58A6FF;
        }
    </style>
    """, unsafe_allow_html=True)


def render_top_navigation():
    """Render top navigation bar."""
    current_page = st.session_state.get("page", "Home")
    
    # Navigation bar
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("← Flight Recorder", key="nav_home_btn", use_container_width=True, type="secondary"):
            st.session_state.page = "Home"
            st.rerun()
    
    with col2:
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        
        with nav_col1:
            if st.button("Live Dashboard", key="nav_dash", use_container_width=True, 
                        type="primary" if current_page == "Live Dashboard" else "secondary"):
                st.session_state.page = "Live Dashboard"
                st.rerun()
        
        with nav_col2:
            if st.button("Trace Analytics", key="nav_trace", use_container_width=True,
                        type="primary" if current_page == "Trace Analytics" else "secondary"):
                st.session_state.page = "Trace Analytics"
                st.rerun()
        
        with nav_col3:
            if st.button("Request Inspector", key="nav_req", use_container_width=True,
                        type="primary" if current_page == "Request Inspector" else "secondary"):
                st.session_state.page = "Request Inspector"
                st.rerun()
    
    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)


def main() -> None:
    """
    Frontend entry point.
    Premium SaaS-style application with landing page navigation.
    """
    try:
        # --------------------------------------------------
        # Page configuration (MUST be first Streamlit call)
        # --------------------------------------------------
        st.set_page_config(
            page_title="Flight Recorder | Enterprise LLM Observability",
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        
        # Apply custom CSS
        apply_custom_css()
        
        # Initialize session state for navigation
        if "page" not in st.session_state:
            st.session_state.page = "Home"
        
        logger.info(f"Frontend application started - Current page: {st.session_state.page}")

        # --------------------------------------------------
        # Page Routing
        # --------------------------------------------------
        
        current_page = st.session_state.page
        
        if current_page == "Home":
            # Landing page - no navigation bar
            from pages.home import render_home_page
            render_home_page()
            
        elif current_page == "Live Dashboard":
            # Show top navigation
            render_top_navigation()
            from pages.debug_mode import render_debug_dashboard
            render_debug_dashboard()
            
        elif current_page == "Trace Analytics":
            # Show top navigation
            render_top_navigation()
            from pages.flight_recorder import render_flight_recorder_page
            render_flight_recorder_page()
            
        elif current_page == "Request Inspector":
            # Show top navigation
            render_top_navigation()
            from pages.request_details import render_request_details
            render_request_details()
            
        else:
            logger.warning(f"Unknown page: {current_page}")
            st.session_state.page = "Home"
            st.rerun()

    except Exception as exc:
        logger.exception("Unhandled exception in frontend")
        st.error("Something went wrong. Please refresh the page.")
        st.exception(exc)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

import logging
import streamlit as st

# --------------------------------------------------
# Logging setup (frontend-safe)
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Frontend entry point.
    
    Responsibilities:
    - App configuration
    - Sidebar navigation
    - Safe page routing
    
    ❌ No backend calls
    ❌ No business logic
    """
    try:
        # --------------------------------------------------
        # Page configuration (MUST be first Streamlit call)
        # --------------------------------------------------
        st.set_page_config(
            page_title="LLM Flight Recorder",
            page_icon="🛫",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        logger.info("Frontend application started")

        # --------------------------------------------------
        # Sidebar
        # --------------------------------------------------
        st.sidebar.title("🛫 LLM Flight Recorder")
        st.sidebar.markdown("---")
        
        selected_page = st.sidebar.radio(
            label="Navigation",
            options=[
                "Debug Dashboard",
                "Flight Recorder",
                "Request Details",
            ],
        )

        st.sidebar.markdown("---")
        st.sidebar.caption("🚀 Real-time AI with Streaming")
        st.sidebar.caption("Observability for LLM systems")

        # --------------------------------------------------
        # Routing
        # --------------------------------------------------
        if selected_page == "Debug Dashboard":
            logger.info("Navigating to Debug Dashboard")
            from pages.debug_mode import render_debug_dashboard
            render_debug_dashboard()

        elif selected_page == "Flight Recorder":
            logger.info("Navigating to Flight Recorder")
            from pages.flight_recorder import render_flight_recorder
            render_flight_recorder()

        elif selected_page == "Request Details":
            logger.info("Navigating to Request Details")
            from pages.request_details import render_request_details
            render_request_details()


        else:
            logger.warning("Unknown navigation option selected")
            st.warning("Unknown page selected.")

    except Exception as exc:
        logger.exception("Unhandled exception in frontend")
        st.error("Something went wrong in the frontend.")
        st.exception(exc)


if __name__ == "__main__":
    main()

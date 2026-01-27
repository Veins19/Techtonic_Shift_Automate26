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

        logger.info("Frontend application started successfully")

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
        st.sidebar.caption("Observability for LLM systems")

        # --------------------------------------------------
        # Routing (SAFE)
        # --------------------------------------------------
        if selected_page == "Debug Dashboard":
            logger.info("User selected Debug Dashboard")

            try:
                from pages.debug_mode import render_debug_dashboard
                render_debug_dashboard()

            except ModuleNotFoundError as e:
                logger.error("Pages module not found", exc_info=True)
                st.error("Debug Dashboard is not available yet.")
                st.info("Next step: create pages/debug_mode.py")

            except Exception as e:
                logger.exception("Failed to load Debug Dashboard")
                st.error("Failed to load Debug Dashboard")
                st.exception(e)

        elif selected_page == "Flight Recorder":
            logger.info("User selected Flight Recorder")
            st.info("🚧 Flight Recorder page not implemented yet.")
            st.write("This page will replay traces step-by-step.")

        elif selected_page == "Request Details":
            logger.info("User selected Request Details")
            st.info("🚧 Request Details page not implemented yet.")
            st.write("This page will show prompt, response, and metrics.")

        else:
            logger.warning("Unknown navigation state")
            st.warning("Unknown page selected.")

    except Exception as e:
        logger.exception("Unhandled exception in frontend")
        st.error("Something went wrong in the frontend.")
        st.exception(e)


if __name__ == "__main__":
    main()

import streamlit as st
import logging

# --------------------------------------------------
# Basic logging setup (frontend-safe)
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """
    Frontend entry point.
    Handles only:
    - Page configuration
    - Sidebar navigation
    - Page routing

    NO backend calls
    NO business logic
    """

    try:
        # --------------------------------------------------
        # Page configuration
        # --------------------------------------------------
        st.set_page_config(
            page_title="LLM Flight Recorder",
            page_icon="🛫",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        logger.info("Frontend app started")

        # --------------------------------------------------
        # Sidebar navigation
        # --------------------------------------------------
        st.sidebar.title("🛫 LLM Flight Recorder")
        st.sidebar.markdown("---")

        selected_page = st.sidebar.radio(
            label="Navigation",
            options=[
                "Debug Dashboard",
                "Flight Recorder",
                "Request Details"
            ]
        )

        st.sidebar.markdown("---")
        st.sidebar.caption("Observability for LLM systems")

        # --------------------------------------------------
        # Page routing
        # --------------------------------------------------
        if selected_page == "Debug Dashboard":
            from pages.debug_mode import render_debug_dashboard
            render_debug_dashboard()

        elif selected_page == "Flight Recorder":
            st.info("Flight Recorder page will be added next.")
            st.write("This page will replay traces step-by-step.")

        elif selected_page == "Request Details":
            st.info("Request Details page will be added later.")
            st.write("This page will show prompt, response, and metrics.")

    except Exception as e:
        logger.exception("Unhandled exception in frontend app")
        st.error("Something went wrong in the frontend.")
        st.exception(e)


if __name__ == "__main__":
    main()
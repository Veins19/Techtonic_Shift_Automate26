import logging
from typing import List, Dict, Any

import streamlit as st

# --------------------------------------------------
# Logger setup
# --------------------------------------------------
logger = logging.getLogger(__name__)


def render_trace_viewer(
    trace_id: str,
    steps: List[Dict[str, Any]],
):
    """
    Renders a step-by-step trace viewer.

    Args:
        trace_id: Unique trace identifier
        steps: List of steps, where each step contains:
            - name (str): step name (e.g. retrieval, generation)
            - status (str): success | error
            - latency_ms (int)
            - details (str): optional human-readable details

    This component:
    - Renders UI only
    - Does NOT fetch data
    - Does NOT mutate data
    """

    try:
        st.subheader(f"🧩 Trace Viewer — {trace_id}")
        st.caption("Step-by-step execution timeline")

        if not steps:
            st.info("No steps available for this trace.")
            logger.info("render_trace_viewer called with empty steps")
            return

        for idx, step in enumerate(steps, start=1):
            step_name = step.get("name", "unknown")
            status = step.get("status", "unknown")
            latency = step.get("latency_ms", 0)
            details = step.get("details", "")

            # Status styling
            if status == "success":
                status_icon = "✅"
            elif status == "error":
                status_icon = "❌"
            else:
                status_icon = "⚪"

            with st.container():
                st.markdown(
                    f"""
                    ### {status_icon} Step {idx}: {step_name}
                    - **Status:** `{status}`
                    - **Latency:** `{latency} ms`
                    """
                )

                if details:
                    with st.expander("Details"):
                        st.write(details)

                st.markdown("---")

        logger.info(
            "Rendered trace viewer",
            extra={
                "trace_id": trace_id,
                "steps_count": len(steps),
            },
        )

    except Exception as e:
        logger.exception("Failed to render trace viewer")
        st.error("Failed to render trace viewer")
        st.exception(e)
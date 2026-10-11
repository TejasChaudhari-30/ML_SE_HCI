import streamlit as st
import pandas as pd

def clear_history_callback():
    """Callback function to safely clear recent checks history before script run."""
    st.session_state["recent_checks"] = []

def render_recent_checks():
    """Renders the Recent Checks tab interface."""
    st.header("📋 Recent Checks")
    st.write("Your recent job-posting analyses from this session.")

    recent_checks = st.session_state.get("recent_checks", [])

    if not recent_checks:
        st.info("No recent checks yet. Analyze a job posting to see it here.")
    else:
        # Display most recent check first
        reversed_history = recent_checks[::-1]
        df = pd.DataFrame(reversed_history)

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.button("🗑️ Clear History", on_click=clear_history_callback)

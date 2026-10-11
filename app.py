import streamlit as st
from utils.session import init_session_state
from utils.theme import render_header
from ui.home import render_home
from ui.check_posting import render_check_posting
from ui.recent_checks import render_recent_checks
from ui.about import render_about

st.set_page_config(page_title="JobShield", page_icon="🛡️", layout="centered")

# Initialize session state
init_session_state()

# Render top header & apply design theme
render_header()

# Main navigation options
nav_options = ["Home", "Check Posting", "Recent Checks", "About"]

# Render navigation via segmented control
selected_nav = st.segmented_control(
    "Navigation",
    options=nav_options,
    key="nav_selection",
    label_visibility="collapsed"
)

# Handle deselection fallback and synchronize active_page
if not selected_nav:
    selected_nav = "Home"
    st.session_state["nav_selection"] = "Home"
st.session_state["active_page"] = selected_nav

# Render selected page
if selected_nav == "Home":
    render_home()
elif selected_nav == "Check Posting":
    render_check_posting()
elif selected_nav == "Recent Checks":
    render_recent_checks()
elif selected_nav == "About":
    render_about()

st.markdown("---")
st.caption("JobShield uses a hybrid ML model (SVM + Logistic Regression) trained on the EMSCAD dataset, augmented with current scam pattern examples. This tool is a decision-support aid, not a guarantee — always verify independently.")
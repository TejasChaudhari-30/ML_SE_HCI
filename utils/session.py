import streamlit as st
from datetime import datetime

def init_session_state():
    """Initializes Streamlit session state variables if they do not exist."""
    defaults = {
        "active_page": "Home",
        "nav_selection": "Home",
        "input_mode": "upload",
        "last_processed_file_id": None,
        "ocr_status": None,
        "ocr_extracted_text": "",
        "form_version": 0,
        "show_clear_confirm": False,
        "has_analysis": False,
        "feedback_given": None,
        "analysis_result": None,
        "fraud_reasons": None,
        "genuine_reasons": None,
        "structured_contributions": None,
        "summary_sentence": None,
        "analyzed_job_text": "",
        "analyzed_has_salary": False,
        "analyzed_has_logo": False,
        "analyzed_is_remote": False,
        "analyzed_has_questions": False,
        "recent_checks": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def add_recent_check(job_text, result_label, confidence_pct):
    """
    Adds a new analysis record to st.session_state.recent_checks.
    """
    if "recent_checks" not in st.session_state:
        st.session_state["recent_checks"] = []

    # Clean text snippet (60-100 characters max)
    clean_text = " ".join(job_text.strip().split())
    if len(clean_text) > 80:
        snippet = clean_text[:77] + "..."
    else:
        snippet = clean_text

    # Format timestamp e.g. "02 Oct 2026, 08:15 PM"
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Format result label cleanly
    if "FRAUDULENT" in result_label.upper():
        formatted_result = "Likely Fraudulent"
    elif "GENUINE" in result_label.upper():
        formatted_result = "Likely Genuine"
    else:
        formatted_result = "Uncertain"

    conf_str = f"{confidence_pct:.1f}%"

    record = {
        "Time": timestamp,
        "Job Posting": snippet,
        "Result": formatted_result,
        "Confidence": conf_str,
    }

    st.session_state["recent_checks"].append(record)

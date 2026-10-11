import streamlit as st

DARK_THEME = {
    "bg_color": "#151824",
    "card_bg": "#1D2231",
    "secondary_surface": "#252B3B",
    "card_border": "#343B50",
    "card_shadow": "0 4px 20px rgba(0, 0, 0, 0.35)",
    "glow_shadow": "0 0 16px rgba(139, 131, 246, 0.25)",
    "text_primary": "#E8ECF5",
    "text_secondary": "#A0A9BC",
    "accent": "#8B83F6",
    "accent_hover": "#786ef4",
    "highlight_fraud_bg": "#5c2b2b",
    "highlight_fraud_text": "#ff6b6b",
    "highlight_genuine_bg": "#2b5c3a",
    "highlight_genuine_text": "#51cf66",
    "highlight_container_bg": "#1D2231",
    "highlight_container_border": "#343B50",
    "highlight_container_text": "#E8ECF5",
}

LIGHT_THEME = {
    "bg_color": "#F1F3F8",
    "card_bg": "#F9FAFD",
    "secondary_surface": "#ffffff",
    "card_border": "#DDE2EF",
    "card_shadow": "0 4px 16px rgba(32, 40, 59, 0.04)",
    "glow_shadow": "0 0 12px rgba(99, 91, 219, 0.15)",
    "text_primary": "#20283B",
    "text_secondary": "#697386",
    "accent": "#635BDB",
    "accent_hover": "#5249cc",
    "highlight_fraud_bg": "#fee2e2",
    "highlight_fraud_text": "#991b1b",
    "highlight_genuine_bg": "#dcfce7",
    "highlight_genuine_text": "#166534",
    "highlight_container_bg": "#F9FAFD",
    "highlight_container_border": "#DDE2EF",
    "highlight_container_text": "#20283B",
}

def get_theme():
    """Returns the current active theme dictionary."""
    theme_name = st.session_state.get("theme", "dark")
    return LIGHT_THEME if theme_name == "light" else DARK_THEME

def apply_theme_css():
    """Injects dynamic CSS variables and styling overrides based on current theme."""
    t = get_theme()

    css = f"""
    <style>
        :root {{
            --bg-color: {t["bg_color"]};
            --card-bg: {t["card_bg"]};
            --secondary-surface: {t["secondary_surface"]};
            --card-border: {t["card_border"]};
            --card-shadow: {t["card_shadow"]};
            --glow-shadow: {t["glow_shadow"]};
            --text-primary: {t["text_primary"]};
            --text-secondary: {t["text_secondary"]};
            --accent: {t["accent"]};
            --accent-hover: {t["accent_hover"]};
        }}

        /* App Background */
        .stApp {{
            background-color: {t["bg_color"]} !important;
            color: {t["text_primary"]} !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* General Typography */
        h1, h2, h3, h4, h5, h6, label, p, span, div {{
            color: {t["text_primary"]};
        }}

        p, .stMarkdown p {{
            color: {t["text_primary"]} !important;
        }}

        .stCaption, small, .caption {{
            color: {t["text_secondary"]} !important;
        }}

        /* Cards & Containers */
        div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="background"] {{
            background-color: {t["card_bg"]} !important;
            border: 1px solid {t["card_border"]} !important;
            border-radius: 12px !important;
            box-shadow: {t["card_shadow"]} !important;
        }}

        /* Text Area */
        .stTextArea textarea {{
            background-color: {t["card_bg"]} !important;
            color: {t["text_primary"]} !important;
            border: 1px solid {t["card_border"]} !important;
            border-radius: 10px !important;
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }}
        .stTextArea textarea:focus {{
            border-color: {t["accent"]} !important;
            box-shadow: 0 0 0 2px {t["accent"]}44 !important;
        }}

        /* Checkboxes */
        div[data-testid="stCheckbox"] label span {{
            color: {t["text_primary"]} !important;
            font-weight: 500 !important;
        }}

        /* Buttons */
        .stButton button {{
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out !important;
        }}
        .stButton button[kind="primary"] {{
            background-color: {t["accent"]} !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: {t["glow_shadow"]} !important;
        }}
        .stButton button[kind="primary"]:hover {{
            background-color: {t["accent_hover"]} !important;
        }}
        .stButton button[kind="secondary"] {{
            background-color: {t["card_bg"]} !important;
            color: {t["text_primary"]} !important;
            border: 1px solid {t["card_border"]} !important;
        }}
        .stButton button[kind="secondary"]:hover {{
            border-color: {t["accent"]} !important;
            color: {t["accent"]} !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px !important;
            background-color: {t["card_bg"]} !important;
            padding: 6px 10px !important;
            border-radius: 10px !important;
            border: 1px solid {t["card_border"]} !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 40px !important;
            border-radius: 6px !important;
            color: {t["text_secondary"]} !important;
            font-weight: 600 !important;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {t["accent"]}20 !important;
            color: {t["accent"]} !important;
            box-shadow: {t["glow_shadow"]} !important;
        }}

        /* DataFrame / Tables */
        .stDataFrame {{
            background-color: {t["card_bg"]} !important;
            border: 1px solid {t["card_border"]} !important;
            border-radius: 10px !important;
        }}

        /* Status Widget */
        div[data-testid="stStatusWidget"] {{
            background-color: {t["card_bg"]} !important;
            border: 1px solid {t["card_border"]} !important;
            border-radius: 10px !important;
        }}

        /* Segmented Control Navigation */
        div[data-testid="stSegmentedControl"] {{
            background-color: {t["card_bg"]} !important;
            border: 1px solid {t["card_border"]} !important;
            border-radius: 12px !important;
            padding: 4px !important;
            box-shadow: {t["card_shadow"]} !important;
            margin-bottom: 24px !important;
        }}
        div[data-testid="stSegmentedControl"] button {{
            border-radius: 8px !important;
            font-weight: 600 !important;
            color: {t["text_secondary"]} !important;
            border: none !important;
        }}
        div[data-testid="stSegmentedControl"] button[aria-checked="true"] {{
            background-color: {t["accent"]}25 !important;
            color: {t["accent"]} !important;
            box-shadow: {t["glow_shadow"]} !important;
        }}

        /* Modal Dialog */
        div[data-testid="stDialog"] {{
            background-color: {t["card_bg"]} !important;
            color: {t["text_primary"]} !important;
            border: 1px solid {t["card_border"]} !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.45) !important;
        }}

        /* File Uploader */
        div[data-testid="stFileUploader"] {{
            background-color: {t["card_bg"]} !important;
            border: 1px dashed {t["card_border"]} !important;
            border-radius: 12px !important;
            padding: 14px !important;
            box-shadow: {t["card_shadow"]} !important;
        }}
        div[data-testid="stFileUploader"] section {{
            background-color: {t["card_bg"]} !important;
        }}

        /* Image Display */
        div[data-testid="stImage"] img {{
            border-radius: 10px !important;
            border: 1px solid {t["card_border"]} !important;
            box-shadow: {t["card_shadow"]} !important;
        }}

        /* Dividers */
        hr {{
            border-color: {t["card_border"]} !important;
            margin: 1.5rem 0 !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_header():
    """Renders the top application header with theme toggle."""
    apply_theme_css()
    current_theme = st.session_state.get("theme", "dark")
    t = get_theme()

    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px;">
                <div style="font-size: 2.2rem; background: {t['accent']}22; padding: 10px 14px; border-radius: 12px; border: 1px solid {t['accent']}44; box-shadow: {t['glow_shadow']};">🛡️</div>
                <div>
                    <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; color: {t['text_primary']};">JobShield</h1>
                    <p style="margin: 0; font-size: 0.95rem; font-weight: 500; color: {t['text_secondary']};">Hybrid ML Job Posting Fraud Detector</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_h2:
        st.write("") # vertical spacing
        toggle_label = "☀️ Light Mode" if current_theme == "dark" else "🌙 Dark Mode"
        if st.button(toggle_label, key="theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "light" if current_theme == "dark" else "dark"
            st.rerun()

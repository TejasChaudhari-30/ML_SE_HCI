import streamlit as st
from utils.theme import get_theme

def go_to_check_posting():
    """Navigates to the Check Posting tab."""
    st.session_state["active_page"] = "Check Posting"
    st.session_state["nav_selection"] = "Check Posting"

def go_to_about():
    """Navigates to the About tab."""
    st.session_state["active_page"] = "About"
    st.session_state["nav_selection"] = "About"

def render_home():
    """Renders the JobShield SaaS Homepage."""
    t = get_theme()

    # Hero Section
    st.markdown(
        f"""
        <div style="text-align: center; padding: 36px 12px 24px 12px;">
            <div style="display: inline-block; padding: 6px 16px; border-radius: 20px; background: {t['accent']}18; border: 1px solid {t['accent']}33; margin-bottom: 18px;">
                <span style="font-size: 0.88rem; font-weight: 600; color: {t['accent']};">🛡️ Hybrid ML Fraud Detection</span>
            </div>
            <h1 style="font-size: 2.7rem; font-weight: 800; line-height: 1.2; letter-spacing: -0.03em; margin: 0 0 16px 0; color: {t['text_primary']};">
                Find the warning signs<br><span style="color: {t['accent']};">before you apply.</span>
            </h1>
            <p style="font-size: 1.12rem; max-width: 600px; margin: 0 auto 28px auto; line-height: 1.6; color: {t['text_secondary']};">
                Analyze job postings with machine learning to identify potential fraud indicators and make more informed career decisions.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Hero Action Buttons
    col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
    with col_cta2:
        btn_c1, btn_c2 = st.columns([1.2, 1])
        with btn_c1:
            st.button(
                "🔍 Check a Job Posting",
                type="primary",
                use_container_width=True,
                on_click=go_to_check_posting,
                key="home_primary_cta"
            )
        with btn_c2:
            st.button(
                "💡 How It Works",
                use_container_width=True,
                on_click=go_to_about,
                key="home_secondary_cta"
            )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # 3-Step Process Section
    st.markdown(
        f"""
        <div style="margin-top: 16px; margin-bottom: 24px;">
            <h3 style="font-size: 1.4rem; font-weight: 700; text-align: center; margin-bottom: 6px; color: {t['text_primary']};">
                How JobShield Works
            </h3>
            <p style="text-align: center; font-size: 0.95rem; color: {t['text_secondary']}; margin-bottom: 24px;">
                A simple 3-step screening process designed for job seekers
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    step_col1, step_col2, step_col3 = st.columns(3)
    with step_col1:
        st.markdown(
            f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 22px 18px; height: 100%; box-shadow: {t['card_shadow']};">
                <div style="font-size: 1.8rem; margin-bottom: 12px;">📋</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: {t['accent']}; text-transform: uppercase; margin-bottom: 4px;">Step 1</div>
                <h4 style="margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 700; color: {t['text_primary']};">Paste a Job Posting</h4>
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                    Enter the job description, title, requirements, and verify optional structural signals.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with step_col2:
        st.markdown(
            f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 22px 18px; height: 100%; box-shadow: {t['card_shadow']};">
                <div style="font-size: 1.8rem; margin-bottom: 12px;">⚙️</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: {t['accent']}; text-transform: uppercase; margin-bottom: 4px;">Step 2</div>
                <h4 style="margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 700; color: {t['text_primary']};">Analyze Warning Signs</h4>
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                    Our hybrid ML ensemble inspects linguistic fraud patterns, vocabulary risk, and metadata features.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with step_col3:
        st.markdown(
            f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 22px 18px; height: 100%; box-shadow: {t['card_shadow']};">
                <div style="font-size: 1.8rem; margin-bottom: 12px;">🛡️</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: {t['accent']}; text-transform: uppercase; margin-bottom: 4px;">Step 3</div>
                <h4 style="margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 700; color: {t['text_primary']};">Review & Protect</h4>
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                    Get an instant fraud probability rating, in-text word highlighting, safety checklist, and clear guidance.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Feature Highlights Section
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h3 style="font-size: 1.4rem; font-weight: 700; text-align: center; margin-bottom: 6px; color: {t['text_primary']};">
                Key Platform Capabilities
            </h3>
            <p style="text-align: center; font-size: 0.95rem; color: {t['text_secondary']};">
                Transparent decision support powered by machine learning
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    feat_col1, feat_col2 = st.columns(2)
    with feat_col1:
        st.markdown(
            f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 20px; margin-bottom: 16px; box-shadow: {t['card_shadow']};">
                <div style="display: flex; align-items: flex-start; gap: 14px;">
                    <div style="font-size: 1.6rem; background: {t['accent']}18; padding: 10px; border-radius: 10px;">🤖</div>
                    <div>
                        <h4 style="margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 700; color: {t['text_primary']};">ML-Based Fraud Detection</h4>
                        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                            Hybrid classification combining Support Vector Machine (SVM) and Logistic Regression with TF-IDF text features.
                        </p>
                    </div>
                </div>
            </div>
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 20px; box-shadow: {t['card_shadow']};">
                <div style="display: flex; align-items: flex-start; gap: 14px;">
                    <div style="font-size: 1.6rem; background: {t['accent']}18; padding: 10px; border-radius: 10px;">🔍</div>
                    <div>
                        <h4 style="margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 700; color: {t['text_primary']};">In-Text Word Highlighting</h4>
                        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                            Direct visual breakdown highlighting suspicious phrases in red and legitimacy indicators in green.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with feat_col2:
        st.markdown(
            f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 20px; margin-bottom: 16px; box-shadow: {t['card_shadow']};">
                <div style="display: flex; align-items: flex-start; gap: 14px;">
                    <div style="font-size: 1.6rem; background: {t['accent']}18; padding: 10px; border-radius: 10px;">✅</div>
                    <div>
                        <h4 style="margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 700; color: {t['text_primary']};">Plain-Language Safety Checklist</h4>
                        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                            Instant review of structural posting signals: salary transparency, company logo presence, and screening questions.
                        </p>
                    </div>
                </div>
            </div>
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 14px; padding: 20px; box-shadow: {t['card_shadow']};">
                <div style="display: flex; align-items: flex-start; gap: 14px;">
                    <div style="font-size: 1.6rem; background: {t['accent']}18; padding: 10px; border-radius: 10px;">⏱️</div>
                    <div>
                        <h4 style="margin: 0 0 6px 0; font-size: 1.05rem; font-weight: 700; color: {t['text_primary']};">Session Recent Checks</h4>
                        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: {t['text_secondary']};">
                            Review your recent analyses from this session in a reverse-chronological history log with clean scores and timestamps.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Safety Disclaimer Callout Card
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-left: 4px solid {t['accent']}; border-radius: 10px; padding: 18px 22px; margin-top: 8px; box-shadow: {t['card_shadow']};">
            <h5 style="margin: 0 0 6px 0; font-size: 0.98rem; font-weight: 700; color: {t['text_primary']};">
                ⚠️ Academic Decision-Support Screening Aid
            </h5>
            <p style="margin: 0; font-size: 0.88rem; line-height: 1.5; color: {t['text_secondary']};">
                JobShield provides a screening assessment based on machine-learning pattern recognition. It is not an absolute guarantee that a job posting is genuine or fraudulent. Always independently verify employers, official domains, and interview requests.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

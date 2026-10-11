import time
import streamlit as st
from model.predictor import predict_job_posting
from model.explanation import (
    get_flagged_reasons,
    get_structured_feature_contributions,
    generate_plain_language_summary,
    highlight_flagged_text,
)
from utils.session import add_recent_check
from utils.ocr import extract_text_from_image
from utils.theme import get_theme

# Define sample texts
GENUINE_SAMPLE = """Senior Software Engineer - Cloud Infrastructure
Acme Tech Solutions | Full-time | Remote

About the Role:
We are looking for an experienced Senior Software Engineer to join our core cloud platform team. In this role, you will design, build, and maintain scalable microservices using Python, Go, and AWS.

Responsibilities:
- Build and maintain infrastructure as code using Terraform and Kubernetes.
- Collaborate with cross-functional product teams to deliver high-availability services.
- Participate in code reviews and mentor junior developers.

Requirements:
- 5+ years of experience in backend software development and cloud architecture.
- Strong proficiency with containerization, CI/CD pipelines, and relational databases.
- Bachelor's degree in Computer Science or equivalent practical experience.

Benefits:
- Competitive salary range ($130,000 - $160,000 / year).
- Comprehensive health, dental, and vision insurance with 401(k) matching.
- Paid parental leave and professional development stipend."""

SCAM_SAMPLE = """URGENT NEED! Data Entry Specialist - Earn $500/day Work From Home!
Global Logistics LLC | Part-time / Full-time | Immediate Start

No experience required! Earn money fast with unlimited commission! We are hiring immediately for remote data entry clerks. Wire transfer payments sent weekly into your account.

Responsibilities:
- Transfer customer data into online spreadsheets.
- Process wire payments, financial transactions, and package forwarding.

Requirements:
- Must have a computer and internet access.
- Must pay a $150 refundable processing fee for home equipment setup kit.

How to Apply:
To apply, send your full name, phone number, and bank account details directly to our hiring manager via Telegram/WhatsApp immediately!"""

BORDERLINE_SAMPLE = """Online Marketing Associate & Product Evaluator
Dynamic Growth Media | Flexible Hours | Remote

We are expanding our digital marketing operations and seeking motivated individuals to assist with online marketing, product reviews, and social media promotion. High earning potential based on daily task completion.

Duties include evaluating partner products, posting promotional links, and submitting brief weekly activity reports. Flexible scheduling makes this ideal for students or freelancers seeking extra income.

Qualifications:
- Basic computer proficiency and active social media accounts.
- Strong communication skills and self-motivation.

Contact us via email to receive the starter orientation guide."""

def get_form_keys():
    """Returns dynamic widget keys based on the current form version in session state."""
    v = st.session_state.get("form_version", 0)
    return {
        "job_text": f"job_text_v{v}",
        "has_salary": f"has_salary_v{v}",
        "has_logo": f"has_logo_v{v}",
        "is_remote": f"is_remote_v{v}",
        "has_questions": f"has_questions_v{v}",
        "file_uploader": f"file_uploader_v{v}",
    }

def clear_form_callback():
    """Callback function to reset form inputs via form versioning and clear analysis state."""
    st.session_state["form_version"] = st.session_state.get("form_version", 0) + 1
    st.session_state["persistent_job_text"] = ""
    st.session_state["last_processed_file_id"] = None
    st.session_state["ocr_status"] = None
    st.session_state["ocr_extracted_text"] = ""
    st.session_state["has_analysis"] = False
    st.session_state["feedback_given"] = None
    st.session_state["analysis_result"] = None
    st.session_state["fraud_reasons"] = None
    st.session_state["genuine_reasons"] = None
    st.session_state["structured_contributions"] = None
    st.session_state["summary_sentence"] = None
    st.session_state["analyzed_job_text"] = ""
    st.session_state["analyzed_has_salary"] = False
    st.session_state["analyzed_has_logo"] = False
    st.session_state["analyzed_is_remote"] = False
    st.session_state["analyzed_has_questions"] = False

def on_dismiss_clear():
    st.session_state["show_clear_confirm"] = False

@st.dialog("Clear this analysis?", on_dismiss=on_dismiss_clear)
def confirm_clear_dialog():
    """Confirmation modal dialog before resetting form and analysis."""
    st.write(
        "This will remove the current job posting, selected options, prediction, explanation, and feedback. "
        "Your Recent Checks history will remain unchanged."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True, key="cancel_clear_btn"):
            st.session_state["show_clear_confirm"] = False
            st.rerun()
    with col2:
        if st.button("Clear Everything", type="primary", use_container_width=True, key="confirm_clear_btn"):
            st.session_state["show_clear_confirm"] = False
            clear_form_callback()
            st.rerun()

def render_check_posting():
    """Renders the redesigned Check Posting interface with Screenshot OCR and Text Review."""
    keys = get_form_keys()
    t = get_theme()

    st.markdown("## Check a Job Posting")
    st.caption("Upload a screenshot or paste job text to evaluate potential fraud risk indicators.")

    with st.expander("ℹ️ How does JobShield work?"):
        st.write(
            "JobShield analyzes the text of a job posting using Natural Language Processing. "
            "It converts text into numerical features using TF-IDF, then evaluates those features "
            "with a combined Machine Learning ensemble (SVM and Logistic Regression) to assess fraud risk."
        )

    # 1. Two side-by-side selectable input cards
    current_mode = st.session_state.get("input_mode", "upload")
    is_upload = (current_mode == "upload")

    col_card1, col_card2 = st.columns(2)
    with col_card1:
        border1 = f"2px solid {t['accent']}" if is_upload else f"1px solid {t['card_border']}"
        bg1 = f"{t['accent']}18" if is_upload else t['card_bg']
        shadow1 = t['glow_shadow'] if is_upload else t['card_shadow']
        badge1 = f"<span style='background: {t['accent']}; color: #ffffff; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>ACTIVE</span>" if is_upload else ""
        st.markdown(
            f"""
            <div style="border: {border1}; background: {bg1}; border-radius: 14px; padding: 18px 20px; box-shadow: {shadow1}; min-height: 105px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <div style="font-size: 1.8rem;">🖼️</div>
                    <div>{badge1}</div>
                </div>
                <div style="font-size: 1.12rem; font-weight: 700; color: {t['text_primary']}; margin-bottom: 4px;">Upload Screenshot</div>
                <div style="font-size: 0.88rem; color: {t['text_secondary']};">JPG, PNG or screenshot</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("✓ Upload Selected" if is_upload else "Select Screenshot Upload", key="btn_mode_upload", type="primary" if is_upload else "secondary", use_container_width=True):
            st.session_state["input_mode"] = "upload"
            st.rerun()

    with col_card2:
        border2 = f"2px solid {t['accent']}" if not is_upload else f"1px solid {t['card_border']}"
        bg2 = f"{t['accent']}18" if not is_upload else t['card_bg']
        shadow2 = t['glow_shadow'] if not is_upload else t['card_shadow']
        badge2 = f"<span style='background: {t['accent']}; color: #ffffff; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>ACTIVE</span>" if not is_upload else ""
        st.markdown(
            f"""
            <div style="border: {border2}; background: {bg2}; border-radius: 14px; padding: 18px 20px; box-shadow: {shadow2}; min-height: 105px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <div style="font-size: 1.8rem;">📋</div>
                    <div>{badge2}</div>
                </div>
                <div style="font-size: 1.12rem; font-weight: 700; color: {t['text_primary']}; margin-bottom: 4px;">Paste Job Text</div>
                <div style="font-size: 0.88rem; color: {t['text_secondary']};">Existing input method</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("✓ Paste Selected" if not is_upload else "Select Paste Job Text", key="btn_mode_paste", type="primary" if not is_upload else "secondary", use_container_width=True):
            st.session_state["input_mode"] = "paste"
            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. Selected input method panel
    if is_upload:
        uploaded_file = st.file_uploader(
            "Upload Job Posting Screenshot",
            type=["png", "jpg", "jpeg"],
            key=keys["file_uploader"],
            help="Upload a screenshot (PNG, JPG, JPEG) to extract job text automatically with local EasyOCR."
        )

        if uploaded_file is not None:
            st.image(uploaded_file, caption=f"Screenshot Preview: {uploaded_file.name}", use_container_width=True)
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.get("last_processed_file_id") != file_id:
                with st.spinner("🔄 Extracting text from screenshot using EasyOCR..."):
                    ok, text, msg = extract_text_from_image(uploaded_file)
                    st.session_state["last_processed_file_id"] = file_id
                    st.session_state["ocr_status"] = {"success": ok, "message": msg}
                    if ok:
                        st.session_state[keys["job_text"]] = text
                        st.session_state["persistent_job_text"] = text
                        st.session_state["ocr_extracted_text"] = text
                    st.rerun()

        # Processing status panel for Upload mode
        ocr_status = st.session_state.get("ocr_status")
        if uploaded_file is not None and ocr_status:
            if ocr_status["success"]:
                st.markdown(
                    f"""
                    <div style="background: {t['card_bg']}; border: 1px solid {t['accent']}55; border-left: 4px solid #10b981; border-radius: 10px; padding: 14px 18px; margin: 12px 0 20px 0; box-shadow: {t['card_shadow']};">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 1.3rem;">✅</span>
                            <div>
                                <div style="font-weight: 700; color: {t['text_primary']};">Text extracted successfully</div>
                                <div style="font-size: 0.88rem; color: {t['text_secondary']};">{ocr_status['message']} Review and edit below before running analysis.</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="background: {t['card_bg']}; border: 1px solid #ef444455; border-left: 4px solid #ef4444; border-radius: 10px; padding: 14px 18px; margin: 12px 0 20px 0; box-shadow: {t['card_shadow']};">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-size: 1.3rem;">⚠️</span>
                            <div>
                                <div style="font-weight: 700; color: #ef4444;">Extraction notice</div>
                                <div style="font-size: 0.88rem; color: {t['text_secondary']};">{ocr_status['message']}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                f"""
                <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-left: 4px solid {t['accent']}; border-radius: 10px; padding: 14px 18px; margin: 12px 0 20px 0; box-shadow: {t['card_shadow']};">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 1.3rem;">📸</span>
                        <div>
                            <div style="font-weight: 700; color: {t['text_primary']};">Upload Screenshot to Extract Text</div>
                            <div style="font-size: 0.88rem; color: {t['text_secondary']};">Select or drop a PNG, JPG, or JPEG file above. EasyOCR will process the image in memory and populate the review area below.</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:
        # Paste Mode: Sample Buttons
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("📄 Sample: Genuine Job", use_container_width=True):
                st.session_state[keys["job_text"]] = GENUINE_SAMPLE
                st.session_state["persistent_job_text"] = GENUINE_SAMPLE
                st.session_state[keys["has_salary"]] = True
                st.session_state[keys["has_logo"]] = True
                st.session_state[keys["is_remote"]] = True
                st.session_state[keys["has_questions"]] = True
                st.rerun()

        with col_s2:
            if st.button("⚠️ Sample: Common Scam", use_container_width=True):
                st.session_state[keys["job_text"]] = SCAM_SAMPLE
                st.session_state["persistent_job_text"] = SCAM_SAMPLE
                st.session_state[keys["has_salary"]] = False
                st.session_state[keys["has_logo"]] = False
                st.session_state[keys["is_remote"]] = True
                st.session_state[keys["has_questions"]] = False
                st.rerun()

        with col_s3:
            if st.button("🤔 Sample: Borderline Case", use_container_width=True):
                st.session_state[keys["job_text"]] = BORDERLINE_SAMPLE
                st.session_state["persistent_job_text"] = BORDERLINE_SAMPLE
                st.session_state[keys["has_salary"]] = False
                st.session_state[keys["has_logo"]] = False
                st.session_state[keys["is_remote"]] = True
                st.session_state[keys["has_questions"]] = False
                st.rerun()

        # Processing status panel for Paste mode
        st.markdown(
            f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-left: 4px solid {t['accent']}; border-radius: 10px; padding: 14px 18px; margin: 12px 0 20px 0; box-shadow: {t['card_shadow']};">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.3rem;">📋</span>
                    <div>
                        <div style="font-weight: 700; color: {t['text_primary']};">Direct Text Entry Ready</div>
                        <div style="font-size: 0.88rem; color: {t['text_secondary']};">Paste job details directly into the review area below or select a sample above to test.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. Review Section containing extracted or pasted text
    st.markdown("### Review Job Posting Text")
    st.caption("Inspect and adjust the job posting text before analyzing fraud risk. OCR text can be corrected directly here.")

    # Synchronize persistent text with widget key if needed
    if keys["job_text"] not in st.session_state or not st.session_state[keys["job_text"]]:
        if st.session_state.get("persistent_job_text"):
            st.session_state[keys["job_text"]] = st.session_state["persistent_job_text"]

    job_text = st.text_area(
        "Job Posting Text",
        height=200,
        placeholder="Paste or review the job title, description, requirements, and benefits here...",
        key=keys["job_text"]
    )

    if job_text:
        st.session_state["persistent_job_text"] = job_text

    cleaned_input = job_text.strip()
    if len(cleaned_input) == 0:
        st.caption("ℹ️ Waiting for job posting text (enter or extract at least 30 characters).")
    elif len(cleaned_input) < 30:
        st.caption(f"⚠️ Text too short ({len(cleaned_input)}/30 chars). Please provide at least 30 characters for analysis.")
    else:
        st.caption(f"✓ Ready for analysis: {len(cleaned_input.split())} words ({len(cleaned_input)} characters).")

    # 4. Optional Structural Indicators
    col1, col2 = st.columns(2)
    with col1:
        has_salary = st.checkbox("Salary range mentioned?", key=keys["has_salary"])
        has_logo = st.checkbox("Company logo/profile present?", key=keys["has_logo"])
    with col2:
        is_remote = st.checkbox("Remote / Work from home?", key=keys["is_remote"])
        has_questions = st.checkbox("Screening questions included?", key=keys["has_questions"])

    st.caption("ℹ️ *Note: These indicators are optional signals to verify. Missing details (e.g. salary or logo) do not automatically indicate fraud.*")

    # Disable button if input text is empty or shorter than 30 characters
    is_btn_disabled = len(cleaned_input) < 30

    # 5. Prominent Full-Width Purple Analyze Button
    check_clicked = st.button(
        "🔍 Analyze Job Posting",
        type="primary",
        disabled=is_btn_disabled,
        use_container_width=True,
        key="analyze_posting_btn"
    )

    # Secondary Clear action
    col_cl1, col_cl2 = st.columns([4, 1])
    with col_cl2:
        if st.button("🗑️ Clear", key="clear_posting_btn", use_container_width=True):
            st.session_state["show_clear_confirm"] = True
            st.rerun()

    if st.session_state.get("show_clear_confirm", False):
        confirm_clear_dialog()

    # 6. ML Prediction Pipeline
    if check_clicked:
        if cleaned_input == "":
            st.warning("Please enter or extract a job posting before checking.")
        elif len(cleaned_input) < 30:
            st.warning("Please enter a more complete job posting for a meaningful analysis.")
        else:
            with st.status("🔄 Analyzing posting...", expanded=True) as status:
                st.write("📖 Reading job posting...")
                time.sleep(0.15)

                st.write("🔍 Extracting text features...")
                result = predict_job_posting(
                    job_text,
                    telecommuting=int(is_remote),
                    has_company_logo=int(has_logo),
                    has_questions=int(has_questions),
                    has_salary_range=int(has_salary)
                )
                fraud_reasons, genuine_reasons = get_flagged_reasons(job_text)
                structured_contributions = get_structured_feature_contributions(
                    telecommuting=int(is_remote),
                    has_company_logo=int(has_logo),
                    has_questions=int(has_questions),
                    has_salary_range=int(has_salary)
                )
                time.sleep(0.15)

                st.write("🧠 Evaluating risk patterns...")
                summary_sentence = generate_plain_language_summary(
                    result['label'],
                    fraud_reasons,
                    genuine_reasons,
                    structured_contributions
                )
                time.sleep(0.15)

                st.write("✅ Preparing results...")
                time.sleep(0.15)
                status.update(label="Analysis complete!", state="complete", expanded=False)

            # Determine primary confidence score to record
            if result['label'] == "LIKELY FRAUDULENT":
                primary_conf = result['fraud_confidence']
            elif result['label'] == "LIKELY GENUINE":
                primary_conf = result['genuine_confidence']
            else:
                primary_conf = max(result['fraud_confidence'], result['genuine_confidence'])

            # Record in session history (exactly once per analysis click)
            add_recent_check(job_text, result['label'], primary_conf)

            st.session_state["has_analysis"] = True
            st.session_state["analysis_result"] = result
            st.session_state["fraud_reasons"] = fraud_reasons
            st.session_state["genuine_reasons"] = genuine_reasons
            st.session_state["structured_contributions"] = structured_contributions
            st.session_state["summary_sentence"] = summary_sentence
            st.session_state["analyzed_job_text"] = job_text
            st.session_state["analyzed_has_salary"] = has_salary
            st.session_state["analyzed_has_logo"] = has_logo
            st.session_state["analyzed_is_remote"] = is_remote
            st.session_state["analyzed_has_questions"] = has_questions
            st.session_state["feedback_given"] = None

    # 7. Render Analysis Results
    if st.session_state.get("has_analysis", False):
        result = st.session_state["analysis_result"]
        fraud_reasons = st.session_state["fraud_reasons"]
        genuine_reasons = st.session_state["genuine_reasons"]
        structured_contributions = st.session_state["structured_contributions"]
        summary_sentence = st.session_state["summary_sentence"]
        analyzed_text = st.session_state["analyzed_job_text"]
        analyzed_salary = st.session_state["analyzed_has_salary"]
        analyzed_logo = st.session_state["analyzed_has_logo"]
        analyzed_remote = st.session_state["analyzed_is_remote"]
        analyzed_questions = st.session_state["analyzed_has_questions"]

        st.markdown("---")
        st.markdown(f"### Result: :{result['color']}[{result['label']}]")
        st.write(f"**Risk Level:** {result['risk_level']}")

        st.progress(result['fraud_confidence'] / 100)
        st.write(f"Fraud likelihood: **{result['fraud_confidence']}%**  |  Genuine likelihood: **{result['genuine_confidence']}%**")

        st.markdown("---")

        # 1. In-text highlighting
        st.markdown("**Your posting with flagged terms highlighted:**")
        highlighted_html = highlight_flagged_text(
            analyzed_text,
            fraud_reasons,
            genuine_reasons,
            theme_name=st.session_state.get("theme", "dark")
        )
        st.markdown(highlighted_html, unsafe_allow_html=True)

        # 2. Plain-language safety checklist
        st.markdown("**Quick Safety Checklist:**")
        st.write("✅ Salary range mentioned" if analyzed_salary else "❌ No salary range mentioned")
        st.write("✅ Company logo/profile present" if analyzed_logo else "❌ No company logo/profile")
        st.write("✅ Screening questions included" if analyzed_questions else "❌ No screening questions")
        if analyzed_remote:
            st.write("ℹ️ Remote / Work from home position")
        else:
            st.write("ℹ️ On-site / Non-remote position")

        st.markdown("---")

        # 3. Expandable detailed analysis
        with st.expander("🔍 See detailed word analysis"):
            st.markdown(f"💡 **Summary:** {summary_sentence}")

            if structured_contributions:
                st.markdown("**📋 Checked Options Contribution:**")
                for contrib in structured_contributions:
                    direction_color = "red" if contrib["direction"] == "fraud" else "green"
                    direction_label = "Fraud Risk ⚠️" if contrib["direction"] == "fraud" else "Legitimacy Signal ✅"
                    st.write(f"- **{contrib['display_name']}**: Pushed prediction toward **:{direction_color}[{contrib['direction']}]** ({direction_label})")

            if result['label'] != "LIKELY GENUINE" and fraud_reasons:
                st.markdown("**⚠️ Words that raised suspicion:**")
                fraud_formatted = [f"{w} ({s})" for w, s, c in fraud_reasons]
                st.write(", ".join(fraud_formatted))

            if genuine_reasons:
                st.markdown("**✅ Words that suggested legitimacy:**")
                genuine_formatted = [f"{w} ({s})" for w, s, c in genuine_reasons]
                st.write(", ".join(genuine_formatted))

        if result['risk_level'] == "High Risk":
            st.error("⚠️ This posting shows strong signs of being fraudulent. Avoid sharing personal or financial information.")
        elif result['risk_level'] == "Medium Risk":
            st.warning("⚠️ This posting has mixed signals. Proceed with caution and verify the company independently.")
        else:
            st.success("✅ This posting appears genuine based on our analysis.")

        # Feedback Section
        st.markdown("---")
        st.markdown("**Was this helpful?**")
        fb_col1, fb_col2, _ = st.columns([1, 1, 4])
        with fb_col1:
            if st.button("👍 Yes", key="feedback_yes_btn"):
                st.session_state["feedback_given"] = "yes"
        with fb_col2:
            if st.button("👎 No", key="feedback_no_btn"):
                st.session_state["feedback_given"] = "no"

        if st.session_state.get("feedback_given"):
            st.success("Thanks for your feedback!")

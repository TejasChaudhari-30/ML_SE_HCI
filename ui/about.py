import streamlit as st

def render_about():
    """Renders the About tab interface for JobShield."""
    st.header("🛡️ JobShield")
    st.subheader("Hybrid ML Job Posting Fraud Detector")

    st.write(
        "JobShield analyzes job-posting text and predicts whether a posting is likely "
        "genuine or fraudulent using a hybrid machine-learning model."
    )

    st.markdown("---")

    # 1. How It Works
    st.markdown("### ⚙️ How It Works")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            "1. **User enters a job posting:** Paste job text and select structural options.\n"
            "2. **Feature extraction:** Text is converted into numerical TF-IDF features.\n"
            "3. **Model analysis:** SVM and Logistic Regression analyze the posting.\n"
            "4. **Ensemble voting:** Predictions are combined using a Voting Classifier.\n"
            "5. **Results displayed:** JobShield shows predicted result, confidence score, and supporting indicators."
        )
    with col2:
        st.info(
            "💡 **Hybrid ML Approach:** Combines text classification (TF-IDF) with "
            "structured metadata signals (salary, logo, remote status, screening questions) "
            "to evaluate job postings."
        )

    st.markdown("---")

    # 2. Machine Learning Model
    st.markdown("### 🧠 Machine Learning Model")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("**TF-IDF Vectorizer**")
        st.write("Converts raw job-posting text into numerical features based on word frequencies and importance.")

        st.markdown("**Support Vector Machine (SVM)**")
        st.write("Identifies complex patterns separating genuine job descriptions from fraudulent postings.")
    with m_col2:
        st.markdown("**Logistic Regression**")
        st.write("Provides probabilistic classification perspectives and interpretable feature coefficients for word analysis.")

        st.markdown("**Voting Classifier**")
        st.write("Combines the predictions of SVM and Logistic Regression into a final ensemble assessment.")

    st.markdown("---")

    # 3. Key Features
    st.markdown("### ✨ Key Features")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.markdown("- **Fraud/Genuine Prediction:** Instant risk rating and confidence breakdown.")
        st.markdown("- **Confidence Score:** Percentage breakdown for fraud vs. genuine likelihood.")
        st.markdown("- **Risk Indication:** High, Medium, or Low risk level badge.")
        st.markdown("- **Important-Word Analysis:** Flagged terms highlighted in-text and detailed word breakdown.")
        st.markdown("- **Safety Checklist:** Plain-language verification of salary, logo, remote, and question signals.")
    with f_col2:
        st.markdown("- **Sample Job Postings:** One-click loading of Genuine, Common Scam, and Borderline examples.")
        st.markdown("- **User Feedback:** 👍 / 👎 interactive feedback mechanism.")
        st.markdown("- **Recent Checks History:** Session-based table tracking recent analyses with clean timestamps.")
        st.markdown("- **Session-based Storage:** In-memory tracking without requiring a external database.")

    st.markdown("---")

    # 4. Important Safety Note
    st.markdown("### ⚠️ Important Safety Note")
    st.warning(
        "JobShield is an academic/project-based tool and should be used as a screening aid, "
        "not as the sole basis for deciding whether a job opportunity is legitimate.\n\n"
        "**Encouraged independent verification steps:**\n"
        "- Company identity and official registration\n"
        "- Recruiter identity and communication channels\n"
        "- Official company website and career portal\n"
        "- Detailed job description and requirements\n"
        "- Requests for money, fees, or sensitive financial information"
    )

    st.markdown("---")

    # 5. Project Information
    st.markdown("### 📋 Project Information")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.markdown("**Project:** JobShield")
        st.markdown("**Purpose:** Job Posting Fraud Detection")
    with p_col2:
        st.markdown("**Approach:** Hybrid Machine Learning")
        st.markdown("**Interface:** Streamlit")


import streamlit as st
import joblib
import re
import numpy as np
from nltk.corpus import stopwords
from scipy.sparse import hstack

# Load saved model and vectorizer
model = joblib.load('hybrid_model.pkl')
tfidf = joblib.load('tfidf_vectorizer.pkl')
print(f"Vocabulary size: {len(tfidf.get_feature_names_out())}")

stop_words = set(stopwords.words('english'))

def clean_text_single(text):
    text = text.lower()
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'http\S+|www\S+', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    words = [w for w in words if w not in stop_words and len(w) > 2]
    return ' '.join(words)

def predict_job_posting(raw_text, telecommuting, has_company_logo, has_questions, has_salary_range):
    cleaned = clean_text_single(raw_text)
    text_vector = tfidf.transform([cleaned])
    structured = np.array([[telecommuting, has_company_logo, has_questions, has_salary_range]])
    final_vector = hstack([text_vector, structured])

    probability = model.predict_proba(final_vector)[0]
    fraud_prob = probability[1] * 100
    genuine_prob = probability[0] * 100

    if fraud_prob >= 70:
        label = "LIKELY FRAUDULENT"
        risk_level = "High Risk"
        color = "red"
    elif fraud_prob >= 45:
        label = "UNCERTAIN — REVIEW RECOMMENDED"
        risk_level = "Medium Risk"
        color = "orange"
    else:
        label = "LIKELY GENUINE"
        risk_level = "Low Risk"
        color = "green"

    return {
        'label': label,
        'risk_level': risk_level,
        'fraud_confidence': round(fraud_prob, 2),
        'genuine_confidence': round(genuine_prob, 2),
        'color': color
    }

def get_strength_label(weight):
    abs_val = abs(weight)
    if abs_val > 1.5:
        return "Strong"
    elif abs_val > 0.7:
        return "Moderate"
    else:
        return "Weak"

def get_flagged_reasons(raw_text, top_n=5):
    """
    Identifies which words in the user's input most contributed
    to the fraud/genuine prediction, using LR's learned coefficients.
    Returns lists of tuples: (word, strength, weight)
    """
    cleaned = clean_text_single(raw_text)
    words_in_text = set(cleaned.split())

    feature_names = list(tfidf.get_feature_names_out())
    word_to_idx = {word: idx for idx, word in enumerate(feature_names)}

    lr_component = model.named_estimators_['lr']
    coefficients = lr_component.coef_[0][:len(feature_names)]

    word_weights = {}
    for word in words_in_text:
        if word in word_to_idx:
            idx = word_to_idx[word]
            word_weights[word] = coefficients[idx]

    sorted_words = sorted(word_weights.items(), key=lambda x: x[1], reverse=True)

    fraud_reasons = [(w, get_strength_label(weight), weight) for w, weight in sorted_words if weight > 0][:top_n]

    genuine_sorted = sorted([(w, weight) for w, weight in word_weights.items() if weight < 0], key=lambda x: x[1])
    genuine_reasons = [(w, get_strength_label(weight), weight) for w, weight in genuine_sorted][:top_n]

    return fraud_reasons, genuine_reasons

def get_structured_feature_contributions(telecommuting, has_company_logo, has_questions, has_salary_range):
    """
    Extracts LR coefficients for the 4 structured features and determines
    the contribution direction for features checked/True by the user.
    """
    lr_component = model.named_estimators_['lr']
    struct_coefs = lr_component.coef_[0][-4:]

    features = [
        ("Remote / Work from home option", "the remote work option", telecommuting, struct_coefs[0]),
        ("Company logo/profile present", "the company logo/profile", has_company_logo, struct_coefs[1]),
        ("Screening questions included", "screening questions", has_questions, struct_coefs[2]),
        ("Salary range mentioned", "the salary range", has_salary_range, struct_coefs[3]),
    ]

    contributions = []
    for display_name, summary_name, is_checked, coef in features:
        if is_checked:
            direction = "fraud" if coef > 0 else "genuine"
            contributions.append({
                "display_name": display_name,
                "summary_name": summary_name,
                "direction": direction,
                "coef": coef,
                "strength": get_strength_label(coef)
            })
    return contributions

def generate_plain_language_summary(result_label, fraud_reasons, genuine_reasons, structured_contributions):
    # Determine top words (2 to 3) based on prediction
    if result_label in ["LIKELY FRAUDULENT", "UNCERTAIN — REVIEW RECOMMENDED"]:
        top_words = [w for w, s, c in fraud_reasons[:3]]
        if not top_words and genuine_reasons:
            top_words = [w for w, s, c in genuine_reasons[:3]]
    else:
        top_words = [w for w, s, c in genuine_reasons[:3]]
        if not top_words and fraud_reasons:
            top_words = [w for w, s, c in fraud_reasons[:3]]

    # Format words string
    if len(top_words) == 1:
        words_str = f"'{top_words[0]}'"
    elif len(top_words) == 2:
        words_str = f"'{top_words[0]}' and '{top_words[1]}'"
    elif len(top_words) >= 3:
        words_str = f"'{top_words[0]}', '{top_words[1]}', and '{top_words[2]}'"
    else:
        words_str = ""

    # Group structured feature contributions
    fraud_structs = [c["summary_name"] for c in structured_contributions if c["direction"] == "fraud"]
    genuine_structs = [c["summary_name"] for c in structured_contributions if c["direction"] == "genuine"]

    def join_items(items):
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, and {items[-1]}"

    fraud_struct_str = join_items(fraud_structs) if fraud_structs else ""
    genuine_struct_str = join_items(genuine_structs) if genuine_structs else ""

    # Build single sentence summary
    if result_label in ["LIKELY FRAUDULENT", "UNCERTAIN — REVIEW RECOMMENDED"]:
        if words_str and (fraud_struct_str or genuine_struct_str):
            if fraud_struct_str and genuine_struct_str:
                sentence = (f"This job posting was flagged as suspicious primarily due to keywords like {words_str}, "
                            f"with {fraud_struct_str} adding to the risk while {genuine_struct_str} provided a positive signal.")
            elif fraud_struct_str:
                sentence = (f"This job posting was flagged as suspicious primarily due to keywords like {words_str}, "
                            f"along with {fraud_struct_str} which also contributed to the risk.")
            else:
                sentence = (f"This job posting was flagged as suspicious primarily due to keywords like {words_str}, "
                            f"though {genuine_struct_str} provided a positive signal.")
        elif words_str:
            sentence = f"This job posting was flagged as suspicious primarily due to keywords like {words_str}."
        elif fraud_struct_str or genuine_struct_str:
            if fraud_struct_str:
                sentence = f"This job posting was flagged as suspicious based on job details like {fraud_struct_str}."
            else:
                sentence = f"This job posting was flagged as suspicious based on overall text patterns, despite positive signals from {genuine_struct_str}."
        else:
            sentence = "This job posting was flagged as suspicious based on overall language patterns in the text."
    else:
        # LIKELY GENUINE
        if words_str and (genuine_struct_str or fraud_struct_str):
            if genuine_struct_str and fraud_struct_str:
                sentence = (f"This job posting appears genuine primarily due to reassuring terms like {words_str}, "
                            f"supported by positive signals from {genuine_struct_str}, despite {fraud_struct_str} raising slight risk.")
            elif genuine_struct_str:
                sentence = (f"This job posting appears genuine primarily due to reassuring terms like {words_str}, "
                            f"supported by positive signals from {genuine_struct_str}.")
            else:
                sentence = (f"This job posting appears genuine primarily due to reassuring terms like {words_str}, "
                            f"despite {fraud_struct_str} raising slight risk.")
        elif words_str:
            sentence = f"This job posting appears genuine primarily due to reassuring terms like {words_str}."
        elif genuine_struct_str or fraud_struct_str:
            if genuine_struct_str:
                sentence = f"This job posting appears genuine based on positive signals from job details like {genuine_struct_str}."
            else:
                sentence = f"This job posting appears genuine based on text analysis, despite {fraud_struct_str} raising slight risk."
        else:
            sentence = "This job posting appears genuine based on overall text patterns."

    return sentence


# ---------------- UI Layout ----------------

st.set_page_config(page_title="JobShield", page_icon="🛡️", layout="centered")

st.title("🛡️ JobShield")
st.subheader("Detect Fraudulent Job Postings using Hybrid Machine Learning")
st.write("Paste a job posting below and check whether it looks genuine or fraudulent.")

job_text = st.text_area(
    "Job Posting Text",
    height=200,
    placeholder="Paste the job title, description, requirements, and benefits here..."
)

col1, col2 = st.columns(2)
with col1:
    has_salary = st.checkbox("Salary range mentioned?")
    has_logo = st.checkbox("Company logo/profile present?")
with col2:
    is_remote = st.checkbox("Remote / Work from home?")
    has_questions = st.checkbox("Screening questions included?")

if st.button("🔍 Check Posting", type="primary"):
    if job_text.strip() == "":
        st.warning("Please paste a job posting before checking.")
    else:
        with st.spinner("Analyzing posting..."):
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
            summary_sentence = generate_plain_language_summary(
                result['label'],
                fraud_reasons,
                genuine_reasons,
                structured_contributions
            )

        st.markdown("---")
        st.markdown(f"### Result: :{result['color']}[{result['label']}]")
        st.write(f"**Risk Level:** {result['risk_level']}")

        st.progress(result['fraud_confidence'] / 100)
        st.write(f"Fraud likelihood: **{result['fraud_confidence']}%**  |  Genuine likelihood: **{result['genuine_confidence']}%**")

        st.markdown("---")

        # 3. Plain-language summary
        st.markdown(f"💡 **Summary:** {summary_sentence}")

        # 2. Structured feature contribution
        if structured_contributions:
            st.markdown("**📋 Checked Options Contribution:**")
            for contrib in structured_contributions:
                direction_color = "red" if contrib["direction"] == "fraud" else "green"
                direction_label = "Fraud Risk ⚠️" if contrib["direction"] == "fraud" else "Legitimacy Signal ✅"
                st.write(f"- **{contrib['display_name']}**: Pushed prediction toward **:{direction_color}[{contrib['direction']}]** ({direction_label})")

        # 1. Word strength labels & flagged word list
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

st.markdown("---")
st.caption("JobShield uses a hybrid ML model (SVM + Logistic Regression) trained on the EMSCAD dataset, augmented with current scam pattern examples. This tool is a decision-support aid, not a guarantee — always verify independently.")
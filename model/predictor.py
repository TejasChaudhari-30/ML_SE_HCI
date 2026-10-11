import os
import re
import joblib
import numpy as np
import nltk
from nltk.corpus import stopwords
from scipy.sparse import hstack

# Resolve project base directory reliably
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'hybrid_model.pkl')
TFIDF_PATH = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')

if not os.path.exists(MODEL_PATH) or not os.path.exists(TFIDF_PATH):
    raise FileNotFoundError(
        "Model or TF-IDF vectorizer artifact missing. "
        "Ensure hybrid_model.pkl and tfidf_vectorizer.pkl exist in the project root."
    )

# Load saved model and vectorizer
model = joblib.load(MODEL_PATH)
tfidf = joblib.load(TFIDF_PATH)
print(f"Vocabulary size: {len(tfidf.get_feature_names_out())}")

# Ensure NLTK stopwords resource is available
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords', quiet=True)
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

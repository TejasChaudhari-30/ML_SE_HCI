# JobShield — Hybrid ML Job Posting Fraud Detector

An ML-powered web application that analyzes job-posting text and metadata signals to help detect potentially fraudulent employment listings.

---

## Overview

JobShield addresses the growing issue of employment scams and fake job listings designed to compromise job seekers' personal information, identity, or financial resources. By combining natural language processing (NLP) of job descriptions with key metadata indicators (such as salary transparency, company logo presence, screening questions, and remote work flags), JobShield provides real-time, interpretable fraud risk assessments through a clean Streamlit web interface.

---

## Key Features

- **Screenshot OCR & Dual Input Methods:** Upload screenshots (PNG, JPG, JPEG) to automatically extract text via local in-memory EasyOCR, or paste text directly.
- **Review & Edit Before Analysis:** Provides an editable review area for correcting OCR mistakes or supplementing details before running fraud detection.
- **Hybrid Job Posting Classification:** Classifies job postings into `LIKELY GENUINE`, `UNCERTAIN — REVIEW RECOMMENDED`, or `LIKELY FRAUDULENT`.
- **Confidence Score & Risk Indication:** Displays percentage likelihood for fraud vs. genuine probability along with clear risk badges (`High Risk`, `Medium Risk`, `Low Risk`).
- **In-Text Word Highlighting:** Highlights suspicious terms (muted red) and reassuring terms (muted green) directly within the user's pasted job text.
- **Plain-Language Safety Checklist:** Evaluates structural job posting attributes (salary range, company logo/profile, screening questions, remote status).
- **Detailed Word Analysis & Plain-Language Summary:** Provides expandable feature contribution breakdowns and readable summary sentences based on learned model coefficients.
- **Sample Job Postings:** Offers one-click sample loading for `Genuine Job`, `Common Scam`, and `Borderline Case` listings.
- **Recent Checks History:** Maintains a session-only table recording previous analyses with clean timestamps, snippets, results, and confidence scores (newest checks first).
- **User Feedback Mechanism:** Includes interactive `👍 Yes` / `👎 No` feedback buttons with immediate acknowledgement.
- **About Tab:** Contains structured system documentation detailing system architecture, ML model mechanics, and independent safety recommendations.

---

## How It Works

The processing pipeline operates as follows:

```text
Screenshot Upload (OCR) OR Direct Text Paste
                 ↓
       Text Preprocessing
 (Lowercasing, Regex Cleaning, NLTK Stopword Removal)
                 ↓
      TF-IDF Vectorization
   (Scikit-Learn TF-IDF Vectorizer)
                 ↓
        Feature Stacking
  (Sparse TF-IDF Vector + 4 Binary Metadata Features)
                 ↓
    Voting Classifier Ensemble
  (Soft Voting: SVM + Logistic Regression)
                 ↓
     Prediction & Risk Assessment
  (Fraud Probability Thresholding: >=70% Fraud, 45-69% Uncertain, <45% Genuine)
                 ↓
  In-Text Highlighting & Safety Checklist Output
```

---

## Machine Learning Approach

### TF-IDF Vectorizer
Converts raw, preprocessed job text into a numerical feature matrix based on term frequency and inverse document frequency, capturing key vocabulary signatures across job postings.

### Support Vector Machine (SVM)
Identifies high-dimensional decision boundaries separating genuine job descriptions from fraudulent listings.

### Logistic Regression
Provides probabilistic classification perspectives and interpretable feature coefficients used for word highlighting and feature influence ranking.

### Voting Classifier
Ensembles Support Vector Machine and Logistic Regression using soft probability voting to produce a robust overall prediction score.

---

## Model Explanation

JobShield extracts learned coefficients from the Logistic Regression component inside the Voting Classifier (`model.named_estimators_['lr']`):

- **Positive Coefficients:** Words that push the classification toward **Fraudulent**.
- **Negative Coefficients:** Words that push the classification toward **Genuine**.

Words present in the analyzed input text are categorized by coefficient direction and weight magnitude into strength levels (`Strong` if $|w| > 1.5$, `Moderate` if $|w| > 0.7$, `Weak` otherwise). Flagged words are dynamically styled in HTML:
- **Fraud-flagged terms:** Soft red background (`#5c2b2b`) with light red text (`#ff6b6b`).
- **Genuine-flagged terms:** Muted green background (`#2b5c3a`) with light green text (`#51cf66`).

---

## Application Architecture

```text
JobShield/
│
├── app.py                     # Main Streamlit application entrypoint & tab layout
│
├── model/
│   ├── __init__.py            # Model package initialization
│   ├── predictor.py           # Text cleaning, vectorization, & Voting Classifier inference
│   └── explanation.py         # Coefficient extraction, word highlighting, & summary generation
│
├── ui/
│   ├── __init__.py            # UI package initialization
│   ├── home.py                # Dedicated SaaS homepage
│   ├── check_posting.py       # Check Posting tab (OCR uploader, paste cards, review, results)
│   ├── recent_checks.py       # Recent Checks tab (session history table & clear history)
│   └── about.py               # About tab (system architecture, ML model info, safety disclaimer)
│
├── utils/
│   ├── __init__.py            # Utilities package initialization
│   ├── ocr.py                 # EasyOCR text extraction and reader caching
│   ├── theme.py               # Design tokens (Light/Dark) and styling overrides
│   └── session.py             # Session state initialization & recent check history manager
│
├── hybrid_model.pkl           # Pre-trained Voting Classifier model artifact
├── tfidf_vectorizer.pkl       # Pre-trained TF-IDF vectorizer artifact
├── requirements.txt           # Python dependencies
└── README.md                  # Comprehensive project documentation
```

### Module Responsibilities
- **`app.py`**: Configures Streamlit page settings, initializes session state, and sets up navigation.
- **`model/`**: Houses prediction pipeline (`predictor.py`) and feature explanation engine (`explanation.py`).
- **`ui/`**: Modular UI components (`home.py`, `check_posting.py`, `recent_checks.py`, `about.py`).
- **`utils/`**: Utilities for OCR extraction (`ocr.py`), theme management (`theme.py`), and session state (`session.py`).

---

## Tech Stack

| Technology | Purpose |
| --- | --- |
| **Python** | Application programming language |
| **Streamlit** | Interactive web interface and segmented navigation |
| **EasyOCR** | Local in-memory optical character recognition for screenshots |
| **Pillow (PIL)** | Image loading and preprocessing in memory |
| **Scikit-learn** | ML models (SVM, Logistic Regression, VotingClassifier, TF-IDF Vectorizer) |
| **NLTK** | Stopword removal for text preprocessing |
| **NumPy & SciPy** | Matrix manipulation and sparse feature stacking |
| **Pandas** | Tabular formatting for session check history |
| **Joblib** | Model and vectorizer artifact loading |

---

## Dataset and Artifacts

- **Model Artifacts:** The application uses pre-trained serialized artifacts: `hybrid_model.pkl` (Voting Classifier) and `tfidf_vectorizer.pkl` (TF-IDF Vectorizer).
- **Training Data:** Trained on the **EMSCAD** (Employment Scam Dataset), augmented with manually constructed scam pattern examples representing recent employment fraud patterns.
- **Target Classes:** Binary classification (`0`: Genuine, `1`: Fraudulent).

---

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd JobShield

# (Optional) Create and activate a virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Launch the Streamlit web application
streamlit run app.py
```

---

## Usage

1. Launch the application using `streamlit run app.py`.
2. Open the **Check Posting** tab.
3. Paste job posting text or click one of the sample buttons (`📄 Sample: Genuine Job`, `⚠️ Sample: Common Scam`, `🤔 Sample: Borderline Case`).
4. Check relevant job indicator boxes (salary, company logo, remote status, screening questions).
5. Click **🔍 Check Posting**.
6. Review prediction label, risk badge, and confidence percentage.
7. Inspect in-text highlighted terms, safety checklist, and detailed word analysis.
8. Submit feedback using `👍 Yes` or `👎 No`.
9. Switch to **Recent Checks** to view session history or clear records.
10. Switch to **About** for system details and safety recommendations.

---

## Screenshots

### Check Posting Tab
<!-- Add screenshot of Check Posting tab here -->

### Analysis Results & Highlighting
<!-- Add screenshot of analysis results and highlighted text here -->

### Recent Checks Tab
<!-- Add screenshot of Recent Checks history table here -->

### About Tab
<!-- Add screenshot of About page here -->

---

## Limitations

- **Session-Only History:** Recent checks are stored in memory (`st.session_state`) and disappear when the Streamlit session ends.
- **English Postings:** Stopwords and TF-IDF features are optimized for English text postings.
- **Static Artifacts:** Model inference uses pre-trained static model files without live online learning.
- **Screening Aid:** Designed as a decision-support tool; does not provide legal or absolute guarantees.

---

## Future Improvements

- **Persistent Database:** Support persistent database storage for user check histories.
- **User Authentication:** User accounts and personal history dashboard.
- **Deep Learning NLP:** Integration of Transformer architectures (e.g., BERT/DeBERTa) for contextual embeddings.
- **OCR & Document Upload:** Direct analysis of PDF/image job offer letters.
- **Browser Extension:** Real-time job listing scanning on web job portals.

---

## Safety Disclaimer

> **Safety Disclaimer:** JobShield is an academic/project-based screening tool. Its predictions should not be treated as definitive proof that a job posting is legitimate or fraudulent. Users should independently verify the employer, recruiter identity, official company website, and any requests for money or sensitive personal information.

---

## Project Status

**Status: Academic Project / MVP**

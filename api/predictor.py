"""
JobShield API Predictor Service
Wraps and reuses the trained hybrid VotingClassifier and TF-IDF vectorizer
for FastAPI inference.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple

# Ensure project root is available in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger("jobshield.api.predictor")

MODEL_PATH = os.path.join(PROJECT_ROOT, "hybrid_model.pkl")
TFIDF_PATH = os.path.join(PROJECT_ROOT, "tfidf_vectorizer.pkl")


class JobShieldPredictor:
    """Singleton-style wrapper for JobShield model inference and explanations."""

    def __init__(self):
        self.model = None
        self.tfidf = None
        self._is_ready = False
        self._load_error = None

    def load_artifacts(self) -> None:
        """Loads model and vectorizer artifacts once at API startup."""
        try:
            if not os.path.exists(MODEL_PATH):
                raise FileNotFoundError(f"Model artifact not found at: {MODEL_PATH}")
            if not os.path.exists(TFIDF_PATH):
                raise FileNotFoundError(f"TF-IDF vectorizer artifact not found at: {TFIDF_PATH}")

            # Import existing model logic
            from model.predictor import model as existing_model, tfidf as existing_tfidf

            self.model = existing_model
            self.tfidf = existing_tfidf
            self._is_ready = True
            self._load_error = None
            logger.info("Successfully loaded JobShield model and vectorizer artifacts.")
        except Exception as exc:
            self._is_ready = False
            self._load_error = str(exc)
            logger.error("Failed to load JobShield model artifacts: %s", exc, exc_info=True)
            raise

    @property
    def is_ready(self) -> bool:
        return self._is_ready and self.model is not None and self.tfidf is not None

    def get_info(self) -> Dict[str, Any]:
        return {
            "model_type": "VotingClassifier (Logistic Regression + LinearSVC)",
            "vectorizer_vocab_size": len(self.tfidf.get_feature_names_out()) if self.tfidf else 0,
            "status": "ready" if self.is_ready else "not_ready",
            "error": self._load_error
        }

    def predict(
        self,
        raw_text: str,
        telecommuting: int = 0,
        has_company_logo: int = 0,
        has_questions: int = 0,
        has_salary_range: int = 0
    ) -> Dict[str, Any]:
        """
        Executes prediction using the existing hybrid model and explanation pipeline.
        Returns native Python types safe for JSON serialization.
        """
        if not self.is_ready:
            raise RuntimeError(f"Predictor service is not ready. Load error: {self._load_error}")

        from model.predictor import predict_job_posting
        from model.explanation import (
            get_flagged_reasons,
            get_structured_feature_contributions,
            generate_plain_language_summary
        )

        # 1. Run core hybrid prediction
        pred_result = predict_job_posting(
            raw_text=raw_text,
            telecommuting=int(telecommuting),
            has_company_logo=int(has_company_logo),
            has_questions=int(has_questions),
            has_salary_range=int(has_salary_range)
        )

        label = pred_result["label"]
        risk_level = pred_result["risk_level"]
        fraud_conf = float(pred_result["fraud_confidence"])
        genuine_conf = float(pred_result["genuine_confidence"])
        color = pred_result["color"]

        # Primary confidence score matching Streamlit semantics
        if label == "LIKELY FRAUDULENT":
            primary_conf = fraud_conf
        elif label == "LIKELY GENUINE":
            primary_conf = genuine_conf
        else:
            primary_conf = fraud_conf

        # 2. Extract explanation and top contributing words
        fraud_reasons, genuine_reasons = get_flagged_reasons(raw_text)
        structured_contributions = get_structured_feature_contributions(
            telecommuting=int(telecommuting),
            has_company_logo=int(has_company_logo),
            has_questions=int(has_questions),
            has_salary_range=int(has_salary_range)
        )

        summary_sentence = generate_plain_language_summary(
            label,
            fraud_reasons,
            genuine_reasons,
            structured_contributions
        )

        # Format indicator lists with native types
        warning_indicators = [
            {"word": w, "strength": str(s), "weight": round(float(wt), 4)}
            for w, s, wt in fraud_reasons
        ]
        reassuring_indicators = [
            {"word": w, "strength": str(s), "weight": round(float(wt), 4)}
            for w, s, wt in genuine_reasons
        ]

        char_count = len(raw_text)
        word_count = len(raw_text.split())

        return {
            "label": label,
            "risk_level": risk_level,
            "confidence": round(primary_conf, 2),
            "fraud_confidence": round(fraud_conf, 2),
            "genuine_confidence": round(genuine_conf, 2),
            "color": color,
            "explanation": summary_sentence,
            "warning_indicators": warning_indicators,
            "reassuring_indicators": reassuring_indicators,
            "character_count": char_count,
            "word_count": word_count
        }


# Global service instance
predictor_service = JobShieldPredictor()

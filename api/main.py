"""
JobShield FastAPI Backend Service
Exposes the trained JobShield hybrid ML fraud detection pipeline via HTTP.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

# Ensure project root is available in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from api.predictor import predictor_service

# Logging setup: do not log raw job descriptions
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jobshield.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: loads model artifacts once at startup."""
    logger.info("Initializing JobShield prediction service on startup...")
    try:
        predictor_service.load_artifacts()
        logger.info("JobShield model and vectorizer ready for inference.")
    except Exception as exc:
        logger.error("Failed to initialize model artifacts during startup: %s", exc)
    yield
    logger.info("Shutting down JobShield prediction service.")


app = FastAPI(
    title="JobShield Fraud Detection API",
    description=(
        "Production-ready FastAPI service providing real-time job-posting fraud "
        "screening powered by a hybrid ensemble (LinearSVC + Logistic Regression)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Explicit CORS configuration: local development environments, deployed domains & Chrome Extension
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:8501",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8501"
]

# Allow additional origins via environment variable (comma-separated)
extra_origins = os.environ.get("CORS_ORIGINS", "")
if extra_origins:
    for origin in extra_origins.split(","):
        stripped = origin.strip()
        if stripped and stripped not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(stripped)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Schemas ---

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_type: str
    version: str


class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        description="Full text of the job posting to analyze (title, description, qualifications)."
    )
    telecommuting: Optional[int] = Field(
        default=0,
        ge=0,
        le=1,
        description="Optional structural flag: 1 if remote/telecommuting work is offered, else 0."
    )
    has_company_logo: Optional[int] = Field(
        default=0,
        ge=0,
        le=1,
        description="Optional structural flag: 1 if company logo/profile is present, else 0."
    )
    has_questions: Optional[int] = Field(
        default=0,
        ge=0,
        le=1,
        description="Optional structural flag: 1 if screening questions are present, else 0."
    )
    has_salary_range: Optional[int] = Field(
        default=0,
        ge=0,
        le=1,
        description="Optional structural flag: 1 if salary range is explicitly stated, else 0."
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Job posting text must be a valid string.")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Job posting text cannot be empty or whitespace only.")
        if len(stripped) < 30:
            raise ValueError(
                f"Job posting text is too short ({len(stripped)} chars). "
                "Minimum 30 characters required for a reliable analysis."
            )
        if len(v) > 50000:
            raise ValueError(
                f"Job posting text exceeds maximum allowed length of 50,000 characters (length: {len(v)})."
            )
        return v


class IndicatorItem(BaseModel):
    word: str
    strength: str
    weight: float


class PredictResponse(BaseModel):
    label: str
    risk_level: str
    confidence: float
    fraud_confidence: float
    genuine_confidence: float
    color: str
    explanation: str
    warning_indicators: List[IndicatorItem]
    reassuring_indicators: List[IndicatorItem]
    character_count: int
    word_count: int


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Confirms API status and readiness of the underlying ML model."""
    is_ready = predictor_service.is_ready
    info = predictor_service.get_info()

    if not is_ready:
        return HealthResponse(
            status="degraded",
            model_loaded=False,
            model_type=info["model_type"],
            version="1.0.0"
        )

    return HealthResponse(
        status="healthy",
        model_loaded=True,
        model_type=info["model_type"],
        version="1.0.0"
    )


@app.post("/predict", response_model=PredictResponse)
def predict_posting(req: PredictRequest):
    """
    Analyzes a job posting using JobShield's hybrid VotingClassifier model.
    Returns prediction label, risk assessment, confidence score, and explanatory indicators.
    """
    if not predictor_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready or failed to load. Please verify server logs."
        )

    # Log only length metadata, preserving privacy
    char_count = len(req.text)
    word_count = len(req.text.split())
    logger.info("Processing prediction request (%d chars, %d words).", char_count, word_count)

    try:
        result = predictor_service.predict(
            raw_text=req.text,
            telecommuting=req.telecommuting or 0,
            has_company_logo=req.has_company_logo or 0,
            has_questions=req.has_questions or 0,
            has_salary_range=req.has_salary_range or 0
        )
    except Exception as exc:
        logger.error("Prediction pipeline failure: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while running prediction on the provided job posting."
        )

    logger.info(
        "Prediction finished: label='%s', risk='%s', conf=%.2f%%",
        result["label"],
        result["risk_level"],
        result["confidence"]
    )

    return PredictResponse(**result)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("api.main:app", host=host, port=port, reload=False)

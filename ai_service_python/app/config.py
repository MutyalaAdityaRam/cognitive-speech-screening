from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
ARTIFACT_DIR = BASE_DIR / "artifacts" / "colab_artifacts"
SOURCE_DATA_DIR = PROJECT_DIR / "prompts"
REPORT_DIR = PROJECT_DIR / "reports"
REQUIRED_ORIGINAL_ARTIFACTS = [
    "model_1_pipeline.pkl",
    "model_2_ensemble.pkl",
    "tfidf_vectorizer.pkl",
    "scaler.pkl",
    "imputer.pkl",
    "label_encoder.pkl",
    "feature_names.json",
    "selected_features.json",
]

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "openai/gpt-oss-120b"

SAFETY_NOTE = (
    "This system is an AI-assisted cognitive screening tool and not a medical diagnosis. Please consult a qualified healthcare professional."
)

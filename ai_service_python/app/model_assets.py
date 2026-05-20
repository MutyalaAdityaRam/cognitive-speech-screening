from functools import lru_cache
from typing import Any
import numpy as np
import warnings

# Suppress non-critical warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Set deterministic seeds for model loading
np.random.seed(42)

from .colab_runtime import (
    load_feature_names,
    load_imputer_artifact,
    load_label_encoder_artifact,
    load_model_1,
    load_model_2,
    load_scaler_artifact,
    load_selected_features,
    load_tfidf_vectorizer,
)


@lru_cache(maxsize=1)
def load_feature_columns() -> list[str]:
    return load_feature_names()


@lru_cache(maxsize=1)
def load_selected_feature_columns() -> list[str]:
    return load_selected_features()


@lru_cache(maxsize=1)
def load_models() -> tuple[Any, Any]:
    return (load_model_1(), load_model_2())


@lru_cache(maxsize=1)
def load_label_encoder() -> Any:
    return load_label_encoder_artifact()


@lru_cache(maxsize=1)
def load_imputer() -> Any:
    return load_imputer_artifact()


@lru_cache(maxsize=1)
def load_scaler() -> Any:
    return load_scaler_artifact()


@lru_cache(maxsize=1)
def load_tfidf() -> Any:
    return load_tfidf_vectorizer()

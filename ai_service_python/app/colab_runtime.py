from __future__ import annotations

import json
from functools import lru_cache
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import joblib

from .config import ARTIFACT_DIR


def artifact_path(name: str) -> Path:
    return ARTIFACT_DIR / name


@lru_cache(maxsize=None)
def _load_artifact_module(filename: str) -> ModuleType:
    module_path = artifact_path(filename)
    spec = util.spec_from_file_location(f"colab_artifacts.{module_path.stem}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load artifact module from {module_path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_json_artifact(name: str) -> list[str]:
    with artifact_path(name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_tfidf_vectorizer() -> Any:
    return joblib.load(artifact_path("tfidf_vectorizer.pkl"))


@lru_cache(maxsize=1)
def load_model_1() -> Any:
    return joblib.load(artifact_path("model_1_pipeline.pkl"))


@lru_cache(maxsize=1)
def load_model_2() -> Any:
    return joblib.load(artifact_path("model_2_ensemble.pkl"))


@lru_cache(maxsize=1)
def load_label_encoder_artifact() -> Any:
    return joblib.load(artifact_path("label_encoder.pkl"))


@lru_cache(maxsize=1)
def load_imputer_artifact() -> Any:
    return joblib.load(artifact_path("imputer.pkl"))


@lru_cache(maxsize=1)
def load_scaler_artifact() -> Any:
    return joblib.load(artifact_path("scaler.pkl"))


@lru_cache(maxsize=1)
def load_feature_names() -> list[str]:
    return load_json_artifact("feature_names.json")


@lru_cache(maxsize=1)
def load_selected_features() -> list[str]:
    return load_json_artifact("selected_features.json")


@lru_cache(maxsize=1)
def load_audio_preprocessor() -> Any:
    return getattr(_load_artifact_module("audio_preprocessing.py"), "preprocess_audio")


@lru_cache(maxsize=1)
def load_clean_text() -> Any:
    return getattr(_load_artifact_module("feature_extraction.py"), "clean_text")


@lru_cache(maxsize=1)
def load_extract_features() -> Any:
    return getattr(_load_artifact_module("feature_extraction.py"), "extract_features")


@lru_cache(maxsize=1)
def load_apply_feature_selection() -> Any:
    return getattr(_load_artifact_module("feature_selection.py"), "apply_feature_selection")


@lru_cache(maxsize=1)
def load_preprocess_features() -> Any:
    return getattr(_load_artifact_module("preprocessing.py"), "preprocess_features")
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

# Set deterministic seeds for reproducibility
np.random.seed(42)

from ..asr import FasterWhisperTranscriber
from ..colab_runtime import (
    load_apply_feature_selection,
    load_audio_preprocessor,
    load_clean_text,
    load_extract_features,
    load_feature_names,
    load_imputer_artifact,
    load_preprocess_features,
    load_scaler_artifact,
    load_selected_features,
    load_tfidf_vectorizer,
)


class DataAgent:
    def run_from_csv(self, csv_path: str | Path) -> dict[str, object]:
        frame = pd.read_csv(csv_path)
        features = self._prepare_features(frame)
        return {"features": features, "source": "csv", "valid": True}

    def transcribe_from_audio(self, audio_path: str | Path) -> dict[str, object]:
        audio_path = Path(audio_path)
        processed_path = audio_path.with_name(f"{audio_path.stem}_processed.wav")

        preprocess = load_audio_preprocessor()
        result = preprocess(audio_path, processed_path)
        if not result.get("status"):
            return {"status": "needs_restart", "valid": False, "message": result.get("message", "No voice detected. Please restart reading.")}

        transcriber = FasterWhisperTranscriber()
        transcription = transcriber.transcribe(processed_path)
        transcript = (transcription.text or "").strip()
        if not transcript:
            return {"status": "needs_restart", "valid": False, "message": "No voice detected. Please restart reading."}

        clean_text = load_clean_text()
        cleaned_transcript = clean_text(transcript)
        return {
            "valid": True,
            "transcript": transcript,
            "transcript_clean": cleaned_transcript,
            "audio_file_path": str(audio_path),
            "processed_audio_path": str(processed_path),
            "preprocessing": result,
        }

    def run_from_audio(self, audio_path: str | Path) -> dict[str, object]:
        audio_path = Path(audio_path)
        processed_path = audio_path.with_name(f"{audio_path.stem}_processed.wav")

        preprocess = load_audio_preprocessor()
        result = preprocess(audio_path, processed_path)
        if not result.get("status"):
            return {"status": "needs_restart", "valid": False, "message": result.get("message", "No voice detected. Please restart reading.")}

        transcriber = FasterWhisperTranscriber()
        transcription = transcriber.transcribe(processed_path)
        transcript = (transcription.text or "").strip()
        if not transcript:
            return {"status": "needs_restart", "valid": False, "message": "No voice detected. Please restart reading."}

        clean_text = load_clean_text()
        cleaned_transcript = clean_text(transcript)

        extract_features = load_extract_features()
        tfidf_vectorizer = load_tfidf_vectorizer()
        raw_features = extract_features(processed_path, cleaned_transcript, tfidf_vectorizer)
        features = self._prepare_features(raw_features)

        return {
            "features": features,
            "raw_features": raw_features,
            "source": "audio",
            "valid": True,
            "preprocessing": result,
            "transcript": transcript,
            "transcript_clean": cleaned_transcript,
            "audio_file_path": str(audio_path),
            "processed_audio_path": str(processed_path),
            "duration_seconds": result.get("duration_seconds"),
            "rms": result.get("rms"),
        }

    def _prepare_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        feature_names = load_feature_names()
        selected_features = load_selected_features()
        preprocess_features = load_preprocess_features()

        aligned = frame.copy()
        for column in feature_names:
            if column not in aligned.columns:
                aligned[column] = 0
        aligned = aligned[feature_names]

        processed = preprocess_features(aligned, load_scaler_artifact(), load_imputer_artifact(), feature_names)

        apply_selection = load_apply_feature_selection()
        selected = apply_selection(processed, selected_features)
        return pd.DataFrame(selected, columns=selected_features)

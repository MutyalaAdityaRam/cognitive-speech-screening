import os
import numpy as np
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

# Set random seed for deterministic ASR behavior
np.random.seed(42)
os.environ['PYTHONHASHSEED'] = '42'


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None = None
    duration_seconds: float | None = None

    @property
    def has_transcript(self) -> bool:
        return bool(self.text.strip())


class FasterWhisperTranscriber:
    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        self.model_size = model_size or os.getenv("WHISPER_MODEL_SIZE", "tiny")
        self.device = device or os.getenv("WHISPER_DEVICE", "cpu")
        self.compute_type = compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    @property
    def model(self) -> WhisperModel:
        return _load_model(self.model_size, self.device, self.compute_type)

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        # Use deterministic parameters for consistent transcription
        segments, info = self.model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},  # Consistent silence detection
            temperature=0.0,  # Deterministic decoding (greedy, no sampling)
            language="en",  # Lock language for consistency
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", None),
            duration_seconds=getattr(info, "duration", None),
        )


@lru_cache(maxsize=2)
def _load_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    return WhisperModel(model_size, device=device, compute_type=compute_type)


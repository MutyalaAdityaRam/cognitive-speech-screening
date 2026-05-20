from __future__ import annotations

from pathlib import Path
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.orchestrator import OrchestratorAgent


def main() -> None:
    sample = Path(__file__).resolve().parents[2] / "test_audio_files" / "tone_voice.wav"
    try:
        print("starting")
        result = OrchestratorAgent().run_from_audio(sample)
        print("prediction:", result.get("prediction"))
        print("confidence:", result.get("confidence"))
        print("prob1:", result.get("prob1"))
        print("prob2:", result.get("prob2"))
        print("transcript:", result.get("transcript", "")[:200])
        print("report:", result.get("final_report", "")[:400])
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
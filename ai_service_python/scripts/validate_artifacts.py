from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import ARTIFACT_DIR, REQUIRED_ORIGINAL_ARTIFACTS, SOURCE_DATA_DIR


def main() -> int:
    missing: list[str] = []

    if not ARTIFACT_DIR.exists():
        missing.append(f"artifact directory missing: {ARTIFACT_DIR}")

    if not SOURCE_DATA_DIR.exists():
        missing.append(f"source prompts directory missing: {SOURCE_DATA_DIR}")

    for artifact in REQUIRED_ORIGINAL_ARTIFACTS:
        path = ARTIFACT_DIR / artifact
        if not path.exists():
            missing.append(f"missing artifact: {path}")

    optional = [
        ARTIFACT_DIR / "selected_features_model2.json",
    ]
    for path in optional:
        if not path.exists():
            print(f"optional artifact not found: {path}")

    if missing:
        print("artifact validation failed:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("artifact validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
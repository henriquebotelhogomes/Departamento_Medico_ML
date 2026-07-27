"""Ensure the inference model exists at backend/app/ml/artifacts/model.keras.

Copies the fine-tuned model from the repository root. Run from anywhere:

    uv run python scripts/get_model.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CANDIDATES = [
    REPO_ROOT / "modelo_raiox_mendeley_ft.keras",
    REPO_ROOT / "modelo_raiox_mendeley.keras",
    REPO_ROOT / "modelo_raiox.keras",
]
DEST = REPO_ROOT / "backend" / "app" / "ml" / "artifacts" / "model.keras"


def main() -> int:
    if DEST.exists():
        print(f"[skip] Model already present: {DEST}")
        return 0

    source = next((p for p in SOURCE_CANDIDATES if p.exists()), None)
    if source is None:
        print("[error] No source .keras model found in the repository root.")
        print("        Expected one of:")
        for candidate in SOURCE_CANDIDATES:
            print(f"          - {candidate.name}")
        return 1

    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DEST)
    size_mb = DEST.stat().st_size / (1024 * 1024)
    print(f"[ok] Copied {source.name} -> {DEST} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

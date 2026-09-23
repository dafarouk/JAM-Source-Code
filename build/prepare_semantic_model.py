from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config import SEMANTIC_MODEL_DIR  # noqa: E402

MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def model_ready(path: Path) -> bool:
    required_any = (
        path / "model.safetensors",
        path / "pytorch_model.bin",
    )
    return (
        (path / "config.json").exists()
        and (path / "tokenizer.json").exists()
        and any(item.exists() for item in required_any)
    )


def main() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    target = SEMANTIC_MODEL_DIR
    if model_ready(target):
        print(f"Semantic model already prepared: {target}")
        return

    print("Preparing JAM multilingual semantic model...")
    print(f"Model: {MODEL_ID}")
    print(f"Target: {target}")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_ID)
    target.mkdir(parents=True, exist_ok=True)
    model.save(str(target), safe_serialization=True)

    if not model_ready(target):
        raise RuntimeError(
            "The semantic model was downloaded but the local release copy is incomplete."
        )

    print("Semantic model prepared for offline JAM analysis.")


if __name__ == "__main__":
    main()

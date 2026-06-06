"""Pre-build the FAISS knowledge base (run once before deploy)."""

from __future__ import annotations

import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    with open(os.path.join(ROOT, "config.yaml"), "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    provider_cfg = config.get("provider", {}) or {}
    os.environ.setdefault("EMBEDDING_PROVIDER", str(provider_cfg.get("embeddings", "local")))

    from rag.embeddings import get_embedder
    from rag.knowledge_base import create_medical_knowledge_base

    models = config.get("models", {}) or {}
    embedder = get_embedder(models.get("embedder", "all-MiniLM-L6-v2"))
    print("Building knowledge base (this may take several minutes on first run)...")
    kb = create_medical_knowledge_base(embedder, config)
    if kb is None:
        print("ERROR: Knowledge base build returned None. Check data/ paths and PDF files.")
        sys.exit(1)
    print("Knowledge base built successfully.")


if __name__ == "__main__":
    main()

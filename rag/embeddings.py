"""Embedding provider factory for the medical knowledge base."""

from __future__ import annotations

import os


def get_embedder(model: str | None = None):
    provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
    model = model or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    if provider == "openrouter":
        return _get_openrouter_embedder(model)

    if provider == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except Exception:  # pragma: no cover
            from langchain_community.embeddings import OllamaEmbeddings

        return OllamaEmbeddings(model=model)

    return _get_local_embedder(model)


def _get_local_embedder(model: str):
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except Exception:  # pragma: no cover
        from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def _get_openrouter_embedder(model: str):
    from rag.openrouter_embeddings import OpenRouterEmbeddings

    return OpenRouterEmbeddings(model=model)

"""Factory for LLM clients (OpenRouter or local Ollama)."""

from __future__ import annotations

import os


def get_llm(model: str):
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    if provider == "ollama":
        from utils.ollama_client import OllamaLLM

        return OllamaLLM(model=model)

    from utils.openrouter_client import OpenRouterLLM

    return OpenRouterLLM(model=model)

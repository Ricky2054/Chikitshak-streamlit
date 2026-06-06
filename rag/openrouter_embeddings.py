"""OpenRouter embeddings via the OpenAI-compatible /embeddings endpoint."""

from __future__ import annotations

import os
from typing import List

import httpx

try:
    from langchain_core.embeddings import Embeddings
except Exception:  # pragma: no cover
    from langchain.embeddings.base import Embeddings  # type: ignore


class OpenRouterEmbeddings(Embeddings):
    def __init__(self, model: str = "openai/text-embedding-3-small"):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required when EMBEDDING_PROVIDER=openrouter")

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={"model": self.model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        batch_size = 32
        vectors: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            vectors.extend(self._embed_batch(texts[i : i + batch_size]))
        return vectors

    def embed_query(self, text: str) -> List[float]:
        return self._embed_batch([text])[0]

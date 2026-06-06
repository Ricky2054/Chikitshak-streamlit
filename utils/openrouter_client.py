"""OpenRouter chat-completions client (OpenAI-compatible API)."""

from __future__ import annotations

import asyncio
import os

import httpx

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterLLM:
    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL).rstrip("/")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "https://medical-rag.local")
        self.app_name = os.getenv("OPENROUTER_APP_NAME", "Medical RAG System")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

    async def ping(self) -> bool:
        if not self.api_key:
            return False
        timeout = httpx.Timeout(10.0, connect=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{self.base_url}/models", headers=self._headers())
                return response.status_code == 200
        except Exception:
            return False

    async def agenerate(self, prompts, context=None):
        if not self.api_key:
            return ["[ERROR: OPENROUTER_API_KEY is not set. Add it to your environment or .env file.]"]

        results = []
        timeout = httpx.Timeout(120.0, connect=10.0)
        max_retries = 2

        async with httpx.AsyncClient(timeout=timeout) as client:
            for prompt in prompts:
                for attempt in range(max_retries):
                    try:
                        response = await client.post(
                            f"{self.base_url}/chat/completions",
                            headers=self._headers(),
                            json={
                                "model": self.model,
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.3,
                            },
                        )
                        if response.status_code != 200:
                            detail = response.text[:500]
                            results.append(
                                f"[ERROR: OpenRouter request failed ({response.status_code}): {detail}]"
                            )
                            break

                        data = response.json()
                        content = (
                            data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                        )
                        results.append(content or "")
                        break
                    except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as exc:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 * (attempt + 1))
                            continue
                        results.append(
                            f"[ERROR: OpenRouter timed out or is unreachable. Details: {exc}]"
                        )
                    except Exception as exc:
                        results.append(f"[ERROR: OpenRouter error: {exc}]")
                        break
        return results

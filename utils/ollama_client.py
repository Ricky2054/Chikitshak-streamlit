import httpx
import asyncio
import os

class OllamaLLM:
    def __init__(self, model):
        self.model = model
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.api_url = f"{self.base_url}/api/generate"  # Default Ollama endpoint

    async def ping(self) -> bool:
        """Return True if Ollama server is reachable."""
        timeout = httpx.Timeout(2.0, connect=1.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def agenerate(self, prompts, context=None):
        results = []
        timeout = httpx.Timeout(60.0, connect=5.0)  # Fail faster when Ollama is down
        max_retries = 2
        async with httpx.AsyncClient(timeout=timeout) as client:
            for prompt in prompts:
                for attempt in range(max_retries):
                    try:
                        response = await client.post(
                            self.api_url,
                            json={"model": self.model, "prompt": prompt, "stream": False}
                        )
                        data = response.json()
                        results.append(data.get("response", ""))
                        break  # Success, break retry loop
                    except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            results.append(f"[ERROR: Ollama server timed out or is not responding. Please ensure Ollama is running and the model is loaded. Details: {str(e)}]")
                    except Exception as e:
                        results.append(f"[ERROR: Ollama server error: {str(e)}]")
                        break
        return results 
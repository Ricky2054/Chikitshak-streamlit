import httpx
import asyncio

class OllamaLLM:
    def __init__(self, model):
        self.model = model
        self.api_url = "http://localhost:11434/api/generate"  # Default Ollama endpoint

    async def agenerate(self, prompts, context=None):
        results = []
        timeout = httpx.Timeout(120.0, connect=30.0)  # 2 minutes total, 30s connect
        max_retries = 3
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
                    except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            results.append(f"[ERROR: Ollama server timed out or is not responding. Please ensure Ollama is running and the model is loaded. Details: {str(e)}]")
                    except Exception as e:
                        results.append(f"[ERROR: Ollama server error: {str(e)}]")
                        break
        return results 
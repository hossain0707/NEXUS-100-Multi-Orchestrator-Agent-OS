import httpx

from nexus.config import settings


class LLMProvider:
    @property
    def configured(self) -> bool:
        return bool(settings.llm_api_key)

    async def complete(self, system: str, prompt: str) -> str:
        if not self.configured:
            return "LLM provider is not configured; mission retained for deterministic planning."
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        timeout = httpx.Timeout(60.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


llm = LLMProvider()

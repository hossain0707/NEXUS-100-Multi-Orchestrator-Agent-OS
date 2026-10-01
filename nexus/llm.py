from dataclasses import dataclass

import httpx

from nexus.config import settings
from nexus.model_router import ReasoningEffort


class LLMNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class CompletionResult:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None


class LLMProvider:
    @property
    def configured(self) -> bool:
        return bool(
            settings.backend_model_execution_enabled
            and settings.llm_api_key
        )

    async def complete(
        self,
        *,
        model: str,
        reasoning_effort: ReasoningEffort,
        max_output_tokens: int,
        system: str,
        prompt: str,
    ) -> CompletionResult:
        if not self.configured:
            raise LLMNotConfigured(
                "Backend model execution is disabled or no provider API key is configured."
            )

        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_output_tokens,
        }

        # Different providers expose reasoning controls under different names.
        # Operators opt in by configuring the provider-specific parameter name.
        if settings.llm_reasoning_parameter:
            effort_value = "xhigh" if reasoning_effort is ReasoningEffort.extra_high else reasoning_effort.value
            payload[settings.llm_reasoning_parameter] = effort_value

        timeout = httpx.Timeout(90.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage") or {}
        return CompletionResult(
            text=choice["message"]["content"],
            model=data.get("model", model),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            finish_reason=choice.get("finish_reason"),
        )


llm = LLMProvider()

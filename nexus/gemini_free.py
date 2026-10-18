"""Strictly opt-in, bounded Google Gemini API test; never active by default.

The operator must confirm a genuinely free-tier Gemini project and quota.
No software-only guard can guarantee zero charges if provider billing is enabled.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from nexus.config import settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
FREE_MODELS = frozenset({"gemini-2.5-flash-lite", "gemini-2.5-flash"})


class GeminiDisabled(RuntimeError):
    """Operator configuration is insufficient for a provider request."""


class GeminiUpstreamError(RuntimeError):
    """Sanitized model provider failure without response body or secret."""


@dataclass(frozen=True)
class GeminiSmokeResult:
    output: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None


def ready() -> bool:
    return bool(
        settings.gemini_smoke_enabled
        and settings.gemini_free_tier_ack
        and settings.api_token
        and settings.gemini_api_key
        and settings.gemini_model in FREE_MODELS
    )


def public_config() -> dict:
    return {
        "enabled": ready(),
        "model": settings.gemini_model,
        "operator_confirmed_free_tier": settings.gemini_free_tier_ack,
        "max_output_tokens": 96,
    }


async def complete(
    prompt: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> GeminiSmokeResult:
    """One non-streaming request: no retries, fallback or external side effects."""
    if not ready():
        raise GeminiDisabled("Gemini smoke generation is disabled or not configured")
    if not 3 <= len(prompt.strip()) <= 500:
        raise ValueError("Prompt must contain between 3 and 500 characters")
    payload = {
        "model": settings.gemini_model,
        "messages": [
            {"role": "system", "content": "You are a concise enterprise AI agent. "
             "Answer factually and do not request secrets."},
            {"role": "user", "content": prompt.strip()},
        ],
        "max_tokens": 96,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(15, connect=5),
            follow_redirects=False,
        ) as client:
            response = await client.post(
                GEMINI_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.gemini_api_key}",
                    "Content-Type": "application/json",
                },
            )
        if response.status_code == 429:
            raise GeminiUpstreamError("quota_exceeded")
        if response.status_code >= 400:
            raise GeminiUpstreamError("upstream_request_failed")
        data = response.json()
        choice = data["choices"][0]
        output = choice["message"]["content"]
        if not isinstance(output, str) or not output.strip():
            raise ValueError("empty or invalid output")
        usage = data.get("usage") or {}
        return GeminiSmokeResult(
            output=output[:2000],
            model=settings.gemini_model,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            finish_reason=choice.get("finish_reason"),
        )
    except GeminiUpstreamError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
        # Do not leak upstream error response data, which could include identifiers.
        raise GeminiUpstreamError("upstream_unavailable_or_invalid_response") from exc

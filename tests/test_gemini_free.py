"""Offline Gemini tests never call external providers or consume quota."""
import json

import httpx
import pytest

from nexus.config import settings
from nexus import gemini_free


@pytest.mark.asyncio
async def test_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "gemini_smoke_enabled", False)
    with pytest.raises(gemini_free.GeminiDisabled):
        await gemini_free.complete("Summarize the plan")


@pytest.mark.asyncio
async def test_mock_request_is_bounded_and_successful(monkeypatch):
    monkeypatch.setattr(settings, "api_token", "test-control-token")
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    monkeypatch.setattr(settings, "gemini_smoke_enabled", True)
    monkeypatch.setattr(settings, "gemini_free_tier_ack", True)
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash-lite")
    requests = []

    def handler(req):
        assert str(req.url) == gemini_free.GEMINI_URL
        assert req.headers["Authorization"] == "Bearer fake-key"
        body = json.loads(req.content)
        assert body["max_tokens"] == 96
        assert body["model"] == "gemini-2.5-flash-lite"
        assert body["stream"] is False
        requests.append(body)
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "Mock response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3},
        })

    response = await gemini_free.complete(
        "Create a pilot plan", transport=httpx.MockTransport(handler)
    )
    assert response.output == "Mock response"
    assert response.input_tokens == 10
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_rate_limit_is_sanitized(monkeypatch):
    monkeypatch.setattr(settings, "api_token", "test-control-token")
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    monkeypatch.setattr(settings, "gemini_smoke_enabled", True)
    monkeypatch.setattr(settings, "gemini_free_tier_ack", True)
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-flash-lite")
    transport = httpx.MockTransport(
        lambda req: httpx.Response(429, text="SECRET_PROVIDER_ERROR_BODY")
    )
    with pytest.raises(gemini_free.GeminiUpstreamError, match="quota_exceeded") as exc:
        await gemini_free.complete("Create a pilot plan", transport=transport)
    assert "SECRET_PROVIDER_ERROR_BODY" not in str(exc.value)


@pytest.mark.asyncio
async def test_disallowed_model_never_calls_provider(monkeypatch):
    monkeypatch.setattr(settings, "api_token", "test-control-token")
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")
    monkeypatch.setattr(settings, "gemini_smoke_enabled", True)
    monkeypatch.setattr(settings, "gemini_free_tier_ack", True)
    monkeypatch.setattr(settings, "gemini_model", "gemini-2.5-pro")
    assert not gemini_free.ready()
    with pytest.raises(gemini_free.GeminiDisabled):
        await gemini_free.complete("Create a pilot plan")

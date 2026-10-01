from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterable

import httpx

from nexus.config import settings


@dataclass(frozen=True)
class ModelProfile:
    id: str
    family: str
    quality: float
    speed: float
    cost_index: float
    reasoning_efforts: tuple[str, ...]
    specializations: tuple[str, ...] = ()
    source: str = "configured"
    available: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


REASONING_LEVELS = ("low", "medium", "high", "extra_high")

_EXCLUDED_MODEL_MARKERS = (
    "image",
    "realtime",
    "transcribe",
    "whisper",
    "tts",
    "embedding",
    "moderation",
    "audio",
)


def _profile_for(model_id: str, *, source: str, available: bool) -> ModelProfile | None:
    lower = model_id.lower()
    if any(marker in lower for marker in _EXCLUDED_MODEL_MARKERS):
        return None

    if "cyber" in lower or "daybreak-red" in lower:
        return ModelProfile(
            id=model_id,
            family="cyber",
            quality=0.98,
            speed=0.45,
            cost_index=4.5,
            reasoning_efforts=REASONING_LEVELS,
            specializations=("security",),
            source=source,
            available=available,
        )

    if "codex" in lower:
        return ModelProfile(
            id=model_id,
            family="codex",
            quality=0.92,
            speed=0.65,
            cost_index=2.4,
            reasoning_efforts=REASONING_LEVELS,
            specializations=("engineering",),
            source=source,
            available=available,
        )

    if "rosalind" in lower:
        return ModelProfile(
            id=model_id,
            family="research",
            quality=0.95,
            speed=0.50,
            cost_index=3.0,
            reasoning_efforts=REASONING_LEVELS,
            specializations=("research",),
            source=source,
            available=available,
        )

    if "astra" in lower:
        return ModelProfile(
            id=model_id,
            family="premium",
            quality=1.00,
            speed=0.45,
            cost_index=5.0,
            reasoning_efforts=REASONING_LEVELS,
            source=source,
            available=available,
        )

    if "sol" in lower:
        return ModelProfile(
            id=model_id,
            family="strong",
            quality=0.92,
            speed=0.72,
            cost_index=2.2,
            reasoning_efforts=REASONING_LEVELS,
            source=source,
            available=available,
        )

    if "terra" in lower:
        return ModelProfile(
            id=model_id,
            family="balanced",
            quality=0.82,
            speed=0.82,
            cost_index=1.5,
            reasoning_efforts=REASONING_LEVELS,
            source=source,
            available=available,
        )

    if "luna" in lower:
        return ModelProfile(
            id=model_id,
            family="fast",
            quality=0.72,
            speed=0.96,
            cost_index=0.5,
            reasoning_efforts=REASONING_LEVELS,
            source=source,
            available=available,
        )

    if lower.startswith("gpt-"):
        return ModelProfile(
            id=model_id,
            family="general",
            quality=0.78,
            speed=0.75,
            cost_index=2.0,
            reasoning_efforts=REASONING_LEVELS,
            source=source,
            available=available,
        )

    return None


class ModelCatalog:
    def __init__(self):
        self._models: dict[str, ModelProfile] = {}
        self._last_refresh: datetime | None = None
        self._last_error: str | None = None
        self._seed_configured_models()

    def _seed_configured_models(self) -> None:
        configured = {
            settings.model_fast,
            settings.model_balanced,
            settings.model_strong,
            settings.model_premium,
        }
        for model_id in configured:
            profile = _profile_for(model_id, source="configured", available=True)
            if profile:
                self._models[profile.id] = profile

    @property
    def last_refresh(self) -> datetime | None:
        return self._last_refresh

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def stale(self) -> bool:
        if self._last_refresh is None:
            return True
        return datetime.now(UTC) - self._last_refresh > timedelta(
            seconds=settings.model_catalog_ttl_seconds
        )

    def snapshot(self) -> list[ModelProfile]:
        return sorted(
            self._models.values(),
            key=lambda item: (item.cost_index, -item.quality, item.id),
        )

    def public_snapshot(self) -> dict:
        return {
            "models": [item.to_dict() for item in self.snapshot()],
            "count": len(self._models),
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "last_error": self._last_error,
            "discovery_enabled": settings.model_discovery_enabled,
        }

    async def refresh(self) -> dict:
        if not settings.model_discovery_enabled:
            return self.public_snapshot()
        if not settings.llm_api_key:
            self._last_error = "model discovery requires NEXUS_LLM_API_KEY"
            return self.public_snapshot()

        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        timeout = httpx.Timeout(20.0, connect=5.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{settings.llm_base_url.rstrip('/')}/models",
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
            discovered = {}
            for item in payload.get("data", []):
                model_id = item.get("id")
                if not model_id:
                    continue
                profile = _profile_for(model_id, source="provider", available=True)
                if profile:
                    discovered[profile.id] = profile
            if discovered:
                self._models.update(discovered)
            self._last_refresh = datetime.now(UTC)
            self._last_error = None
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            self._last_error = f"{type(exc).__name__}: {exc}"
        return self.public_snapshot()

    def candidates(
        self,
        *,
        minimum_quality: float,
        reasoning_effort: str,
        domain: str,
    ) -> list[ModelProfile]:
        models = [
            model
            for model in self.snapshot()
            if model.available
            and model.quality >= minimum_quality
            and reasoning_effort in model.reasoning_efforts
        ]
        specialized = [
            model for model in models if domain in model.specializations
        ]
        return specialized or models

    def choose(
        self,
        *,
        minimum_quality: float,
        reasoning_effort: str,
        domain: str,
    ) -> ModelProfile | None:
        candidates = self.candidates(
            minimum_quality=minimum_quality,
            reasoning_effort=reasoning_effort,
            domain=domain,
        )
        if not candidates:
            return None

        return min(
            candidates,
            key=lambda item: (
                item.cost_index,
                -item.speed,
                -item.quality,
                item.id,
            ),
        )

    def stronger_than(
        self,
        selected: ModelProfile,
        *,
        reasoning_effort: str,
        domain: str,
    ) -> list[ModelProfile]:
        candidates = [
            model
            for model in self.candidates(
                minimum_quality=min(1.0, selected.quality + 0.01),
                reasoning_effort=reasoning_effort,
                domain=domain,
            )
            if model.id != selected.id
        ]
        return sorted(
            candidates,
            key=lambda item: (
                item.cost_index,
                -item.quality,
                item.id,
            ),
        )

    def replace_for_test(self, models: Iterable[ModelProfile]) -> None:
        self._models = {model.id: model for model in models}


model_catalog = ModelCatalog()

from nexus.config import settings
from nexus.model_catalog import ModelCatalog, ModelProfile
from nexus.model_router import ReasoningEffort


def test_catalog_prefers_cheapest_qualified_model():
    catalog = ModelCatalog()
    catalog.replace_for_test(
        [
            ModelProfile(
                id="small-general",
                family="general",
                quality=0.80,
                speed=0.95,
                cost_index=0.5,
                reasoning_efforts=("low", "medium"),
            ),
            ModelProfile(
                id="large-general",
                family="general",
                quality=0.95,
                speed=0.60,
                cost_index=3.0,
                reasoning_efforts=("low", "medium", "high"),
            ),
        ]
    )

    selected = catalog.choose(
        minimum_quality=0.78,
        reasoning_effort=ReasoningEffort.medium.value,
        domain="business",
    )
    assert selected is not None
    assert selected.id == "small-general"


def test_catalog_prefers_domain_specialist_when_qualified():
    catalog = ModelCatalog()
    catalog.replace_for_test(
        [
            ModelProfile(
                id="general-strong",
                family="general",
                quality=0.95,
                speed=0.80,
                cost_index=1.0,
                reasoning_efforts=("high",),
            ),
            ModelProfile(
                id="security-specialist",
                family="cyber",
                quality=0.96,
                speed=0.60,
                cost_index=2.0,
                reasoning_efforts=("high",),
                specializations=("security",),
            ),
        ]
    )

    selected = catalog.choose(
        minimum_quality=0.90,
        reasoning_effort=ReasoningEffort.high.value,
        domain="security",
    )
    assert selected is not None
    assert selected.id == "security-specialist"


def test_catalog_escalation_only_returns_stronger_models():
    catalog = ModelCatalog()
    fast = ModelProfile(
        id="fast-model",
        family="fast",
        quality=0.72,
        speed=0.95,
        cost_index=0.5,
        reasoning_efforts=("low", "medium"),
    )
    strong = ModelProfile(
        id="strong-model",
        family="strong",
        quality=0.92,
        speed=0.70,
        cost_index=2.0,
        reasoning_efforts=("low", "medium", "high"),
    )
    premium = ModelProfile(
        id="premium-model",
        family="premium",
        quality=1.0,
        speed=0.45,
        cost_index=5.0,
        reasoning_efforts=("low", "medium", "high", "extra_high"),
    )
    catalog.replace_for_test([fast, strong, premium])

    models = catalog.stronger_than(
        fast,
        reasoning_effort="medium",
        domain="engineering",
    )
    assert [model.id for model in models] == ["strong-model", "premium-model"]


async def test_catalog_refresh_respects_ttl_without_provider_key():
    catalog = ModelCatalog()
    original_key = settings.llm_api_key
    original_enabled = settings.model_discovery_enabled
    try:
        settings.llm_api_key = None
        settings.model_discovery_enabled = True

        first = await catalog.refresh()
        first_attempt = catalog.last_attempt
        assert first_attempt is not None
        assert first["last_error"] == "model discovery requires NEXUS_LLM_API_KEY"

        second = await catalog.refresh()
        assert catalog.last_attempt == first_attempt
        assert second["count"] == first["count"]
    finally:
        settings.llm_api_key = original_key
        settings.model_discovery_enabled = original_enabled

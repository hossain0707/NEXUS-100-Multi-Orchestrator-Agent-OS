from nexus.model_router import ModelTier, ReasoningEffort, model_router
from nexus.orchestrator import orchestrator
from nexus.registry import registry


def test_existing_100_agents_are_preserved():
    assert len(registry.agents) == 100


def test_simple_task_uses_fast_low_effort():
    objective = "Summarize meeting notes"
    route = orchestrator.route(objective)
    strategy = model_router.plan(objective, route)

    assert strategy["decisions"]
    decision = strategy["decisions"][0]
    assert decision["tier"] == ModelTier.fast.value
    assert decision["reasoning_effort"] == ReasoningEffort.low.value
    assert decision["max_output_tokens"] > 0


def test_complex_security_task_uses_stronger_compute():
    objective = (
        "Research and design a production security architecture for a distributed "
        "LLM API, evaluate deployment tradeoffs, benchmark GPU serving latency, "
        "debug reliability risks, and perform a vulnerability threat review."
    )
    route = orchestrator.route(objective)
    strategy = model_router.plan(objective, route)

    tiers = {item["tier"] for item in strategy["decisions"]}
    efforts = {item["reasoning_effort"] for item in strategy["decisions"]}

    assert tiers & {ModelTier.strong.value, ModelTier.premium.value}
    assert efforts & {ReasoningEffort.high.value, ReasoningEffort.extra_high.value}


def test_escalation_is_bounded_and_only_moves_up():
    objective = "Implement and deploy production API security"
    route = orchestrator.route(objective)
    strategy = model_router.plan(objective, route)

    for decision in strategy["decisions"]:
        assert len(decision["escalation_models"]) <= 2
        assert decision["model"] not in decision["escalation_models"]

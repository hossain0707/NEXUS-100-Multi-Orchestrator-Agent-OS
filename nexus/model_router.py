from dataclasses import asdict, dataclass
from enum import Enum

from nexus.config import settings
from nexus.model_catalog import model_catalog


class ModelTier(str, Enum):
    fast = "fast"
    balanced = "balanced"
    strong = "strong"
    premium = "premium"


class ReasoningEffort(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    extra_high = "extra_high"


@dataclass(frozen=True)
class ModelDecision:
    agent_id: str
    domain: str
    capability: str
    tier: ModelTier
    model: str
    reasoning_effort: ReasoningEffort
    max_output_tokens: int
    complexity_score: float
    confidence: float
    escalation_models: tuple[str, ...]
    rationale: tuple[str, ...]
    selection_source: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tier"] = self.tier.value
        data["reasoning_effort"] = self.reasoning_effort.value
        data["escalation_models"] = list(self.escalation_models)
        data["rationale"] = list(self.rationale)
        return data


TIER_ORDER = [
    ModelTier.fast,
    ModelTier.balanced,
    ModelTier.strong,
    ModelTier.premium,
]

TIER_MIN_QUALITY = {
    ModelTier.fast: 0.65,
    ModelTier.balanced: 0.78,
    ModelTier.strong: 0.90,
    ModelTier.premium: 0.97,
}

DOMAIN_FLOOR = {
    "productivity": ModelTier.fast,
    "personal": ModelTier.fast,
    "career": ModelTier.fast,
    "business": ModelTier.balanced,
    "data": ModelTier.balanced,
    "finance": ModelTier.balanced,
    "research": ModelTier.balanced,
    "engineering": ModelTier.balanced,
    "infrastructure": ModelTier.balanced,
    "security": ModelTier.strong,
}

COMPLEX_TERMS = {
    "architecture",
    "benchmark",
    "debug",
    "distributed",
    "evaluate",
    "migration",
    "optimize",
    "production",
    "reason",
    "research",
    "security",
    "threat",
    "tradeoff",
}

HIGH_STAKES_TERMS = {
    "critical",
    "financial",
    "incident",
    "production",
    "security",
    "sensitive",
    "vulnerability",
}


class AdaptiveModelRouter:
    policy_version = "adaptive-model-v2-catalog"

    @staticmethod
    def _fallback_model_for(tier: ModelTier) -> str:
        return {
            ModelTier.fast: settings.model_fast,
            ModelTier.balanced: settings.model_balanced,
            ModelTier.strong: settings.model_strong,
            ModelTier.premium: settings.model_premium,
        }[tier]

    @staticmethod
    def _token_budget(effort: ReasoningEffort) -> int:
        return {
            ReasoningEffort.low: settings.max_output_tokens_low,
            ReasoningEffort.medium: settings.max_output_tokens_medium,
            ReasoningEffort.high: settings.max_output_tokens_high,
            ReasoningEffort.extra_high: settings.max_output_tokens_extra_high,
        }[effort]

    @staticmethod
    def _tier_index(tier: ModelTier) -> int:
        return TIER_ORDER.index(tier)

    def score(
        self,
        objective: str,
        domain_count: int,
        priority: str = "normal",
    ) -> tuple[float, list[str]]:
        text = objective.lower()
        words = text.split()
        score = 0.12
        reasons = []

        if len(words) >= 25:
            score += 0.12
            reasons.append("longer task")
        if len(words) >= 60:
            score += 0.10
            reasons.append("large prompt")
        if domain_count >= 2:
            score += min(0.24, 0.08 * (domain_count - 1))
            reasons.append("cross-domain coordination")

        hits = sum(1 for term in COMPLEX_TERMS if term in text)
        if hits:
            score += min(0.28, hits * 0.055)
            reasons.append("complexity signals")

        high_stakes_hits = sum(1 for term in HIGH_STAKES_TERMS if term in text)
        if high_stakes_hits:
            score += min(0.18, high_stakes_hits * 0.06)
            reasons.append("higher-stakes context")

        if priority.lower() in {"high", "critical", "urgent"}:
            score += 0.08
            reasons.append("high priority")

        return min(score, 1.0), reasons or ["routine task"]

    @staticmethod
    def _effort(score: float) -> ReasoningEffort:
        if score < 0.30:
            return ReasoningEffort.low
        if score < 0.58:
            return ReasoningEffort.medium
        if score < 0.82:
            return ReasoningEffort.high
        return ReasoningEffort.extra_high

    @staticmethod
    def _score_tier(score: float) -> ModelTier:
        if score < 0.30:
            return ModelTier.fast
        if score < 0.58:
            return ModelTier.balanced
        if score < 0.82:
            return ModelTier.strong
        return ModelTier.premium

    def _select_model(
        self,
        tier: ModelTier,
        effort: ReasoningEffort,
        domain: str,
    ) -> tuple[str, tuple[str, ...], str]:
        selected = model_catalog.choose(
            minimum_quality=TIER_MIN_QUALITY[tier],
            reasoning_effort=effort.value,
            domain=domain,
        )

        if selected is not None:
            stronger = model_catalog.stronger_than(
                selected,
                reasoning_effort=effort.value,
                domain=domain,
            )
            fallbacks = tuple(
                profile.id
                for profile in stronger[: settings.max_model_escalations]
            )
            return selected.id, fallbacks, selected.source

        model = self._fallback_model_for(tier)
        later_models = [
            self._fallback_model_for(candidate)
            for candidate in TIER_ORDER[self._tier_index(tier) + 1 :]
        ]
        fallbacks = tuple(
            item
            for index, item in enumerate(later_models)
            if item != model and item not in later_models[:index]
        )[: settings.max_model_escalations]
        return model, fallbacks, "tier-fallback"

    def choose(
        self,
        objective: str,
        step,
        domain_count: int,
        priority: str = "normal",
    ) -> ModelDecision:
        score, reasons = self.score(objective, domain_count, priority)
        requested = self._score_tier(score)
        floor = DOMAIN_FLOOR.get(step.domain, ModelTier.balanced)
        tier = TIER_ORDER[max(self._tier_index(requested), self._tier_index(floor))]

        if tier != requested:
            reasons.append(f"{step.domain} domain floor")

        effort = self._effort(score)
        model, escalation_models, source = self._select_model(
            tier,
            effort,
            step.domain,
        )

        thresholds = [0.30, 0.58, 0.82]
        distance = min(abs(score - threshold) for threshold in thresholds)
        confidence = min(0.98, 0.72 + distance)

        return ModelDecision(
            agent_id=step.agent_id,
            domain=step.domain,
            capability=step.capability,
            tier=tier,
            model=model,
            reasoning_effort=effort,
            max_output_tokens=self._token_budget(effort),
            complexity_score=round(score, 3),
            confidence=round(confidence, 3),
            escalation_models=escalation_models,
            rationale=tuple(reasons),
            selection_source=source,
        )

    def plan(self, objective: str, route: list, priority: str = "normal") -> dict:
        domain_count = len({step.domain for step in route})
        decisions = [
            self.choose(objective, step, domain_count, priority).to_dict()
            for step in route
        ]
        return {
            "policy": self.policy_version,
            "routing_enabled": settings.model_routing_enabled,
            "backend_execution_enabled": settings.backend_model_execution_enabled,
            "catalog_models": len(model_catalog.snapshot()),
            "catalog_last_refresh": (
                model_catalog.last_refresh.isoformat()
                if model_catalog.last_refresh
                else None
            ),
            "decisions": decisions,
            "max_planned_output_tokens": sum(
                decision["max_output_tokens"] for decision in decisions
            ),
        }


model_router = AdaptiveModelRouter()

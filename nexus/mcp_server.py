from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from nexus import __version__
from nexus.config import settings
from nexus.model_catalog import model_catalog
from nexus.model_router import model_router
from nexus.models import RouteStep
from nexus.orchestrator import orchestrator
from nexus.registry import DOMAIN_CAPABILITIES, registry

Priority = Literal["low", "normal", "high", "critical"]
Objective = Annotated[
    str,
    Field(
        min_length=3,
        max_length=4000,
        description=(
            "The user's planning objective. Include the concrete task, constraints, "
            "and domains that matter. NEXUS uses this text only for routing and "
            "strategy calculation; the public plugin does not execute the task."
        ),
    ),
]


class SystemStatusOutput(BaseModel):
    status: Literal["healthy"] = Field(description="Public NEXUS runtime health state.")
    version: str = Field(description="Deployed NEXUS Python service version.")
    domains: int = Field(description="Number of registered domain orchestrators.")
    agents: int = Field(description="Number of registered specialist agents.")
    adaptive_model_routing: bool = Field(
        description="Whether adaptive model/effort strategy calculation is enabled."
    )
    backend_model_execution: bool = Field(
        description=(
            "Whether optional NEXUS-managed paid backend inference is enabled. "
            "This does not indicate or change the ChatGPT host model."
        )
    )
    model_catalog_size: int = Field(
        description="Number of model profiles currently available to the strategy router."
    )


class DomainCatalogOutput(BaseModel):
    domains: dict[str, list[str]] = Field(
        description="Mapping of each NEXUS domain to its ten specialist capabilities."
    )


class MissionPreviewOutput(BaseModel):
    objective: str
    priority: Priority
    route: list[RouteStep] = Field(
        description="Stateless ordered route through selected domains and specialist agents."
    )


class PublicModelProfile(BaseModel):
    id: str = Field(description="Configured or discovered model identifier.")
    family: str = Field(description="NEXUS model-family classification.")
    quality: float = Field(
        description="Internal relative quality score used by the NEXUS routing policy."
    )
    speed: float = Field(
        description="Internal relative speed score used by the NEXUS routing policy."
    )
    cost_index: float = Field(
        description=(
            "Internal relative cost index used for routing. It is not a live provider price."
        )
    )
    reasoning_efforts: list[str] = Field(
        description="Reasoning-effort levels this catalog profile can represent."
    )
    specializations: list[str] = Field(
        description="NEXUS domains for which this profile is treated as specialized."
    )
    available: bool


class ModelCatalogOutput(BaseModel):
    count: int
    models: list[PublicModelProfile]


class ModelDecisionOutput(BaseModel):
    agent_id: str
    domain: str
    capability: str
    tier: Literal["fast", "balanced", "strong", "premium"]
    model: str = Field(
        description="Concrete configured/discovered backend model ID NEXUS would select."
    )
    reasoning_effort: Literal["low", "medium", "high", "extra_high"]
    max_output_tokens: int
    complexity_score: float
    confidence: float
    escalation_models: list[str] = Field(
        description="Bounded stronger fallback model IDs, ordered by policy."
    )
    rationale: list[str]
    selection_source: str


class ModelStrategyOutput(BaseModel):
    policy: str
    routing_enabled: bool
    backend_execution_enabled: bool = Field(
        description=(
            "Whether NEXUS-managed backend inference is enabled. The MCP recommendation "
            "tool itself never performs paid inference and cannot change ChatGPT's model."
        )
    )
    catalog_models: int
    decisions: list[ModelDecisionOutput]
    max_planned_output_tokens: int


class StrategyRecommendationOutput(BaseModel):
    route: list[RouteStep]
    model_strategy: ModelStrategyOutput


# Public directory MCP surface: read-only planning, routing and model-strategy
# inspection. Stateful/write operations remain on the protected REST control
# plane and are intentionally not exposed to marketplace users.
mcp = FastMCP(
    "NEXUS-100",
    instructions=(
        "NEXUS-100 is a read-only orchestration and adaptive model-strategy plugin. "
        "Use it when the user asks to inspect NEXUS capabilities, preview which "
        "domains/agents would handle a task, or calculate a NEXUS backend model and "
        "reasoning strategy. The public tools do not deploy code, send messages, "
        "spend money, modify external systems, create tracked missions, or execute "
        "backend model inference. NEXUS model recommendations apply only to optional "
        "NEXUS-managed backend calls; they never change the model selected in ChatGPT."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        # Cloud Run terminates TLS and validates routing before traffic reaches
        # the app. This avoids rejecting the managed run.app Host value.
        enable_dns_rebinding_protection=False,
    ),
)


def _readonly(title: str) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


@mcp.tool(annotations=_readonly("Get NEXUS system status"))
def get_system_status() -> SystemStatusOutput:
    """Use when the user asks whether NEXUS is available or what core features are enabled.

    Returns public service/version information and registry counts only. It does not
    return request IDs, user data, logs, secrets, or internal diagnostics.
    """
    return SystemStatusOutput(
        status="healthy",
        version=__version__,
        domains=len(DOMAIN_CAPABILITIES),
        agents=len(registry.agents),
        adaptive_model_routing=settings.model_routing_enabled,
        backend_model_execution=settings.backend_model_execution_enabled,
        model_catalog_size=len(model_catalog.snapshot()),
    )


@mcp.tool(annotations=_readonly("List NEXUS domains and specialist capabilities"))
def list_domains() -> DomainCatalogOutput:
    """Use when the user wants to discover what NEXUS can plan or which agents exist.

    Returns the fixed 10-domain capability map. It does not inspect external systems.
    """
    return DomainCatalogOutput(domains=DOMAIN_CAPABILITIES)


@mcp.tool(annotations=_readonly("Preview a NEXUS mission plan"))
def plan_mission(
    objective: Objective,
    priority: Priority = "normal",
) -> MissionPreviewOutput:
    """Use when the user wants a stateless NEXUS routing plan for a concrete objective.

    Returns the selected domains, orchestrators, agent IDs, and capabilities. It does
    not persist a mission, enqueue work, call a model provider, or perform external
    actions. Use recommend_model_strategy instead when model/effort allocation is the
    main question.
    """
    return MissionPreviewOutput.model_validate(orchestrator.preview(objective, priority))


@mcp.tool(annotations=_readonly("List NEXUS model catalog"))
def list_model_catalog() -> ModelCatalogOutput:
    """Use when the user explicitly wants the model profiles NEXUS can route across.

    Returns sanitized cached model metadata only. Relative quality/speed/cost fields
    are NEXUS policy scores, not provider benchmarks or live prices. No credentials,
    provider diagnostics, timestamps, request telemetry, or user data are returned.
    """
    models = [
        PublicModelProfile(
            id=item.id,
            family=item.family,
            quality=item.quality,
            speed=item.speed,
            cost_index=item.cost_index,
            reasoning_efforts=list(item.reasoning_efforts),
            specializations=list(item.specializations),
            available=item.available,
        )
        for item in model_catalog.snapshot()
    ]
    return ModelCatalogOutput(count=len(models), models=models)


@mcp.tool(annotations=_readonly("Recommend a NEXUS adaptive model strategy"))
async def recommend_model_strategy(
    objective: Objective,
    priority: Priority = "normal",
) -> StrategyRecommendationOutput:
    """Use when the user asks how NEXUS would allocate models, effort, and token budgets.

    The tool may refresh the server-owned provider model catalog, but it never sends
    the user's objective to a model provider and never performs paid inference. The
    returned model IDs are recommendations for optional NEXUS-managed backend calls;
    they cannot silently change the ChatGPT host model selected by the user.
    """
    await model_catalog.refresh()
    route = orchestrator.route(objective)
    return StrategyRecommendationOutput.model_validate(
        {
            "route": [step.model_dump(mode="json") for step in route],
            "model_strategy": model_router.plan(objective, route, priority),
        }
    )

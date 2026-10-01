from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from nexus import __version__
from nexus.config import settings
from nexus.model_catalog import model_catalog
from nexus.model_router import model_router
from nexus.orchestrator import orchestrator
from nexus.registry import DOMAIN_CAPABILITIES, registry

# Public directory MCP surface: read-only planning, routing and model-strategy
# inspection. Stateful/write operations remain available through the protected
# REST control plane and are intentionally not exposed to marketplace users.
mcp = FastMCP(
    "NEXUS-100",
    instructions=(
        "NEXUS-100 is a read-only orchestration and adaptive model-strategy plugin. "
        "Use it to inspect the 100-agent capability map, preview a multi-domain plan, "
        "and recommend model/reasoning budgets. It does not deploy code, send messages, "
        "spend money, modify external systems, or execute consequential actions."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
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


@mcp.tool(
    annotations=_readonly("Get NEXUS system status"),
)
def get_system_status() -> dict:
    """Check public NEXUS-100 runtime capabilities and feature availability."""
    return {
        "status": "healthy",
        "version": __version__,
        "domains": len(DOMAIN_CAPABILITIES),
        "agents": len(registry.agents),
        "adaptive_model_routing": settings.model_routing_enabled,
        "backend_model_execution": settings.backend_model_execution_enabled,
        "model_catalog_size": len(model_catalog.snapshot()),
    }


@mcp.tool(
    annotations=_readonly("List NEXUS domains"),
)
def list_domains() -> dict:
    """List the 10 orchestration domains and their supported specialist capabilities."""
    return {"domains": DOMAIN_CAPABILITIES}


@mcp.tool(
    annotations=_readonly("Preview a NEXUS mission plan"),
)
def plan_mission(objective: str, priority: str = "normal") -> dict:
    """Preview which domains and specialist agents would handle a user objective.

    This is stateless and read-only. It does not create a tracked mission, call a
    model provider, or perform external actions.
    """
    return orchestrator.preview(objective, priority)


@mcp.tool(
    annotations=_readonly("List available model catalog"),
)
def list_model_catalog() -> dict:
    """List the cached model choices NEXUS can consider for adaptive routing.

    The response contains model capability metadata only and omits credentials,
    provider diagnostics, timestamps and internal request telemetry.
    """
    models = []
    for item in model_catalog.snapshot():
        models.append(
            {
                "id": item.id,
                "family": item.family,
                "quality": item.quality,
                "speed": item.speed,
                "cost_index": item.cost_index,
                "reasoning_efforts": list(item.reasoning_efforts),
                "specializations": list(item.specializations),
                "available": item.available,
            }
        )
    return {"count": len(models), "models": models}


@mcp.tool(
    annotations=_readonly("Recommend an adaptive model strategy"),
)
async def recommend_model_strategy(
    objective: str,
    priority: str = "normal",
) -> dict:
    """Recommend domains, agents, model IDs, reasoning effort and token budgets.

    NEXUS may refresh its configured provider's model catalog, but it does not send
    the user's objective to a model provider and does not run paid model inference.
    """
    await model_catalog.refresh()
    route = orchestrator.route(objective)
    return {
        "route": [step.model_dump(mode="json") for step in route],
        "model_strategy": model_router.plan(objective, route, priority),
    }

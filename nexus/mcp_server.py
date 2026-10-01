from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from nexus.memory import memory
from nexus.orchestrator import orchestrator
from nexus.registry import DOMAIN_CAPABILITIES, registry

# The MCP sub-application is mounted by FastAPI at /mcp. Serving the transport
# at "/" inside that sub-application keeps the public endpoint exactly /mcp/
# instead of producing /mcp/mcp.
mcp = FastMCP(
    "NEXUS-100",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    # NEXUS is deployed behind Cloud Run, whose managed ingress already
    # terminates TLS and controls Host routing. Disabling SDK-level DNS
    # rebinding checks here avoids rejecting the real Cloud Run hostname
    # while keeping the deployment architecture explicit.
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


@mcp.tool()
def get_system_status() -> dict:
    """Inspect NEXUS-100 health and registry counts. Read only."""
    return {
        "status": "healthy",
        "domains": len(DOMAIN_CAPABILITIES),
        "agents": len(registry.agents),
        "missions": len(memory.missions),
    }


@mcp.tool()
def list_domains() -> dict:
    """List domain orchestrators and capabilities. Read only."""
    return {"domains": DOMAIN_CAPABILITIES}


@mcp.tool()
def plan_mission(objective: str, priority: str = "normal") -> dict:
    """Plan a governed multi-domain mission without external side effects."""
    return orchestrator.plan(objective, priority).model_dump(mode="json")


@mcp.tool()
def run_mission(
    objective: str,
    priority: str = "normal",
    dry_run: bool = True,
) -> dict:
    """Create a tracked mission. External writes are not executed."""
    return orchestrator.start(objective, priority, dry_run).model_dump(mode="json")


@mcp.tool()
def get_mission(mission_id: str) -> dict:
    """Get a tracked mission by ID."""
    mission = memory.missions.get(mission_id)
    return (
        mission.model_dump(mode="json")
        if mission
        else {"error": "mission_not_found"}
    )


@mcp.tool()
def request_sensitive_action(
    action: str,
    reason: str,
    mission_id: str | None = None,
    risk: str = "high",
) -> dict:
    """Create an approval request; never execute the consequential action."""
    from uuid import UUID

    from nexus.models import Risk

    mid = UUID(mission_id) if mission_id else None
    return orchestrator.approval(
        action,
        reason,
        mid,
        Risk(risk),
    ).model_dump(mode="json")

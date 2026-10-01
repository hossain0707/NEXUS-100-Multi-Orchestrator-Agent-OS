from typing import Literal

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nexus import __version__
from nexus.api import router
from nexus.config import settings
from nexus.mcp_server import mcp
from nexus.model_catalog import model_catalog
from nexus.model_router import model_router
from nexus.orchestrator import orchestrator
from nexus.persistence import init_db
from nexus.registry import DOMAIN_CAPABILITIES, registry
from nexus.security import SecurityMiddleware

DASHBOARD_ORIGINS = [
    "https://hossain0707.github.io",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


class StrategyPreviewIn(BaseModel):
    objective: str = Field(min_length=3, max_length=2000)
    priority: Literal["low", "normal", "high", "critical"] = "normal"


# Build the mounted MCP application once. This initializes its session manager
# before the parent FastAPI lifespan starts.
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await model_catalog.refresh()
    # Mounted ASGI sub-app lifespans are not run by Starlette, so the parent
    # application owns the MCP session-manager lifecycle.
    async with mcp.session_manager.run():
        yield


app = FastAPI(
    title="NEXUS-100 AI Agent OS",
    version=__version__,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=DASHBOARD_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "nexus-100-agent-os",
        "version": __version__,
    }


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/.well-known/openai-apps-challenge", response_class=PlainTextResponse)
async def openai_apps_challenge():
    """Serve the exact OpenAI directory domain-verification token when configured."""
    if not settings.openai_apps_challenge:
        return PlainTextResponse("", status_code=404)
    return PlainTextResponse(settings.openai_apps_challenge)


@app.get("/status")
async def public_status():
    """Safe public runtime status for the GitHub Pages architecture dashboard."""
    snapshot = model_catalog.public_snapshot()
    return {
        "status": "healthy",
        "version": __version__,
        "domains": len(DOMAIN_CAPABILITIES),
        "agents": len(registry.agents),
        "adaptive_model_routing": settings.model_routing_enabled,
        "backend_model_execution": settings.backend_model_execution_enabled,
        "model_catalog_size": snapshot["count"],
        "catalog_last_refresh": snapshot["last_refresh"],
        "catalog_discovery_enabled": snapshot["discovery_enabled"],
    }


@app.post("/demo/strategy")
async def public_strategy_preview(body: StrategyPreviewIn):
    """Read-only strategy preview. It never performs paid model inference."""
    route = orchestrator.route(body.objective)
    return {
        "route": [step.model_dump(mode="json") for step in route],
        "model_strategy": model_router.plan(
            body.objective,
            route,
            body.priority,
        ),
    }


# Keep this catch-all mount after the REST, health and public dashboard routes.
# The inner MCP transport serves at "/", yielding the public endpoint /mcp/.
app.mount("/mcp", mcp_app)

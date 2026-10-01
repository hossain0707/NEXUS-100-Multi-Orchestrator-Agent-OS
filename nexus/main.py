from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexus import __version__
from nexus.api import router
from nexus.mcp_server import mcp
from nexus.persistence import init_db
from nexus.security import SecurityMiddleware

# Build the mounted MCP application once. This initializes its session manager
# before the parent FastAPI lifespan starts.
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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


# Keep this catch-all mount after the REST and health routes. The inner MCP
# transport serves at "/", yielding the public Streamable HTTP endpoint /mcp/.
app.mount("/mcp", mcp_app)

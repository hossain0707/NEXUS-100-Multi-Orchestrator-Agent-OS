from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexus import __version__
from nexus.api import router
from nexus.mcp_server import mcp
from nexus.persistence import init_db
from nexus.security import SecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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

# FastMCP's Streamable HTTP ASGI app serves its protocol at its own /mcp
# path. Mount it at the application root so the public endpoint is /mcp,
# rather than accidentally nesting it as /mcp/mcp.
app.mount("/", mcp.streamable_http_app())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexus-100-agent-os", "version": __version__}


@app.get("/ready")
async def ready():
    return {"status": "ready"}

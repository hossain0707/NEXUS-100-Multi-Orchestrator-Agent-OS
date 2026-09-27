from contextlib import asynccontextmanager
from fastapi import FastAPI
from nexus import __version__
from nexus.api import router
from nexus.mcp_server import mcp
from nexus.security import SecurityMiddleware

@asynccontextmanager
async def lifespan(app:FastAPI):
    async with mcp.session_manager.run(): yield

app=FastAPI(
    title="NEXUS-100 AI Agent OS",
    version=__version__,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(SecurityMiddleware)
app.include_router(router)
app.mount("/mcp",mcp.streamable_http_app())

@app.get("/health")
async def health():
    return {"status":"ok","service":"nexus-100-agent-os","version":__version__}

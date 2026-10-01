import hmac
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from nexus.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Deployment boundary for control-plane and MCP requests.

    The REST control plane uses NEXUS_API_TOKEN when configured (and production
    startup already requires that token). The public directory MCP endpoint is
    intentionally independent: set NEXUS_MCP_API_TOKEN only for a private MCP
    deployment. This prevents enabling REST authentication from accidentally
    making the public read-only plugin unreachable.
    """

    @staticmethod
    def _authorized(request, token: str) -> bool:
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {token}"
        return hmac.compare_digest(supplied, expected)

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        length = request.headers.get("content-length")
        if length:
            try:
                content_length = int(length)
            except ValueError:
                return JSONResponse(
                    {"error": "invalid_content_length", "request_id": request_id},
                    status_code=400,
                )
            if content_length < 0:
                return JSONResponse(
                    {"error": "invalid_content_length", "request_id": request_id},
                    status_code=400,
                )
            if content_length > 1_000_000:
                return JSONResponse(
                    {"error": "payload_too_large", "request_id": request_id},
                    status_code=413,
                )

        path = request.url.path
        token = None
        if path.startswith("/api/"):
            token = settings.api_token
        elif path.startswith("/mcp"):
            token = settings.mcp_api_token

        if token and not self._authorized(request, token):
            return JSONResponse(
                {"error": "unauthorized", "request_id": request_id},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

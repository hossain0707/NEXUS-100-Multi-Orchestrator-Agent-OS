import hmac
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from nexus.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Minimal deployment boundary: bearer auth when configured, request IDs, body limits."""

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        length = request.headers.get("content-length")
        if length and int(length) > 1_000_000:
            return JSONResponse({"error": "payload_too_large"}, status_code=413)

        protected = request.url.path.startswith(("/api/", "/mcp"))
        if protected and settings.api_token:
            supplied = request.headers.get("authorization", "")
            expected = f"Bearer {settings.api_token}"
            if not hmac.compare_digest(supplied, expected):
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

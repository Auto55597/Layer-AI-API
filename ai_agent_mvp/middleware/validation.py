"""
Validation Guard Middleware
- Enforces request body size limits
- Provides early DoS protection
- Supports demo / trial clients
- Designed to be safe and non-intrusive
"""

import os
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

# -------------------------
# CONFIG
# -------------------------

# Production limit: 10 MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

# Demo limit: 1 MB
DEMO_MAX_CONTENT_LENGTH = 1 * 1024 * 1024

# Enable demo mode via env
DEMO_MODE_ENABLED = os.getenv("DEMO_MODE", "true").lower() == "true"

# Header used to mark demo clients
DEMO_HEADER = "x-demo-client"


class ContentSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Reject requests with body size exceeding allowed limits.
        Uses Content-Length header for fast-fail protection.
        """

        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "INVALID_CONTENT_LENGTH",
                        "message": "Invalid Content-Length header"
                    }
                )

            # Determine limit
            limit = MAX_CONTENT_LENGTH
            client_type = "production"

            if DEMO_MODE_ENABLED and request.headers.get(DEMO_HEADER) == "true":
                limit = DEMO_MAX_CONTENT_LENGTH
                client_type = "demo"

            if length > limit:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "PAYLOAD_TOO_LARGE",
                        "message": f"Request body exceeds limit for {client_type} client",
                        "limit_bytes": limit
                    }
                )

        # IMPORTANT:
        # We do NOT read the request body here.
        # This middleware is intentionally a guard only.
        return await call_next(request)

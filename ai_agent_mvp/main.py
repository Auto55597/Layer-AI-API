print("RUNNING FILE:", __file__)

"""
FastAPI Main Application
AI Agent Permission & Audit Layer API

Key Components:
- Agent Control: Permissions, Kill Switches (System/Agent), Audits
- SaaS Layer: Customer Management, API Keys, Subscription Tiers
- Admin Interface: Internal management of Agents and Permissions
"""
import os
import uvicorn

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import init_db
from routers import agent, logs, permissions, admin, customers
from config import (
    API_TITLE, API_DESCRIPTION, API_VERSION, API_DOCS_URL,
    CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS,
    RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
)
from exceptions import APIException
from logger_config import get_logger

# Middleware Imports (MVP-safe only)
from middleware.audit import AuditMiddleware
from middleware.validation import ContentSizeLimitMiddleware

logger = get_logger("main")

# -------------------------
# APP
# -------------------------
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=API_DOCS_URL,
)

# -------------------------
# RATE LIMIT
# -------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW}s"]
    if RATE_LIMIT_ENABLED else []
)
app.state.limiter = limiter

# -------------------------
# MIDDLEWARE
# Order: Last added runs FIRST (request)
# -------------------------

# 1. Content Size Limit (DoS Guard)
app.add_middleware(ContentSizeLimitMiddleware)

# 2. Audit Logging (Trace + Latency)
app.add_middleware(AuditMiddleware)

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

# -------------------------
# API ROUTERS
# -------------------------
app.include_router(agent.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(permissions.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(customers.router, prefix="/api")

# -------------------------
# EXCEPTIONS
# -------------------------
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.detail,
            "path": str(request.url.path),
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "details": exc.errors(),
        },
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "RATE_LIMIT_EXCEEDED"},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_SERVER_ERROR"},
    )

# -------------------------
# SYSTEM
# -------------------------
@app.on_event("startup")
def on_startup():
    logger.info("Starting system")
    init_db()

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Shutting down system")

# -------------------------
# HEALTH / META
# -------------------------
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
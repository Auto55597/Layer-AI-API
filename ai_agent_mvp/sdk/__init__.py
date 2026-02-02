"""
AI Agent SDK
Production-grade Python SDK for AI Agent Permission & Audit Layer.

Public API Surface (v1)
-----------------------
This module intentionally exposes only stable, supported interfaces.
Internal modules and helpers are NOT part of the public contract.
"""

# ======================
# TEMPORARY PUBLIC API
# ======================
# ตอนนี้เปิดแค่ส่วนที่ใช้จริงในการทดสอบ permission
from .agent_guard import AgentGuard


# ======================
# FUTURE / PLANNED API
# (ยังไม่เปิดใช้)
# ======================

# Core configuration & client
# from .config import AgentConfig
# from .client import AgentClient

# High-level helpers
# from .policy import PolicyManager, PolicyDecision
# from .actions import ActionRunner

# Models
# from .models import (
#     AgentRequest,
#     AgentResponse,
# )

# Error hierarchy (explicit, typed)
# from .errors import (
#     SDKError,
#     AuthenticationError,
#     ValidationError,
#     RateLimitError,
#     ConnectionError,
#     ServerError,
# )

__all__ = [
    # Exposed now
    "AgentGuard",

    # Planned (not exposed yet)
    # "AgentConfig",
    # "AgentClient",
    # "PolicyManager",
    # "PolicyDecision",
    # "ActionRunner",
    # "AgentRequest",
    # "AgentResponse",
    # "SDKError",
    # "AuthenticationError",
    # "ValidationError",
    # "RateLimitError",
    # "ConnectionError",
    # "ServerError",
]

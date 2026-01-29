"""
AI Agent SDK
Production-grade Python SDK for AI Agent Permission & Audit Layer.

Public API Surface (v1)
-----------------------
This module intentionally exposes only stable, supported interfaces.
Internal modules and helpers are NOT part of the public contract.
"""

# Core configuration & client
from .config import AgentConfig
from .client import AgentClient

# High-level helpers
from .policy import PolicyManager, PolicyDecision
from .actions import ActionRunner

# Models
from .models import (
    AgentRequest,
    AgentResponse,
)

# Error hierarchy (explicit, typed)
from .errors import (
    SDKError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    ConnectionError,
    ServerError,
)

__all__ = [
    # Core
    "AgentConfig",
    "AgentClient",

    # High-level API
    "PolicyManager",
    "PolicyDecision",
    "ActionRunner",

    # Models
    "AgentRequest",
    "AgentResponse",

    # Errors
    "SDKError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "ConnectionError",
    "ServerError",
]

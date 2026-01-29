"""
Configuration Module
Centralized configuration for the application
"""
import os
from pathlib import Path
from typing import List

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Database
DATABASE_DIR = Path(__file__).parent
DATABASE_FILE = DATABASE_DIR / "agent_audit.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
# Use absolute path for production
if not DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = f"sqlite:///{DATABASE_FILE.absolute()}"

# API Configuration
API_TITLE = "AI Agent Permission & Audit Layer"
API_DESCRIPTION = "Permission management and audit system for AI Agents"
API_VERSION = "1.0.0"
API_DOCS_URL = "/docs" if DEBUG else None

# CORS Configuration (restrict to specific origins in production)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
if not DEBUG:
    # In production, only allow specific origins
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]
else:
    # In development, allow localhost
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]

CORS_CREDENTIALS = True
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS = ["*"]

# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = DATABASE_DIR / "logs" / "app.log"

# Create logs directory if it doesn't exist
LOG_FILE.parent.mkdir(exist_ok=True)

# Security
API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "true").lower() == "true"
ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"}

# ============================================
# SaaS Pricing Tiers Configuration
# ============================================

PRICING_TIERS = {
    "free": {
        "name": "Free",
        "price_per_month": 0,
        "max_agents": 5,
        "max_requests_per_minute": 10,
        "max_api_keys": 1,
        "features": [
            "Up to 5 agents",
            "Basic analytics",
            "Email support",
            "Limited API calls",
        ],
    },
    "starter": {
        "name": "Starter",
        "price_per_month": 99,
        "max_agents": 50,
        "max_requests_per_minute": 100,
        "max_api_keys": 5,
        "features": [
            "Up to 50 agents",
            "Advanced analytics",
            "Priority email support",
            "100 requests/minute",
            "API documentation",
        ],
    },
    "pro": {
        "name": "Pro",
        "price_per_month": 499,
        "max_agents": 500,
        "max_requests_per_minute": 1000,
        "max_api_keys": 20,
        "features": [
            "Up to 500 agents",
            "Real-time analytics",
            "Phone & email support",
            "1000 requests/minute",
            "Webhook support",
            "Custom integrations",
            "SLA guarantee",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_per_month": "Custom",
        "max_agents": 5000,
        "max_requests_per_minute": 10000,
        "max_api_keys": 100,
        "features": [
            "Unlimited agents",
            "Real-time analytics",
            "Dedicated support",
            "Unlimited API calls",
            "Custom workflows",
            "On-premise option",
            "99.99% SLA",
            "Custom training",
        ],
    },
}
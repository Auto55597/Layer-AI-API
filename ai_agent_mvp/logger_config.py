"""
Logging Configuration
Centralized logging setup for the application
"""
import logging
import logging.handlers
from pathlib import Path
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, DEBUG

# Create logger
logger = logging.getLogger("ai_agent_api")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Create formatter
formatter = logging.Formatter(LOG_FORMAT)

# File handler
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler (in development)
if DEBUG:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Prevent propagation to root logger
logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module"""
    return logging.getLogger(f"ai_agent_api.{name}")

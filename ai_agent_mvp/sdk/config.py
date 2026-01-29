"""
SDK Configuration
"""
from dataclasses import dataclass
from typing import Optional
import logging

@dataclass
class AgentConfig:
    """
    Configuration for AI Agent SDK
    """
    base_url: str = "http://localhost:8000"
    api_key: str = ""
    timeout: float = 30.0
    retries: int = 3
    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        # Validate base_url
        if not self.base_url:
            raise ValueError("base_url is required")
        self.base_url = self.base_url.rstrip("/")
        
        # Validate api_key
        if not self.api_key:
            raise ValueError("api_key is required")
            
        # Set default logger if not provided
        if self.logger is None:
            self.logger = logging.getLogger("ai_agent_sdk")
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

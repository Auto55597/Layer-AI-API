"""
Authentication and Authorization Module
Handles API key validation and permission checks
"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

# API Key Configuration
# In production, load from environment variables or secret manager
DEFAULT_API_KEYS = {
    "dev-key-12345": "Development",
    "prod-key-67890": "Production"
}

# Load API keys from environment or use defaults
VALID_API_KEYS = {
    os.getenv("API_KEY_DEV", "dev-key-12345"): "Development",
    os.getenv("API_KEY_PROD", "prod-key-67890"): "Production"
}

security = HTTPBearer()


class APIKeyManager:
    """Manages API key validation and rotation"""
    
    @staticmethod
    def validate_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """
        Validate API key from request headers
        
        Args:
            credentials: HTTPAuthorizationCredentials from Authorization header
            
        Returns:
            str: Environment type (Development/Production)
            
        Raises:
            HTTPException: 403 Forbidden if API key is invalid
        """
        api_key = credentials.credentials
        
        if api_key not in VALID_API_KEYS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API key"
            )
        
        return VALID_API_KEYS[api_key]
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure random API key"""
        return f"key_{secrets.token_urlsafe(32)}"


# Dependency for endpoints that require authentication
require_api_key = APIKeyManager.validate_api_key

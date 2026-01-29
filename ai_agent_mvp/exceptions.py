"""
Custom Exception Classes for API
Provides standardized error responses
"""
from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class APIException(HTTPException):
    """Base exception for API errors"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code or "INTERNAL_ERROR"
        self.detail = detail
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationException(APIException):
    """Raised when input validation fails"""
    
    def __init__(self, detail: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code
        )


class PermissionException(APIException):
    """Raised when permission is denied"""
    
    def __init__(self, detail: str = "Permission denied", error_code: str = "PERMISSION_DENIED"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code
        )


class AuthenticationException(APIException):
    """Raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTH_FAILED"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers={"WWW-Authenticate": "Bearer"}
        )


class NotFoundException(APIException):
    """Raised when resource not found"""
    
    def __init__(self, resource: str = "Resource", error_code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
            error_code=error_code
        )


class ConflictException(APIException):
    """Raised when there's a conflict (e.g., duplicate record)"""
    
    def __init__(self, detail: str, error_code: str = "CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code
        )


class SystemException(APIException):
    """Raised for system-level errors"""
    
    def __init__(self, detail: str = "System error", error_code: str = "SYSTEM_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code
        )


class RateLimitException(APIException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded", error_code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
            headers={"Retry-After": "60"}
        )

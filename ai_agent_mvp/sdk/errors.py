"""
AI Agent SDK Exception Hierarchy
"""

from typing import Optional, List


class SDKError(Exception):
    """
    Base class for all SDK errors.
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ConfigurationError(SDKError):
    """
    Raised when SDK configuration is invalid or incomplete.
    """
    pass


class AuthenticationError(SDKError):
    """
    Raised when API authentication or authorization fails (401 / 403).
    """
    pass


class ValidationError(SDKError):
    """
    Raised when request data is invalid (400 / 422).
    """
    def __init__(
        self,
        message: str,
        details: Optional[List[dict]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error=original_error)
        self.details = details


class RateLimitError(SDKError):
    """
    Raised when API rate limit is exceeded (429).
    """
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, original_error=original_error)
        self.retry_after = retry_after


class SDKConnectionError(SDKError):
    """
    Raised when connection to API fails or times out.
    """
    pass


class ServerError(SDKError):
    """
    Raised when API returns a server-side error (5xx).
    """
    pass

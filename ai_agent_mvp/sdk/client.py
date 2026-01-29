"""
Core SDK Client
"""
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Optional, Any, Dict, Type, TypeVar

from .config import AgentConfig
from .errors import (
    SDKError, AuthenticationError, ValidationError, 
    RateLimitError, ConnectionError, ServerError
)
from .models import BaseModel

T = TypeVar("T", bound=BaseModel)

class AgentClient:
    """
    Main entry point for AI Agent SDK interactions.
    Handles HTTP transport, authentication, and error mapping.
    """
    def __init__(self, config: AgentConfig):
        self.config = config
        self.session = self._create_session()
        self.logger = config.logger

    def _create_session(self) -> requests.Session:
        """Create a configured requests Session with retries"""
        session = requests.Session()
        
        # Add API Key Header
        session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ai-agent-sdk-python/1.0.0"
        })
        
        # Configure Retries
        if self.config.retries > 0:
            retry_strategy = Retry(
                total=self.config.retries,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            
        return session

    def request(self, method: str, endpoint: str, model: Type[T] = None, **kwargs) -> T:
        """
        Execute an HTTP request and map errors.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            model: Optional Pydantic model to parse response into
            **kwargs: Arguments passed to requests.request
            
        Returns:
            Parsed Pydantic model or raw JSON dict
        """
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        try:
            self.logger.debug(f"Request: {method} {url}")
            response = self.session.request(
                method=method, 
                url=url, 
                timeout=self.config.timeout, 
                **kwargs
            )
            
            # Raise for status to trigger error handling logic
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                self._handle_error_response(response)
            
            # Success
            data = response.json()
            if model:
                return model.model_validate(data)
            return data
            
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}", original_error=e)
        except requests.exceptions.Timeout as e:
            raise ConnectionError(f"Request timed out after {self.config.timeout}s", original_error=e)
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                # Already handled in inner try/except, but if it bubbled up:
                pass 
            raise SDKError(f"Unexpected request error: {str(e)}", original_error=e)

    def _handle_error_response(self, response: requests.Response):
        """Map HTTP status codes to SDK exceptions"""
        status = response.status_code
        try:
            error_body = response.json()
            message = error_body.get("message", response.text)
            details = error_body.get("details", None)
        except ValueError:
            message = response.text
            details = None

        if status == 401:
            raise AuthenticationError(f"Authentication failed: {message}")
        elif status == 403:
            raise AuthenticationError(f"Permission denied: {message}")
        elif status == 400:
            raise ValidationError(f"Bad Request: {message}", details=details)
        elif status == 422:
            raise ValidationError(f"Validation Error: {message}", details=details)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(f"Rate limit exceeded: {message}", retry_after=retry_after)
        elif 500 <= status < 600:
            raise ServerError(f"Server Error {status}: {message}")
        else:
            raise SDKError(f"HTTP {status}: {message}")

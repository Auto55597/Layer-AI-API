"""
Audit Middleware
- Generates X-Trace-ID for request tracking
- Logs request access and response status
- Calculates latency
- Redacts sensitive headers
"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from logger_config import get_logger

logger = get_logger("audit")

SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie", "set-cookie"}

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate Trace ID
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        
        # 2. Start Timer
        start_time = time.time()
        
        # 3. Prepare Context for Logging
        # (Ideally, we would set this in a contextvar for the logger, but for now we pass it in log messages)
        client_host = request.client.host if request.client else "unknown"
        
        # 4. Log Request (Redacted)
        # We don't log body here to avoid consuming stream
        self.log_request(request, trace_id, client_host)
        
        try:
            # 5. Process Request
            response = await call_next(request)
            
            # 6. Add Trace ID to Response
            response.headers["X-Trace-ID"] = trace_id
            
            # 7. Log Response
            process_time = (time.time() - start_time) * 1000  # ms
            self.log_response(response, trace_id, start_time, process_time)
            
            return response
            
        except Exception as e:
            # Log error with trace ID before raising
            process_time = (time.time() - start_time) * 1000
            logger.error(f"Request failed: trace_id={trace_id} error={str(e)} latency={process_time:.2f}ms")
            raise e

    def log_request(self, request: Request, trace_id: str, client_host: str):
        """Log incoming request metadata"""
        safe_headers = {
            k: v for k, v in request.headers.items() 
            if k.lower() not in SENSITIVE_HEADERS
        }
        logger.info(
            f"REQUEST_START: trace_id={trace_id} method={request.method} "
            f"path={request.url.path} client={client_host} "
            f"user_agent={request.headers.get('user-agent', 'unknown')}"
        )

    def log_response(self, response, trace_id: str, start_time: float, process_time: float):
        """Log response metadata"""
        logger.info(
            f"REQUEST_END: trace_id={trace_id} status={response.status_code} "
            f"latency={process_time:.2f}ms"
        )

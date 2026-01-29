# Production Layers Documentation

This document describes the production-readiness layers added to the AI Agent MVP. These layers are implemented as middleware to ensure that the core business logic remains untouched while enhancing security, observability, and stability.

## Architecture

The following middleware layers have been added, wrapping the main application logic:

1.  **Security Middleware** (Outermost)
2.  **Validation Middleware** (Guard)
3.  **Audit Middleware** (Log & Trace)
4.  **Application Logic** (Router/Business Logic)

## Layers Description

### 1. Security Headers (`middleware/security.py`)
**Responsibility**: Hardens the HTTP response against common web vulnerabilities.
**Changes**:
- Adds strictly defined headers to *every* response.
- Headers added:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY` (Prevent clickjacking)
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security` (HSTS)
  - `Content-Security-Policy: default-src 'self'`

### 2. Validation Guard (`middleware/validation.py`)
**Responsibility**: Protects the system from Denial-of-Service (DoS) and oversized payloads.
**Changes**:
- Enforces a **10MB** limit on request bodies (`MAX_CONTENT_LENGTH`).
- Rejects requests exceeding this limit with `413 Payload Too Large`.
- Checks `Content-Length` header for fast rejection.

### 3. Audit Logging (`middleware/audit.py`)
**Responsibility**: Provides visibility into every request and ensures traceability.
**Changes**:
- **Trace ID**: Generates a unique `X-Trace-ID` for every request (or propagates one if provided).
- **Structured Logging**: Logs `REQUEST_START` and `REQUEST_END` events.
- **Latency Tracking**: Calculates and logs processing time in milliseconds.
- **Data Redaction**: Automatically scrubs sensitive headers (Authorization, API Keys, Cookies) from logs.

## Middleware Order

The order in `main.py` is critical for correct operation:

```python
# 1. Security Headers (Runs First on Request, Last on Response)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Content Size Limit (Runs Second)
app.add_middleware(ContentSizeLimitMiddleware)

# 3. Audit Logging (Runs Third - captures application behavior)
app.add_middleware(AuditMiddleware)
```

## Monitoring & Operations

- **Logs**: Check standard application logs. Look for `trace_id` to correlate request/response pairs.
- **Alerting**: Monitor for `413` errors (potential DoS attack) or high latency in `REQUEST_END` logs.

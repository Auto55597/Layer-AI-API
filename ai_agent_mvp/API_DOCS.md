# API Documentation - AI Agent Permission & Audit Layer

## Overview
The AI Agent Permission & Audit Layer is a comprehensive system for managing permissions and auditing actions of AI agents. It provides permission-based access control, kill switches for emergency shutdown, and detailed audit logging.

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints (except `/` and `/health`) require an API key in the Authorization header:

```bash
Authorization: Bearer <API_KEY>
```

Default API keys:
- Development: `dev-key-12345`
- Production: `prod-key-67890`

## Endpoints

### Health Check

#### GET /health
Returns API status and version information.

**Response:**
```json
{
    "message": "AI Agent Permission & Audit Layer API",
    "version": "1.0.0",
    "docs": "/docs"
}
```

#### GET /health
Returns health status.

**Response:**
```json
{
    "status": "healthy"
}
```

---

### Agent Requests

#### POST /api/agent/request
Check if an agent has permission to perform an action on a resource.

**Request Body:**
```json
{
    "agent_id": "string",
    "action": "string",
    "resource": "string"
}
```

**Parameters:**
- `agent_id` (required): Unique identifier of the agent
- `action` (required): Action to perform (e.g., "read", "write", "delete")
- `resource` (required): Resource to access (e.g., "database", "api", "file")

**Response (Success):**
```json
{
    "result": "approved",
    "message": "Permission granted for read on database",
    "reason": "all_checks_passed",
    "decision_trace": [
        {
            "rule_checked": "kill_switch",
            "rule_result": "passed",
            "notes": "kill switch off"
        },
        {
            "rule_checked": "agent_status",
            "rule_result": "passed",
            "notes": "agent active"
        },
        {
            "rule_checked": "permission_rule",
            "rule_result": "passed",
            "notes": "permission granted for read on database"
        }
    ],
    "action_required": null
}
```

**Response (Denied):**
```json
{
    "result": "denied",
    "message": "No permission for write on database",
    "reason": "permission_rule_failed",
    "decision_trace": [
        {
            "rule_checked": "kill_switch",
            "rule_result": "passed",
            "notes": "kill switch off"
        },
        {
            "rule_checked": "agent_status",
            "rule_result": "passed",
            "notes": "agent active"
        },
        {
            "rule_checked": "permission_rule",
            "rule_result": "failed",
            "notes": "no permission for write on database"
        }
    ],
    "action_required": null
}
```

---

#### POST /api/agent/kill
Enable or disable an agent (only owner can perform this action).

**Request Body:**
```json
{
    "agent_id": "string",
    "owner": "string",
    "enabled": boolean
}
```

**Parameters:**
- `agent_id` (required): Unique identifier of the agent
- `owner` (required): Owner ID (must match agent's owner)
- `enabled` (required): true to enable, false to disable

**Response:**
```json
{
    "result": "disabled",
    "message": "Agent test-agent has been disabled by owner owner1"
}
```

---

### System Kill Switch

#### GET /api/agent/system-kill-switch
Get current status of the system-wide kill switch.

**Response:**
```json
{
    "status": "disabled",
    "message": "System kill switch is disabled. All agent requests are processed normally."
}
```

#### POST /api/agent/system-kill-switch
Enable or disable the system-wide kill switch (blocks all agent requests).

**Request Body:**
```json
{
    "enabled": boolean
}
```

**Response:**
```json
{
    "status": "enabled",
    "message": "System kill switch has been enabled. All agent requests will be denied."
}
```

---

### Logs

#### GET /api/logs
Query audit logs with optional filtering.

**Query Parameters:**
- `agent_id` (optional): Filter by agent ID
- `start_time` (optional): Filter by start time (ISO format: YYYY-MM-DDTHH:MM:SS)
- `end_time` (optional): Filter by end time (ISO format: YYYY-MM-DDTHH:MM:SS)

**Examples:**
```bash
GET /logs
GET /logs?agent_id=test-agent
GET /logs?agent_id=test-agent&start_time=2024-01-01T00:00:00&end_time=2024-01-02T00:00:00
```

**Response:**
```json
[
    {
        "id": "log-001",
        "agent_id": "test-agent",
        "action": "read",
        "resource": "database",
        "result": "approved",
        "timestamp": "2024-01-01T12:00:00"
    }
]
```

---

### Permissions

#### GET /api/permissions
Get all permissions for a specific agent.

**Query Parameters:**
- `agent_id` (required): Filter by agent ID

**Example:**
```bash
GET /permissions?agent_id=test-agent
```

**Response:**
```json
[
    {
        "id": "perm-001",
        "agent_id": "test-agent",
        "action": "read",
        "resource": "database",
        "condition": null
    },
    {
        "id": "perm-002",
        "agent_id": "test-agent",
        "action": "write",
        "resource": "cache",
        "condition": "time < 18:00"
    }
]
```

---

### Pending Approvals (Human-in-the-Loop)

#### GET /api/agent/pending-approvals
Get list of requests awaiting human review.

**Response:**
```json
[
    {
        "request_id": "req-001",
        "agent_id": "test-agent",
        "action": "write",
        "resource": "database",
        "reason": "system_kill_switch_enabled",
        "decision_trace": [...],
        "action_required": "human_intervention"
    }
]
```

#### POST /api/agent/approve
Human approves a pending request.

**Request Body:**
```json
{
    "request_id": "string",
    "human_id": "string",
    "notes": "string (optional)"
}
```

**Response:**
```json
{
    "result": "approved",
    "reason": "human_override",
    "decision_trace": [...],
    "action_required": null
}
```

#### POST /api/agent/deny
Human denies a pending request.

**Request Body:**
```json
{
    "request_id": "string",
    "human_id": "string",
    "notes": "string (optional)"
}
```

**Response:**
```json
{
    "result": "denied",
    "reason": "human_override",
    "decision_trace": [...],
    "action_required": null
}
```

---

## Error Handling

### Error Response Format
```json
{
    "error": "ERROR_CODE",
    "message": "Error description",
    "path": "/endpoint/path"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid request data (400)
- `PERMISSION_DENIED`: Insufficient permissions (403)
- `AUTH_FAILED`: Authentication failed (401)
- `NOT_FOUND`: Resource not found (404)
- `RATE_LIMIT_EXCEEDED`: Too many requests (429)
- `INTERNAL_SERVER_ERROR`: Server error (500)

---

## Rate Limiting
Default: 100 requests per 60 seconds per IP address

When rate limit is exceeded:
```json
{
    "error": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "path": "/endpoint/path"
}
```

---

## Running the Application

### Development
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Production
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running Tests
```bash
pip install pytest
pytest tests/ -v
```

---

## Configuration

Environment variables:
- `ENVIRONMENT`: "development" or "production" (default: "development")
- `API_KEY_DEV`: Development API key
- `API_KEY_PROD`: Production API key
- `CORS_ORIGINS`: Comma-separated CORS origins
- `RATE_LIMIT_ENABLED`: "true" or "false" (default: "true")
- `RATE_LIMIT_REQUESTS`: Requests per window (default: 100)
- `RATE_LIMIT_WINDOW`: Time window in seconds (default: 60)
- `LOG_LEVEL`: "DEBUG", "INFO", "WARNING", "ERROR" (default: "INFO")

---

## Database
SQLite database stored at: `agent_audit.db`

Tables:
- `agents`: Agent information and status
- `permissions`: Permission rules
- `logs`: Audit log entries
- `system_state`: System-wide settings (kill switch)
- `pending_requests`: Human-in-the-loop requests

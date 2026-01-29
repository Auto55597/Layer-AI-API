# AI Agent Permission & Audit Layer

A comprehensive API system for managing permissions and auditing actions of AI agents. Provides permission-based access control, kill switches for emergency shutdown, and detailed audit logging.

## Features

✅ **Permission Management** - Fine-grained control over agent actions
✅ **Audit Logging** - Complete audit trail of all actions
✅ **Kill Switches** - Emergency shutdown for individual agents or system-wide
✅ **Human-in-the-Loop** - Pending approvals for sensitive actions
✅ **SaaS Ready** - Customer management, subscription tiers, and API key generation
✅ **Admin Interface** - Programmatic management of agents and permissions
✅ **API Key Authentication** - Secure API access with multi-tenant support
✅ **Input Validation** - Comprehensive validation of all inputs
✅ **Rate Limiting** - Prevent abuse and DDoS attacks (tier-based)
✅ **Production Ready** - Error handling, logging, and monitoring

## Quick Start

### Development

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables** (optional)
```bash
cp .env.example .env
```

3. **Start the Server**
```bash
uvicorn main:app --reload
```

API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Production

1. **Using Docker**
```bash
docker build -t ai-agent-api .
docker run -p 8000:8000 -e ENVIRONMENT=production ai-agent-api
```

2. **Using Docker Compose**
```bash
docker-compose up -d
```

3. **Direct Deployment**
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_api.py::TestHealthCheck::test_root_endpoint -v
```

## Configuration

See [.env.example](.env.example) for all available configuration options.

**Key Settings:**
- `ENVIRONMENT`: development or production
- `API_KEY_DEV`: Development API key (default: `dev-key-12345`)
- `API_KEY_PROD`: Production API key
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_REQUESTS`: Requests per window (default: 100)
- `RATE_LIMIT_WINDOW`: Time window in seconds (default: 60)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)

## API Documentation

Full API documentation is available in [API_DOCS.md](API_DOCS.md)

### Example Requests

**Check Agent Permission**
```bash
curl -X POST http://localhost:8000/api/agent/request \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "action": "read",
    "resource": "database"
  }'
```

**Get System Kill Switch Status**
```bash
curl http://localhost:8000/api/agent/system-kill-switch
```

**Get Audit Logs**
```bash
curl "http://localhost:8000/api/logs?agent_id=test-agent"
```

## Architecture

### Project Structure
```
ai_agent_mvp/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── database.py          # Database setup and session management
├── models.py            # SQLModel data models
├── auth.py              # Authentication and API key validation
├── exceptions.py        # Custom exception classes
├── logger_config.py     # Logging configuration
├── requirements.txt     # Python dependencies
├── routers/
│   ├── admin.py         # Admin management endpoints (Agents/Permissions)
│   ├── agent.py         # Agent request and kill switch endpoints
│   ├── customers.py     # SaaS customer and API key management
│   ├── logs.py          # Audit log endpoints
│   └── permissions.py   # Permission query endpoints
└── tests/
    └── test_api.py      # Unit tests
```

### Key Components

**Models** (SQLModel)
- `Agent` - AI agent information
- `Permission` - Permission rules
- `Log` - Audit log entries
- `SystemState` - System-wide settings
- `PendingRequest` - Human-in-the-loop requests
- `Customer` - SaaS tenant/user
- `APIKey` - Customer-specific API credentials

**Routers**
- `/agent` - Runtime checks, kill switches, and approvals
- `/admin` - Management interface for agents and permissions
- `/customers` - SaaS registration and subscription management
- `/logs` - Query audit logs
- `/permissions` - Query agent permissions

## Security

- **API Key Authentication**: All endpoints (except health checks) require API key
- **Input Validation**: Comprehensive validation using Pydantic
- **Rate Limiting**: Prevents abuse (default: 100 req/min per IP)
- **CORS**: Restricted to specific origins (configurable)
- **Logging**: All actions are audited and logged
- **Error Handling**: Standardized error responses

## Database

SQLite database (`agent_audit.db`) with the following tables:
- `agents` - Agent records
- `permissions` - Permission rules
- `logs` - Audit logs
- `system_state` - System settings
- `pending_requests` - Pending approvals
- `customers` - SaaS customer records
- `api_keys` - Hashed API keys

## Monitoring & Logging

Logs are written to:
- Console (development mode)
- File: `logs/app.log` (rotating, max 10MB per file, 5 backups)

Log levels: DEBUG, INFO, WARNING, ERROR

## Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Update `API_KEY_PROD`
- [ ] Configure `CORS_ORIGINS` for your frontend
- [ ] Set up external database (optional, currently uses SQLite)
- [ ] Configure rate limiting appropriately
- [ ] Set up monitoring and alerting
- [ ] Use HTTPS/TLS in production
- [ ] Set up proper backups for database
- [ ] Configure log rotation and archiving

## API Key Management

The system supports two modes of authentication:

### 1. Development / Static Mode
For local development and simple deployments, you can use static API keys defined in your `.env` file.

Default keys for development:
- **Dev**: `dev-key-12345` (set via `API_KEY_DEV`)
- **Prod**: `prod-key-67890` (set via `API_KEY_PROD`)

### 2. SaaS / Multi-Tenant Mode
For production SaaS deployment, use the Customer Management endpoints to generate unique API keys for each tenant.

**Workflow:**
1. **Register a Customer**:
   ```bash
   curl -X POST http://localhost:8000/api/customers/register \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Acme Corp",
       "email": "admin@acme.com",
       "subscription_tier": "starter"
     }'
   ```
   *Response includes the raw `api_key`.*

2. **Use the Generated Key**:
   ```bash
   curl -H "Authorization: Bearer sk-..." http://localhost:8000/api/agent/request ...
   ```

3. **Manage Keys**:
   - Generate additional keys: `POST /api/customers/{id}/api-keys/generate`
   - Revoke keys: `DELETE /api/customers/{id}/api-keys/{key_id}`

> **Note:** SaaS keys are hashed in the database (`api_keys` table) and cannot be retrieved after generation.

## Health Check

The API provides a health check endpoint:
```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please refer to the API_DOCS.md file or contact the development team.

## Changelog

### v1.0.0
- Initial release
- Permission management system
- Audit logging
- Kill switches (agent-level and system-wide)
- Human-in-the-loop approval system
- Complete API documentation
- Unit tests
- Docker support

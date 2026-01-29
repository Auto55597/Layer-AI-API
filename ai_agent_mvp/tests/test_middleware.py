"""
Middleware Tests
Verifies that the new production layers are working as expected.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from main import app

client = TestClient(app)


class TestSecurityHeaders:
    def test_security_headers_present(self):
        response = client.get("/health")
        assert response.status_code == 200

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Content-Security-Policy"] == "default-src 'self'"
        assert "server" not in response.headers


class TestAuditMiddleware:
    def test_trace_id_generated(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert response.headers["X-Trace-ID"]

    def test_trace_id_propagated(self):
        trace_id = "test-trace-123"
        response = client.get("/health", headers={"X-Trace-ID": trace_id})
        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == trace_id


class TestValidationMiddleware:
    @patch("middleware.validation.MAX_CONTENT_LENGTH", new=100)
    def test_payload_exceeding_limit_is_rejected(self):
        """
        Mock size limit to 100 bytes and verify middleware rejects larger payload.
        This avoids sending large payloads and makes the test deterministic.
        """
        large_body = "x" * 150

        response = client.post(
            "/agent/request",
            content=large_body,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 413
        body = response.json()
        assert body["error"] == "PAYLOAD_TOO_LARGE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

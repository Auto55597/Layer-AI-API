"""
Unit Tests for AI Agent Permission & Audit Layer
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime

import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from main import app
from database import get_session
from models import Agent, Permission, Log, SystemState
from routers.agent import check_system_kill_switch, check_permission, log_action

# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Test Cases
class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "AI Agent Permission & Audit Layer API"
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAgentPermissions:
    """Test agent permission checking"""
    
    def test_create_agent_and_check_permission(self, session: Session, client: TestClient):
        """Test creating agent and checking permissions"""
        # Create test agent
        agent = Agent(id="test-agent-1", name="Test Agent", owner="owner1", status="active")
        session.add(agent)
        session.commit()
        
        # Create permission
        permission = Permission(
            agent_id="test-agent-1",
            action="read",
            resource="database"
        )
        session.add(permission)
        session.commit()
        
        # Test check_permission
        assert check_permission(session, "test-agent-1", "read", "database") == True
        assert check_permission(session, "test-agent-1", "write", "database") == False
    
    def test_agent_request_with_permission(self, session: Session, client: TestClient):
        """Test agent request when permission exists"""
        # Setup
        agent = Agent(id="agent-1", name="Agent 1", owner="owner1", status="active")
        session.add(agent)
        session.commit()
        
        permission = Permission(
            agent_id="agent-1",
            action="read",
            resource="database"
        )
        session.add(permission)
        session.commit()
        
        # Test
        response = client.post("/agent/request", json={
            "agent_id": "agent-1",
            "action": "read",
            "resource": "database"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "approved"
    
    def test_agent_request_without_permission(self, session: Session, client: TestClient):
        """Test agent request when permission doesn't exist"""
        # Setup
        agent = Agent(id="agent-2", name="Agent 2", owner="owner2", status="active")
        session.add(agent)
        session.commit()
        
        # Test
        response = client.post("/agent/request", json={
            "agent_id": "agent-2",
            "action": "write",
            "resource": "database"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "denied"
        assert data["reason"] == "permission_rule_failed"


class TestKillSwitch:
    """Test kill switch functionality"""
    
    def test_check_system_kill_switch_default_off(self, session: Session):
        """Test kill switch defaults to OFF"""
        assert check_system_kill_switch(session) == False
    
    def test_agent_request_blocked_by_kill_switch(self, session: Session, client: TestClient):
        """Test agent request blocked when kill switch is enabled"""
        # Setup
        agent = Agent(id="agent-3", name="Agent 3", owner="owner3", status="active")
        permission = Permission(
            agent_id="agent-3",
            action="read",
            resource="database"
        )
        session.add(agent)
        session.add(permission)
        session.commit()
        
        # Enable kill switch
        from database import SYSTEM_KILL_SWITCH_KEY
        kill_switch = SystemState(
            key=SYSTEM_KILL_SWITCH_KEY,
            value="enabled",
            updated_at=datetime.utcnow()
        )
        session.add(kill_switch)
        session.commit()
        
        # Test
        response = client.post("/agent/request", json={
            "agent_id": "agent-3",
            "action": "read",
            "resource": "database"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "denied"
        assert data["reason"] == "system_kill_switch_enabled"


class TestAgentDisabled:
    """Test disabled agent handling"""
    
    def test_disabled_agent_request_denied(self, session: Session, client: TestClient):
        """Test request denied for disabled agent"""
        # Setup
        agent = Agent(id="agent-4", name="Agent 4", owner="owner4", status="disabled")
        permission = Permission(
            agent_id="agent-4",
            action="read",
            resource="database"
        )
        session.add(agent)
        session.add(permission)
        session.commit()
        
        # Test
        response = client.post("/agent/request", json={
            "agent_id": "agent-4",
            "action": "read",
            "resource": "database"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "denied"
        assert data["reason"] == "agent_disabled"


class TestInputValidation:
    """Test input validation"""
    
    def test_empty_agent_id_rejected(self, client: TestClient):
        """Test empty agent_id is rejected"""
        response = client.post("/agent/request", json={
            "agent_id": "",
            "action": "read",
            "resource": "database"
        })
        assert response.status_code == 422
    
    def test_long_string_rejected(self, client: TestClient):
        """Test overly long strings are rejected"""
        response = client.post("/agent/request", json={
            "agent_id": "a" * 300,  # Exceeds max_length of 255
            "action": "read",
            "resource": "database"
        })
        assert response.status_code == 422


class TestLogging:
    """Test audit logging"""
    
    def test_approved_action_logged(self, session: Session, client: TestClient):
        """Test approved action is logged"""
        # Setup
        agent = Agent(id="agent-5", name="Agent 5", owner="owner5", status="active")
        permission = Permission(
            agent_id="agent-5",
            action="read",
            resource="database"
        )
        session.add(agent)
        session.add(permission)
        session.commit()
        
        # Make request
        response = client.post("/agent/request", json={
            "agent_id": "agent-5",
            "action": "read",
            "resource": "database"
        })
        
        assert response.status_code == 200
        
        # Check log
        logs = session.query(Log).filter(Log.agent_id == "agent-5").all()
        assert len(logs) > 0
        assert logs[0].result == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

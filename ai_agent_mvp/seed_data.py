"""
Seed Data Script
Create test data for API testing
Run: python seed_data.py
"""
from sqlmodel import Session
from database import engine, init_db
from models import Agent, Permission
import uuid

def seed_data():
    """Create sample data"""
    
    # Create tables if they don't exist
    init_db()
    
    with Session(engine) as session:
        # Delete old data (optional)
        session.query(Permission).delete()
        session.query(Agent).delete()
        session.commit()
        
        print("🔄 Creating test data...")
        
        # Create Agents
        agents_data = [
            {
                "id": "agent-001",
                "name": "Data Processor",
                "owner": "alice@techcompany.com",
                "status": "active"
            },
            {
                "id": "agent-002",
                "name": "API Gateway",
                "owner": "bob@techcompany.com",
                "status": "active"
            },
            {
                "id": "agent-003",
                "name": "Analytics Engine",
                "owner": "charlie@techcompany.com",
                "status": "active"
            },
            {
                "id": "agent-004",
                "name": "Disabled Agent",
                "owner": "david@techcompany.com",
                "status": "disabled"
            }
        ]
        
        agents = []
        for data in agents_data:
            agent = Agent(**data)
            session.add(agent)
            agents.append(agent)
            print(f"  ✅ Created Agent: {data['id']}")
        
        session.commit()
        
        # Create Permissions
        permissions_data = [
            # Agent-001 permissions
            ("agent-001", "read", "database"),
            ("agent-001", "read", "cache"),
            ("agent-001", "write", "logs"),
            # Agent-002 permissions
            ("agent-002", "read", "api"),
            ("agent-002", "write", "database"),
            ("agent-002", "delete", "cache"),
            # Agent-003 permissions
            ("agent-003", "read", "database"),
            ("agent-003", "read", "api"),
            ("agent-003", "write", "analytics"),
            # Agent-004 (disabled) - still has permission but is disabled
            ("agent-004", "read", "database"),
        ]
        
        for agent_id, action, resource in permissions_data:
            permission = Permission(
                agent_id=agent_id,
                action=action,
                resource=resource
            )
            session.add(permission)
            print(f"  ✅ Created Permission: {agent_id} -> {action} on {resource}")
        
        session.commit()
        
        print("\n" + "="*50)
        print("✅ Test data created successfully!")
        print("="*50)
        print("\n📊 Data created:")
        print(f"  - Agents: {len(agents_data)}")
        print(f"  - Permissions: {len(permissions_data)}")
        print("\n🧪 Ready for testing!")
        print("\n💡 Example test cases:")
        print("  1. curl -X POST http://localhost:8000/agent/request \\")
        print("       -H 'Content-Type: application/json' \\")
        print("       -d '{\"agent_id\":\"agent-001\",\"action\":\"read\",\"resource\":\"database\"}'")
        print("\n  2. curl http://localhost:8000/logs")
        print("\n  3. pytest tests/ -v")


if __name__ == "__main__":
    seed_data()

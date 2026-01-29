"""
Database Setup and Session Management
Manage SQLite database connections and create tables automatically
"""
from sqlmodel import SQLModel, create_engine, Session, select
from typing import Generator
from datetime import datetime
from config import DATABASE_URL, DEBUG

# Create SQLite Database Engine
# SQLite stores data in agent_audit.db file (absolute path)
# echo=False for production, echo=True for development
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=DEBUG  # Only log SQL in development mode
)

# Key for System Kill Switch in SystemState table
SYSTEM_KILL_SWITCH_KEY = "system_kill_switch"


def init_db():
    """
    Function to create tables in database
    Called first time when application starts
    and initialize System Kill Switch to "disabled" (OFF) if not exists
    """
    SQLModel.metadata.create_all(engine)
    
    # Initialize System Kill Switch to "disabled" (OFF) if not exists
    with Session(engine) as session:
        from models import SystemState
        
        # Check if kill switch state already exists
        kill_switch = session.get(SystemState, SYSTEM_KILL_SWITCH_KEY)
        if not kill_switch:
            # Create new kill switch state as "disabled" (OFF)
            kill_switch = SystemState(
                key=SYSTEM_KILL_SWITCH_KEY,
                value="disabled",
                updated_at=datetime.utcnow()
            )
            session.add(kill_switch)
            session.commit()


def get_session() -> Generator[Session, None, None]:
    """
    Function to create Database Session
    Use Context Manager to manage session lifecycle
    """
    with Session(engine) as session:
        yield session

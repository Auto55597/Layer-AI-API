"""
API Router for Permissions Query
- GET /permissions: Retrieve Agent's Permissions
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from typing import List

import sys
import os
# Add parent directory to path to allow importing models and database modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import Permission, PermissionResponse, Agent
from database import get_session

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.get("/", response_model=List[PermissionResponse])
def get_permissions(
    agent_id: str = Query(..., description="Filter by agent_id (required)"),
    session: Session = Depends(get_session)
):
    """
    Retrieve permissions for a specific agent.

    This endpoint returns all access rules defined for the given agent.

    Args:
        agent_id (str): The unique identifier of the agent.

    Returns:
        List[PermissionResponse]: List of permission rules.

    Raises:
        HTTPException(404): If the agent does not exist.
    """
    # Check if Agent exists
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Find Agent's Permissions
    statement = select(Permission).where(Permission.agent_id == agent_id)
    permissions = session.exec(statement).all()
    
    return [
        PermissionResponse(
            id=perm.id,
            agent_id=perm.agent_id,
            action=perm.action,
            resource=perm.resource,
            condition=perm.condition
        )
        for perm in permissions
    ]

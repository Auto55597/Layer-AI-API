"""
API Router for Admin Operations
- POST /admin/agents: Create new Agent
- PUT /admin/agents/{agent_id}: Update Agent
- DELETE /admin/agents/{agent_id}: Delete Agent
- POST /admin/permissions: Create new Permission
- DELETE /admin/permissions/{permission_id}: Delete Permission
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional

import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import Agent, Permission
from database import get_session
from logger_config import get_logger

logger = get_logger("admin_router")
router = APIRouter(prefix="/admin", tags=["admin"])

# Agent Endpoints

@router.post("/agents", response_model=dict)
def create_agent(
    agent_data: dict,
    session: Session = Depends(get_session)
):
    """
    Create a new AI Agent.

    This endpoint allows administrators to register a new agent in the system.
    
    Request Body (JSON):
    - id (str, optional): Unique ID for the agent (auto-generated if not provided)
    - name (str, required): Display name of the agent
    - owner (str, required): Owner identifier (user or system ID) who controls this agent
    - status (str, optional): Initial status ("active" or "disabled"). Default: "active"

    Returns:
        dict: The created agent's details including the generated ID.

    Raises:
        HTTPException(400): If creation fails (e.g. invalid status).
    """
    try:
        agent = Agent(
            id=agent_data.get("id"),
            name=agent_data.get("name"),
            owner=agent_data.get("owner"),
            status=agent_data.get("status", "active")
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        logger.info(f"Agent created: {agent.id}")
        return {
            "id": agent.id,
            "name": agent.name,
            "owner": agent.owner,
            "status": agent.status,
            "message": f"Agent {agent.id} created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents", response_model=List[dict])
def list_agents(session: Session = Depends(get_session)):
    """
    Retrieve a list of all Agents.

    Returns:
        List[dict]: A list of all registered agents with their current status.
    """
    statement = select(Agent)
    agents = session.exec(statement).all()
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "owner": agent.owner,
            "status": agent.status
        }
        for agent in agents
    ]


@router.get("/agents/{agent_id}", response_model=dict)
def get_agent(agent_id: str, session: Session = Depends(get_session)):
    """
    Retrieve details of a specific Agent by ID.

    Args:
        agent_id: The unique identifier of the agent.

    Returns:
        dict: Agent details.

    Raises:
        HTTPException(404): If the agent is not found.
    """
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "owner": agent.owner,
        "status": agent.status
    }


@router.put("/agents/{agent_id}", response_model=dict)
def update_agent(
    agent_id: str,
    agent_data: dict,
    session: Session = Depends(get_session)
):
    """
    Update an existing Agent.

    This endpoint allows partial updates. Only the fields provided in the body will be updated.

    Args:
        agent_id: The unique identifier of the agent to update.

    Request Body (JSON):
    - name (str, optional): New name for the agent
    - status (str, optional): New status ("active" or "disabled")
    - owner (str, optional): New owner identifier

    Returns:
        dict: The updated agent details.

    Raises:
        HTTPException(404): If the agent is not found.
    """
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    if "name" in agent_data:
        agent.name = agent_data["name"]
    if "status" in agent_data:
        agent.status = agent_data["status"]
    if "owner" in agent_data:
        agent.owner = agent_data["owner"]
    
    session.add(agent)
    session.commit()
    session.refresh(agent)
    logger.info(f"Agent updated: {agent_id}")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "owner": agent.owner,
        "status": agent.status,
        "message": f"Agent {agent_id} updated successfully"
    }


@router.delete("/agents/{agent_id}", response_model=dict)
def delete_agent(agent_id: str, session: Session = Depends(get_session)):
    """
    Delete an Agent and its associated Permissions.

    This is a destructive action that removes the agent record and all permissions linked to it.
    Audit logs are NOT deleted to maintain historical integrity.

    Args:
        agent_id: The unique identifier of the agent to delete.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException(404): If the agent is not found.
    """
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Delete related permissions
    statement = select(Permission).where(Permission.agent_id == agent_id)
    permissions = session.exec(statement).all()
    for perm in permissions:
        session.delete(perm)
    
    session.delete(agent)
    session.commit()
    logger.info(f"Agent deleted: {agent_id}")
    
    return {
        "id": agent_id,
        "message": f"Agent {agent_id} and its permissions deleted successfully"
    }


# Permission Endpoints

@router.post("/permissions", response_model=dict)
def create_permission(
    perm_data: dict,
    session: Session = Depends(get_session)
):
    """
    Create a new Permission rule.

    Defines what an agent is allowed to do.

    Request Body (JSON):
    - agent_id (str, required): The ID of the agent this permission applies to
    - action (str, required): The action allowed (e.g., "read", "write")
    - resource (str, required): The target resource (e.g., "database", "s3-bucket")
    - condition (str, optional): Logic condition for the permission (e.g., "time < 18:00")

    Returns:
        dict: The created permission details.
    
    Raises:
        HTTPException(400): If creation fails.
    """
    try:
        permission = Permission(
            agent_id=perm_data.get("agent_id"),
            action=perm_data.get("action"),
            resource=perm_data.get("resource"),
            condition=perm_data.get("condition")
        )
        session.add(permission)
        session.commit()
        session.refresh(permission)
        logger.info(f"Permission created: {permission.id}")
        
        return {
            "id": permission.id,
            "agent_id": permission.agent_id,
            "action": permission.action,
            "resource": permission.resource,
            "condition": permission.condition,
            "message": f"Permission created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating permission: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/permissions", response_model=List[dict])
def list_permissions(
    agent_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Retrieve all Permissions, optionally filtered by Agent.

    Args:
        agent_id (str, optional): If provided, only returns permissions for this specific agent.

    Returns:
        List[dict]: List of permissions.
    """
    statement = select(Permission)
    if agent_id:
        statement = statement.where(Permission.agent_id == agent_id)
    
    permissions = session.exec(statement).all()
    return [
        {
            "id": perm.id,
            "agent_id": perm.agent_id,
            "action": perm.action,
            "resource": perm.resource,
            "condition": perm.condition
        }
        for perm in permissions
    ]


@router.delete("/permissions/{permission_id}", response_model=dict)
def delete_permission(permission_id: str, session: Session = Depends(get_session)):
    """
    Delete a specific Permission rule.

    Args:
        permission_id: The unique identifier of the permission to delete.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException(404): If the permission is not found.
    """
    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail=f"Permission {permission_id} not found")
    
    session.delete(permission)
    session.commit()
    logger.info(f"Permission deleted: {permission_id}")
    
    return {
        "id": permission_id,
        "message": f"Permission {permission_id} deleted successfully"
    }

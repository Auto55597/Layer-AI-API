"""
Policy Management
"""
from typing import Optional
from .client import AgentClient
from .models import AgentRequest, AgentResponse

class PolicyManager:
    """
    Handles permission checks and policy enforcement.
    """
    def __init__(self, client: AgentClient):
        self.client = client

    def check_permission(self, agent_id: str, action: str, resource: str) -> AgentResponse:
        """
        Check if an agent has permission to perform an action.
        This is a passive check - it does not execute the action.
        
        Args:
            agent_id: The ID of the agent
            action: The action to perform (e.g. "read", "write")
            resource: The resource to act upon (e.g. "database", "s3")
            
        Returns:
            AgentResponse containing 'approved' or 'denied' status and trace.
        """
        payload = AgentRequest(
            agent_id=agent_id,
            action=action,
            resource=resource
        )
        
        return self.client.request(
            method="POST",
            endpoint="/agent/request",
            json=payload.model_dump(),
            model=AgentResponse
        )

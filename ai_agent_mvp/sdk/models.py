"""
SDK Data Models
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


class SDKBaseModel(BaseModel):
    """
    Base model for all SDK models.
    - Forbid unknown fields to avoid silent bugs
    """
    model_config = ConfigDict(extra="forbid")


class AgentRequest(SDKBaseModel):
    agent_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    resource: str = Field(..., min_length=1)


class DecisionTrace(SDKBaseModel):
    rule_checked: str
    rule_result: Literal["approved", "denied"]
    notes: Optional[str] = None


class AgentResponse(SDKBaseModel):
    result: Literal["approved", "denied"]
    message: str
    reason: Optional[str] = None
    decision_trace: Optional[List[DecisionTrace]] = None
    action_required: Optional[str] = None

    @property
    def is_approved(self) -> bool:
        return self.result == "approved"


class KillRequest(SDKBaseModel):
    agent_id: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    enabled: bool = Field(
        ...,
        description="False disables the agent immediately"
    )


class KillResponse(SDKBaseModel):
    result: Literal["success", "failed"]
    message: str


class SystemKillSwitchResponse(SDKBaseModel):
    status: Literal["enabled", "disabled"]
    message: str

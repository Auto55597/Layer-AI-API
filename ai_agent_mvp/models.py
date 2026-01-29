"""
Data Models for AI Agent Permission & Audit Layer
Using SQLModel for ORM and Database Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from pydantic import field_validator, Field as PydanticField
import uuid
import json


class Agent(SQLModel, table=True):
    """
    Model for Agent
    - id: Agent ID (String)
    - name: Agent name
    - owner: Agent owner (used for Kill permission check)
    - status: Agent status (active/disabled)
    - created_at: Time when Agent was created
    """
    __tablename__ = "agents"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, min_length=1, max_length=255)
    owner: str = Field(index=True, min_length=1, max_length=255)
    status: str = Field(default="active", index=True)  # "active" or "disabled"
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ["active", "disabled"]:
            raise ValueError("status must be 'active' or 'disabled'")
        return v


class SystemState(SQLModel, table=True):
    """
    Model for System State
    Used to store System-Wide Kill Switch status
    
    - key: State key (e.g. "system_kill_switch")
    - value: State value ("enabled" or "disabled")
    - updated_at: Last update time
    """
    __tablename__ = "system_state"
    
    key: str = Field(primary_key=True)  # Primary key is key to allow only 1 record
    value: str = Field(index=True)  # "enabled" or "disabled"
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class Permission(SQLModel, table=True):
    """
    Model for Permission (Access Rights)
    - id: Permission ID
    - agent_id: Agent ID that has this permission
    - action: Action allowed (e.g. "read", "write", "delete")
    - resource: Resource allowed to access (e.g. "database", "api")
    - condition: Additional conditions (Optional - e.g. "time < 18:00")
    """
    __tablename__ = "permissions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    agent_id: str = Field(foreign_key="agents.id", index=True)
    action: str = Field(index=True)
    resource: str = Field(index=True)
    condition: Optional[str] = Field(default=None)


class Log(SQLModel, table=True):
    """
    Model for Log (Activity Log)
    - id: Log ID
    - agent_id: Agent ID that made the request
    - action: Action requested
    - resource: Resource accessed
    - result: Result (approved/denied)
    - timestamp: Time event occurred
    """
    __tablename__ = "logs"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    agent_id: str = Field(foreign_key="agents.id", index=True)
    action: str = Field(index=True)
    resource: str = Field(index=True)
    result: str = Field(index=True)  # "approved" or "denied"
    timestamp: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class PendingRequest(SQLModel, table=True):
    """
    Model to store Requests requiring Human Intervention
    Used for Human-in-the-loop / Policy Layer
    
    - request_id: Request ID (primary key)
    - agent_id: Agent ID that made the request
    - action: Action requested
    - resource: Resource accessed
    - reason: Reason for needing human intervention
    - decision_trace: JSON string of decision_trace from AI checks
    - action_required: "human_intervention"
    - created_at: Time pending request was created
    - status: "pending" (waiting for human decision)
    """
    __tablename__ = "pending_requests"
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    agent_id: str = Field(index=True)
    action: str = Field(index=True)
    resource: str = Field(index=True)
    reason: str = Field(index=True)
    decision_trace: str = Field()  # JSON string of List[Dict]
    action_required: str = Field(default="human_intervention")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    status: str = Field(default="pending", index=True)  # "pending" or "resolved"


# ============================================
# SaaS Customer Models
# ============================================

class Customer(SQLModel, table=True):
    """
    Model for SaaS Customer
    - id: Customer ID
    - name: Company name
    - email: Contact email
    - subscription_tier: pricing tier ("free", "starter", "pro", "enterprise")
    - api_key_hash: Hashed API Key for database storage
    - max_agents: Maximum agents allowed
    - max_requests_per_minute: Rate limit
    - is_active: Active status
    - created_at: Signup time
    - updated_at: Last update time
    """
    __tablename__ = "customers"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, min_length=1, max_length=255)
    email: str = Field(index=True, unique=True, min_length=5, max_length=255)
    subscription_tier: str = Field(default="starter", index=True)  # "free", "starter", "pro", "enterprise"
    api_key_hash: str = Field()  # Hashed for database
    max_agents: int = Field(default=10)
    max_requests_per_minute: int = Field(default=100)
    total_api_calls: int = Field(default=0)  # For analytics
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()
    
    @field_validator('subscription_tier')
    @classmethod
    def validate_tier(cls, v):
        valid_tiers = ["free", "starter", "pro", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f"subscription_tier must be one of {valid_tiers}")
        return v


class APIKey(SQLModel, table=True):
    """
    Model for API Key Management
    - id: API Key ID
    - customer_id: Customer that owns this key
    - key_hash: API Key (hashed)
    - name: API Key name (for user reference)
    - last_used: Last used time
    - is_active: Active status
    - created_at: Creation time
    """
    __tablename__ = "api_keys"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    customer_id: str = Field(foreign_key="customers.id", index=True)
    key_hash: str = Field(unique=True)  # Hashed key
    name: str = Field(default="Default API Key")
    last_used: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


# ============================================
# Request/Response Models for API
# ============================================

class AgentRequest(SQLModel):
    """Model for Request from Agent"""
    agent_id: str = PydanticField(min_length=1, max_length=255)
    action: str = PydanticField(min_length=1, max_length=100)
    resource: str = PydanticField(min_length=1, max_length=255)
    
    @field_validator('agent_id', 'action', 'resource')
    @classmethod
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class AgentRequestResponse(SQLModel):
    """
    Model for Response of Agent Request
    
    Fields:
    - result: "approved" or "denied"
    - message: Result explanation message
    - reason: Machine-readable reason (e.g. "permission_rule_failed", "system_kill_switch_enabled")
    - decision_trace: List of trace from checking each rule
    - action_required: Action required to be taken (e.g. "human_intervention")
    """
    result: str  # "approved" or "denied"
    message: str
    reason: Optional[str] = None  # Machine-readable reason for denied/approved
    decision_trace: Optional[List[Dict[str, Any]]] = None  # Trace of checking each rule
    action_required: Optional[str] = None  # Action required (e.g. "human_intervention")


class AgentKillRequest(SQLModel):
    """Model for Kill Request (must specify owner to check permission)"""
    agent_id: str = PydanticField(min_length=1, max_length=255)
    owner: str = PydanticField(min_length=1, max_length=255)  # Agent owner to enable/disable
    enabled: bool  # True = enable (set status to "active"), False = disable (set status to "disabled")
    
    @field_validator('agent_id', 'owner')
    @classmethod
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class AgentKillResponse(SQLModel):
    """Model for Response of Kill Request"""
    result: str  # "enabled" or "disabled"
    message: str


class LogResponse(SQLModel):
    """Model for Response of Log Query"""
    id: str
    agent_id: str
    action: str
    resource: str
    result: str
    timestamp: datetime


class PermissionResponse(SQLModel):
    """Model for Response of Permission Query"""
    id: str
    agent_id: str
    action: str
    resource: str
    condition: Optional[str] = None


class SystemKillSwitchRequest(SQLModel):
    """Model for Request to Enable/Disable System Kill Switch"""
    enabled: bool  # True = enable kill switch, False = disable


class SystemKillSwitchResponse(SQLModel):
    """Model for Response of System Kill Switch"""
    status: str  # "enabled" or "disabled"
    message: str


class HumanDecisionRequest(SQLModel):
    """Model for Request from Human to Approve or Deny"""
    request_id: str = PydanticField(min_length=1, max_length=255)
    human_id: str = PydanticField(min_length=1, max_length=255)
    notes: Optional[str] = PydanticField(None, max_length=500)  # Optional notes for deny case
    
    @field_validator('request_id', 'human_id')
    @classmethod
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class HumanDecisionResponse(SQLModel):
    """Model for Response of Human Decision"""
    result: str  # "approved" or "denied"
    reason: str  # "human_override"
    decision_trace: List[Dict[str, Any]]  # AI trace + human decision combined
    action_required: Optional[str] = None  # null after human decision


class PendingApprovalResponse(SQLModel):
    """Model for Response of Pending Approval List"""
    request_id: str
    agent_id: str
    action: str
    resource: str
    reason: str
    decision_trace: List[Dict[str, Any]]
    action_required: str


# ============================================
# Customer/SaaS Request/Response Models
# ============================================

class CreateCustomerRequest(SQLModel):
    """Request model for creating Customer"""
    name: str = PydanticField(min_length=1, max_length=255)
    email: str = PydanticField(min_length=5, max_length=255)
    subscription_tier: str = PydanticField(default="starter")
    
    @field_validator('name', 'email')
    @classmethod
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()


class APIKeyResponse(SQLModel):
    """Response model for API Key"""
    id: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool


class CustomerResponse(SQLModel):
    """Response model for Customer Info"""
    id: str
    name: str
    email: str
    subscription_tier: str
    max_agents: int
    max_requests_per_minute: int
    total_api_calls: int
    is_active: bool
    created_at: datetime


class GenerateAPIKeyResponse(SQLModel):
    """Response model for generating API Key (show raw key only once)"""
    api_key: str  # Raw API key - show only once!
    key_id: str
    message: str = "⚠️  Save this API key somewhere safe. You won't be able to see it again."

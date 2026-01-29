"""
API Router for Agent Operations
- POST /agent/request: Check and Approve/Deny requests
- POST /agent/kill: Disable Agent (Kill Switch)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional, List
import uuid

import sys
import os
# Add parent directory to path to allow importing models and database modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import (
    Agent, Permission, Log, SystemState, PendingRequest,
    AgentRequest, AgentRequestResponse,
    AgentKillRequest, AgentKillResponse,
    SystemKillSwitchRequest, SystemKillSwitchResponse,
    HumanDecisionRequest, HumanDecisionResponse, PendingApprovalResponse
)
from database import get_session, SYSTEM_KILL_SWITCH_KEY
from logger_config import get_logger
import json

logger = get_logger("agent_router")
router = APIRouter(prefix="/agent", tags=["agent"])


def check_system_kill_switch(session: Session) -> bool:
    """
    Function to check System-Wide Kill Switch Status
    
    CRITICAL SAFETY FUNCTION: This function must be called before all permission checks.
    When kill switch is enabled → return True (kill switch is ON)
    When kill switch is disabled → return False (kill switch is OFF)
    
    Args:
        session: Database session
        
    Returns:
        True if kill switch is enabled (must deny all requests)
        False if kill switch is disabled (normal operation)
    """
    kill_switch = session.get(SystemState, SYSTEM_KILL_SWITCH_KEY)
    if not kill_switch:
        # If state doesn't exist → assume kill switch is off (fail-safe: default to OFF)
        logger.debug("Kill switch not found, defaulting to OFF")
        return False
    
    # If value = "enabled" → kill switch is ON
    is_enabled = kill_switch.value == "enabled"
    logger.debug(f"Kill switch status: {'ON' if is_enabled else 'OFF'}")
    return is_enabled


def check_permission(session: Session, agent_id: str, action: str, resource: str) -> bool:
    """
    Function to check Permission
    
    Logic:
    1. Find Permission matching agent_id, action, and resource
    2. If no condition exists → if permission record exists = allow
    3. If condition exists → check condition (in this example we skip real parsing)
    
    Args:
        session: Database session
        agent_id: Agent ID
        action: Action to perform
        resource: Resource to access
        
    Returns:
        True if has permission, False otherwise
    """
    # Find Permission matching agent_id, action, and resource
    statement = select(Permission).where(
        Permission.agent_id == agent_id,
        Permission.action == action,
        Permission.resource == resource
    )
    permission = session.exec(statement).first()
    
    # If Permission record found = has permission
    # (in a real system should parse and check conditions too)
    if permission:
        return True
    
    return False


def log_action(session: Session, agent_id: str, action: str, resource: str, result: str):
    """
    Function to log action
    
    Args:
        session: Database session
        agent_id: Agent ID
        action: Action performed
        resource: Resource
        result: Result ("approved" or "denied")
    """
    log = Log(
        agent_id=agent_id,
        action=action,
        resource=resource,
        result=result,
        timestamp=datetime.utcnow()
    )
    session.add(log)
    session.commit()
    logger.info(f"Logged action: agent={agent_id}, action={action}, resource={resource}, result={result}")


@router.post("/request", response_model=AgentRequestResponse)
def agent_request(
    request: AgentRequest,
    session: Session = Depends(get_session)
):
    """
    API Endpoint: POST /agent/request
    
    Workflow (SAFETY-CRITICAL):
    0. [CRITICAL] Check System-Wide Kill Switch before everything
    1. Check Agent status (if disabled → return error)
    2. Check Permission (action + resource + condition)
    3. Log action (must log in all cases)
    4. Return result with decision_trace and reason
    
    Args:
        request: AgentRequest object (agent_id, action, resource)
        session: Database session
        
    Returns:
        AgentRequestResponse: Result of check with decision trace
        
    Example Response:
        {
            "result": "denied",
            "message": "Permission denied for write on database",
            "reason": "permission_rule_failed",
            "decision_trace": [
                {"rule_checked": "kill_switch", "rule_result": "passed", "notes": "kill switch off"},
                {"rule_checked": "agent_status", "rule_result": "passed", "notes": "agent active"},
                {"rule_checked": "permission_rule", "rule_result": "failed", "notes": "user cannot write to database"}
            ],
            "action_required": null
        }
    """
    logger.info(f"Agent request received: agent_id={request.agent_id}, action={request.action}, resource={request.resource}")
    # Create decision_trace list to store trace of each rule check
    decision_trace = []
    
    try:
        # Step 0: [CRITICAL SAFETY CHECK] Check System-Wide Kill Switch before everything
        # Kill Switch must be checked before permission checks and agent status checks
        kill_switch_enabled = check_system_kill_switch(session)
        
        if kill_switch_enabled:
            # Kill Switch is ON → DENY all requests immediately
            decision_trace.append({
                "rule_checked": "kill_switch",
                "rule_result": "failed",
                "notes": "kill switch enabled - all requests blocked"
            })
            logger.warning(f"Request blocked by kill switch: agent_id={request.agent_id}")
            log_action(session, request.agent_id, request.action, request.resource, "denied")
            
            # Record pending request for human intervention
            request_id = str(uuid.uuid4())
            pending_request = PendingRequest(
                request_id=request_id,
                agent_id=request.agent_id,
                action=request.action,
                resource=request.resource,
                reason="system_kill_switch_enabled",
                decision_trace=json.dumps(decision_trace),
                action_required="human_intervention",
                status="pending"
            )
            session.add(pending_request)
            session.commit()
            
            return AgentRequestResponse(
                result="denied",
                message="System-wide kill switch is enabled. All agent actions are blocked.",
                reason="system_kill_switch_enabled",
                decision_trace=decision_trace,
                action_required="human_intervention"
            )
        else:
            # Kill Switch is OFF → Pass this check
            decision_trace.append({
                "rule_checked": "kill_switch",
                "rule_result": "passed",
                "notes": "kill switch off"
            })
        
        # Step 1: Check Agent status (if disabled → return error)
        agent = session.get(Agent, request.agent_id)
        if not agent:
            decision_trace.append({
                "rule_checked": "agent_status",
                "rule_result": "failed",
                "notes": f"agent {request.agent_id} not found"
            })
            logger.warning(f"Agent not found: {request.agent_id}")
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
        
        if agent.status == "disabled":
            # Agent is disabled → DENY
            decision_trace.append({
                "rule_checked": "agent_status",
                "rule_result": "failed",
                "notes": f"agent {request.agent_id} is disabled"
            })
            log_action(session, request.agent_id, request.action, request.resource, "denied")
            return AgentRequestResponse(
                result="denied",
                message=f"Agent {request.agent_id} is disabled",
                reason="agent_disabled",
                decision_trace=decision_trace,
                action_required=None
            )
        else:
            # Agent is active → Pass this check
            decision_trace.append({
                "rule_checked": "agent_status",
                "rule_result": "passed",
                "notes": "agent active"
            })
        
        # Step 2: Check Permission
        has_permission = check_permission(session, request.agent_id, request.action, request.resource)
        
        if has_permission:
            # Has permission → Pass this check
            decision_trace.append({
                "rule_checked": "permission_rule",
                "rule_result": "passed",
                "notes": f"permission granted for {request.action} on {request.resource}"
            })
            log_action(session, request.agent_id, request.action, request.resource, "approved")
            return AgentRequestResponse(
                result="approved",
                message=f"Permission granted for {request.action} on {request.resource}",
                reason="all_checks_passed",
                decision_trace=decision_trace,
                action_required=None
            )
        else:
            # No permission → DENY
            decision_trace.append({
                "rule_checked": "permission_rule",
                "rule_result": "failed",
                "notes": f"no permission for {request.action} on {request.resource}"
            })
            log_action(session, request.agent_id, request.action, request.resource, "denied")
            return AgentRequestResponse(
                result="denied",
                message=f"No permission for {request.action} on {request.resource}",
                reason="permission_rule_failed",
                decision_trace=decision_trace,
                action_required=None
            )
    
    except HTTPException:
        # Re-raise HTTPException (e.g., 404 Not Found)
        raise
    except Exception as e:
        # Fail-safe: if any error occurs → DENY and log error in trace
        decision_trace.append({
            "rule_checked": "system_error",
            "rule_result": "failed",
            "notes": f"system error occurred: {str(e)}"
        })
        logger.error(f"System error in agent request: {str(e)}", exc_info=True)
        try:
            log_action(session, request.agent_id, request.action, request.resource, "denied")
        except:
            pass  # If logging fails, it's okay (fail-safe)
        
        # Record pending request for human intervention (system error)
        try:
            request_id = str(uuid.uuid4())
            pending_request = PendingRequest(
                request_id=request_id,
                agent_id=request.agent_id,
                action=request.action,
                resource=request.resource,
                reason="system_error",
                decision_trace=json.dumps(decision_trace),
                action_required="human_intervention",
                status="pending"
            )
            session.add(pending_request)
            session.commit()
        except:
            pass  # If recording fails, it's okay (fail-safe)
        
        return AgentRequestResponse(
            result="denied",
            message="System error occurred during request processing",
            reason="system_error",
            decision_trace=decision_trace,
            action_required="human_intervention"
        )


@router.post("/kill", response_model=AgentKillResponse)
def agent_kill(
    request: AgentKillRequest,
    session: Session = Depends(get_session)
):
    """
    API Endpoint: POST /agent/kill
    
    Workflow (Kill Switch):
    1. Check Owner permission (owner must match agent owner)
    2. Adjust status based on enabled field:
       - enabled=True → status="active"
       - enabled=False → status="disabled"
    3. Log event
    4. Return { "result": "enabled"/"disabled", "message": "..." }
    
    Args:
        request: AgentKillRequest object (agent_id, owner, enabled)
        session: Database session
        
    Returns:
        AgentKillResponse: Result of enable/disable action
    """
    # Step 1: Check Agent and Owner permission
    agent = session.get(Agent, request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    if agent.owner != request.owner:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: Only owner '{agent.owner}' can enable/disable this agent"
        )
    
    # Step 2: Adjust status based on enabled field
    if request.enabled:
        agent.status = "active"
        result_status = "enabled"
        log_result = "enabled"
        action_description = "enabled"
    else:
        agent.status = "disabled"
        result_status = "disabled"
        log_result = "disabled"
        action_description = "disabled"
    
    session.add(agent)
    session.commit()
    session.refresh(agent)
    
    # Step 3: Log event (record as special action "kill")
    log_action(session, request.agent_id, "kill", "agent", log_result)
    
    # Step 4: Return result
    return AgentKillResponse(
        result=result_status,
        message=f"Agent {request.agent_id} has been {action_description} by owner {request.owner}"
    )


@router.post("/system-kill-switch", response_model=SystemKillSwitchResponse)
def set_system_kill_switch(
    request: SystemKillSwitchRequest,
    session: Session = Depends(get_session)
):
    """
    API Endpoint: POST /agent/system-kill-switch
    
    Enable/Disable System-Wide Kill Switch
    
    CRITICAL SAFETY ENDPOINT: Used for emergency situations to stop all Agent operations immediately
    
    Args:
        request: SystemKillSwitchRequest object (enabled: bool)
        session: Database session
        
    Returns:
        SystemKillSwitchResponse: Current status of kill switch
    """
    logger.warning(f"System kill switch change requested: enabled={request.enabled}")
    # Update kill switch state
    kill_switch = session.get(SystemState, SYSTEM_KILL_SWITCH_KEY)
    if not kill_switch:
        # If state doesn't exist → create new
        kill_switch = SystemState(
            key=SYSTEM_KILL_SWITCH_KEY,
            value="enabled" if request.enabled else "disabled",
            updated_at=datetime.utcnow()
        )
        session.add(kill_switch)
    else:
        # Update existing state
        kill_switch.value = "enabled" if request.enabled else "disabled"
        kill_switch.updated_at = datetime.utcnow()
        session.add(kill_switch)
    
    session.commit()
    session.refresh(kill_switch)
    
    # Log kill switch change
    log_action(
        session,
        agent_id="system",
        action="system_kill_switch",
        resource="system",
        result="enabled" if request.enabled else "disabled"
    )
    
    logger.info(f"System kill switch changed to: {'enabled' if request.enabled else 'disabled'}")
    
    status = "enabled" if request.enabled else "disabled"
    return SystemKillSwitchResponse(
        status=status,
        message=f"System kill switch has been {status}. All agent requests will be {'denied' if request.enabled else 'processed normally'}."
    )


@router.get("/system-kill-switch", response_model=SystemKillSwitchResponse)
def get_system_kill_switch(
    session: Session = Depends(get_session)
):
    """
    API Endpoint: GET /agent/system-kill-switch
    
    View current status of System-Wide Kill Switch
    
    Returns:
        SystemKillSwitchResponse: Current status of kill switch
    """
    kill_switch = session.get(SystemState, SYSTEM_KILL_SWITCH_KEY)
    if not kill_switch:
        # If state doesn't exist → assume disabled (fail-safe)
        return SystemKillSwitchResponse(
            status="disabled",
            message="System kill switch is disabled (default state)"
        )
    
    status = kill_switch.value
    return SystemKillSwitchResponse(
        status=status,
        message=f"System kill switch is {status}. All agent requests are {'denied' if status == 'enabled' else 'processed normally'}."
    )


@router.get("/pending-approvals", response_model=List[PendingApprovalResponse])
def get_pending_approvals(
    session: Session = Depends(get_session)
):
    """
    API Endpoint: GET /agent/pending-approvals
    
    Retrieve list of Requests requiring Human Intervention
    
    Returns:
        List[PendingApprovalResponse]: List of pending requests with action_required="human_intervention"
        
    Example Response:
        [
            {
                "request_id": "req-001",
                "agent_id": "agent-001",
                "action": "write",
                "resource": "database",
                "reason": "system_kill_switch_enabled",
                "decision_trace": [
                    {"rule_checked": "kill_switch", "rule_result": "failed", "notes": "..."}
                ],
                "action_required": "human_intervention"
            }
        ]
    """
    # Find pending requests that are not yet resolved
    statement = select(PendingRequest).where(
        PendingRequest.status == "pending",
        PendingRequest.action_required == "human_intervention"
    )
    pending_requests = session.exec(statement).all()
    
    # Convert to response format
    result = []
    for pr in pending_requests:
        # Parse decision_trace from JSON string
        try:
            decision_trace = json.loads(pr.decision_trace) if pr.decision_trace else []
        except:
            decision_trace = []
        
        result.append(PendingApprovalResponse(
            request_id=pr.request_id,
            agent_id=pr.agent_id,
            action=pr.action,
            resource=pr.resource,
            reason=pr.reason,
            decision_trace=decision_trace,
            action_required=pr.action_required
        ))
    
    return result


@router.post("/approve", response_model=HumanDecisionResponse)
def human_approve(
    request: HumanDecisionRequest,
    session: Session = Depends(get_session)
):
    """
    API Endpoint: POST /agent/approve
    
    Human Approve Request that was blocked
    
    Workflow:
    1. Find pending request by request_id
    2. If not found → return denied + reason="system_error"
    3. Parse existing decision_trace
    4. Append human decision entry
    5. Update pending request status = "resolved"
    6. Log action
    7. Return response
    
    Args:
        request: HumanDecisionRequest (request_id, human_id, notes=None)
        session: Database session
        
    Returns:
        HumanDecisionResponse: Result of approval
        
    Example Response:
        {
            "result": "approved",
            "reason": "human_override",
            "decision_trace": [
                ... previous AI trace ...,
                {
                    "rule_checked": "human_decision",
                    "rule_result": "passed",
                    "notes": "approved by human alice"
                }
            ],
            "action_required": null
        }
    """
    # Find pending request
    pending_request = session.get(PendingRequest, request.request_id)
    
    if not pending_request or pending_request.status != "pending":
        # Fail-safe: if not found → return denied
        return HumanDecisionResponse(
            result="denied",
            reason="system_error",
            decision_trace=[{
                "rule_checked": "human_decision",
                "rule_result": "failed",
                "notes": f"request_id {request.request_id} not found or already resolved"
            }],
            action_required=None
        )
    
    # Parse existing decision_trace
    try:
        decision_trace = json.loads(pending_request.decision_trace) if pending_request.decision_trace else []
    except:
        decision_trace = []
    
    # Append human decision entry
    decision_trace.append({
        "rule_checked": "human_decision",
        "rule_result": "passed",
        "notes": f"approved by human {request.human_id}"
    })
    
    # Update pending request status
    pending_request.status = "resolved"
    session.add(pending_request)
    
    # Log action
    log_action(session, pending_request.agent_id, pending_request.action, pending_request.resource, "approved")
    
    session.commit()
    
    return HumanDecisionResponse(
        result="approved",
        reason="human_override",
        decision_trace=decision_trace,
        action_required=None
    )


@router.post("/deny", response_model=HumanDecisionResponse)
def human_deny(
    request: HumanDecisionRequest,
    session: Session = Depends(get_session)
):
    """
    API Endpoint: POST /agent/deny
    
    Human Deny Request that was blocked
    
    Workflow:
    1. Find pending request by request_id
    2. If not found → return denied + reason="system_error"
    3. Parse existing decision_trace
    4. Append human decision entry (with optional notes)
    5. Update pending request status = "resolved"
    6. Log action
    7. Return response
    
    Args:
        request: HumanDecisionRequest (request_id, human_id, notes=Optional)
        session: Database session
        
    Returns:
        HumanDecisionResponse: Result of denial
        
    Example Response:
        {
            "result": "denied",
            "reason": "human_override",
            "decision_trace": [
                ... previous AI trace ...,
                {
                    "rule_checked": "human_decision",
                    "rule_result": "failed",
                    "notes": "denied by human bob (not authorized)"
                }
            ],
            "action_required": null
        }
    """
    # Find pending request
    pending_request = session.get(PendingRequest, request.request_id)
    
    if not pending_request or pending_request.status != "pending":
        # Fail-safe: if not found → return denied
        return HumanDecisionResponse(
            result="denied",
            reason="system_error",
            decision_trace=[{
                "rule_checked": "human_decision",
                "rule_result": "failed",
                "notes": f"request_id {request.request_id} not found or already resolved"
            }],
            action_required=None
        )
    
    # Parse existing decision_trace
    try:
        decision_trace = json.loads(pending_request.decision_trace) if pending_request.decision_trace else []
    except:
        decision_trace = []
    
    # Create notes for human decision
    notes = f"denied by human {request.human_id}"
    if request.notes:
        notes += f" ({request.notes})"
    
    # Append human decision entry
    decision_trace.append({
        "rule_checked": "human_decision",
        "rule_result": "failed",
        "notes": notes
    })
    
    # Update pending request status
    pending_request.status = "resolved"
    session.add(pending_request)
    
    # Log action
    log_action(session, pending_request.agent_id, pending_request.action, pending_request.resource, "denied")
    
    session.commit()
    
    return HumanDecisionResponse(
        result="denied",
        reason="human_override",
        decision_trace=decision_trace,
        action_required=None
    )

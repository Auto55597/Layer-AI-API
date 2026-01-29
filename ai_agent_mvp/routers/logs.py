"""
API Router for Logs Query
- GET /logs: Retrieve Audit Logs with optional filtering
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional, List

import sys
import os
# Add parent directory to path to allow importing models and database modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from models import Log, LogResponse
from database import get_session

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/", response_model=List[LogResponse])
def get_logs(
    agent_id: Optional[str] = Query(None, description="Filter logs by a specific Agent ID"),
    start_time: Optional[str] = Query(None, description="Filter logs after this timestamp (ISO format: YYYY-MM-DDTHH:MM:SS)"),
    end_time: Optional[str] = Query(None, description="Filter logs before this timestamp (ISO format: YYYY-MM-DDTHH:MM:SS)"),
    session: Session = Depends(get_session)
):
    """
    Retrieve Audit Logs.

    Provides a historical record of all agent actions, decisions, and system events.
    Results are ordered by timestamp (newest first).

    Args:
        agent_id: Optional filter for a specific agent.
        start_time: Optional start of time range (inclusive).
        end_time: Optional end of time range (inclusive).

    Returns:
        List[LogResponse]: A list of audit log entries matching the criteria.

    Raises:
        HTTPException(400): If the date format is invalid.
    """
    statement = select(Log)

    if agent_id:
        statement = statement.where(Log.agent_id == agent_id)

    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            statement = statement.where(Log.timestamp >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            statement = statement.where(Log.timestamp <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

    statement = statement.order_by(Log.timestamp.desc())
    logs = session.exec(statement).all()

    return [
        LogResponse(
            id=log.id,
            agent_id=log.agent_id,
            action=log.action,
            resource=log.resource,
            result=log.result,
            timestamp=log.timestamp
        )
        for log in logs
    ]

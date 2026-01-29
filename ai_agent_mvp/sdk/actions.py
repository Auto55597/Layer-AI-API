"""
Action Execution
High-level action runner with explicit policy enforcement.
"""

from typing import Any, Callable
from .client import AgentClient
from .policy import PolicyManager
from .errors import SDKError, ValidationError


class ActionRunner:
    """
    Executes actions with explicit policy checks.

    This class is intentionally opinionated:
    - Policy is checked BEFORE execution by default
    - Business logic is executed ONLY after approval
    - Failures are surfaced as typed SDK errors
    """

    def __init__(self, client: AgentClient):
        if not client:
            raise ValidationError("AgentClient is required")

        self.client = client
        self.policy = PolicyManager(client)
        self.logger = client.logger

    def execute(
        self,
        agent_id: str,
        action: str,
        resource: str,
        executor_func: Callable[[], Any],
        *,
        skip_policy_check: bool = False,
    ) -> Any:
        """
        Execute an action safely with policy enforcement.

        Execution Flow:
        1. Validate inputs
        2. Check policy (unless explicitly skipped)
        3. Execute business logic
        4. Return result or raise SDKError

        Args:
            agent_id: ID of the acting agent
            action: Action name (e.g. "read", "write")
            resource: Target resource
            executor_func: Callable containing real business logic
            skip_policy_check: Explicitly bypass policy enforcement (dangerous)

        Returns:
            Result of executor_func()

        Raises:
            SDKError: Permission denied or execution failure
        """

        # ---- Input validation (fail fast) ----
        if not agent_id:
            raise ValidationError("agent_id is required")
        if not action:
            raise ValidationError("action is required")
        if not resource:
            raise ValidationError("resource is required")
        if not callable(executor_func):
            raise ValidationError("executor_func must be callable")

        # ---- Policy enforcement ----
        if not skip_policy_check:
            self.logger.info(
                "Policy check started",
                extra={
                    "agent_id": agent_id,
                    "action": action,
                    "resource": resource,
                },
            )

            decision = self.policy.check_permission(
                agent_id=agent_id,
                action=action,
                resource=resource,
            )

            if not decision.is_approved:
                self.logger.warning(
                    "Action blocked by policy",
                    extra={
                        "agent_id": agent_id,
                        "action": action,
                        "resource": resource,
                        "reason": decision.reason,
                    },
                )
                raise SDKError(
                    f"Action denied: {decision.message}",
                )

            self.logger.info(
                "Policy approved",
                extra={
                    "agent_id": agent_id,
                    "action": action,
                    "resource": resource,
                },
            )

        # ---- Execute business logic ----
        try:
            self.logger.info(
                "Executing action",
                extra={
                    "agent_id": agent_id,
                    "action": action,
                    "resource": resource,
                },
            )
            result = executor_func()
            self.logger.info("Action execution completed successfully")
            return result

        except SDKError:
            # Preserve SDK-level errors exactly
            raise
        except Exception as exc:
            self.logger.error(
                "Action execution failed",
                exc_info=True,
                extra={
                    "agent_id": agent_id,
                    "action": action,
                    "resource": resource,
                },
            )
            raise SDKError(
                "Action execution failed",
                original_error=exc,
            )

    def kill_agent(self, agent_id: str, owner: str) -> str:
        """
        Kill switch: Immediately disable an agent.

        This method does NOT execute business logic.
        It only issues a control-plane command.
        """
        if not agent_id or not owner:
            raise ValidationError("agent_id and owner are required")

        from .models import KillRequest, KillResponse

        payload = KillRequest(
            agent_id=agent_id,
            owner=owner,
            enabled=False,
        )

        response: KillResponse = self.client.request(
            method="POST",
            endpoint="/agent/kill",
            json=payload.model_dump(),
            model=KillResponse,
        )

        return response.message

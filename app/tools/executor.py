from __future__ import annotations

import time
from typing import Any

from pydantic import ValidationError

from app.observability.agent_metrics import (
    record_tool_result,
)

from app.tools.audit import (
    write_tool_audit,
)

from app.tools.base import (
    ToolExecutionContext,
    ToolResult,
)

from app.tools.policy import (
    authorize_tool,
)

from app.tools.registry import (
    get_tool,
)


def execute_tool(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    context: ToolExecutionContext,
) -> ToolResult:

    started = (
        time.perf_counter()
    )

    def finalize(
        result: ToolResult,
    ) -> ToolResult:

        duration_ms = (
            time.perf_counter()
            - started
        ) * 1000.0

        record_tool_result(
            tool_name=tool_name,
            status=result.status,
            success=result.success,
            duration_ms=duration_ms,
        )

        return result

    # =========================================================
    # 1. POLICY AUTHORIZATION
    # =========================================================

    policy = authorize_tool(
        tool_name=tool_name,
        actor_roles=(
            context.actor_roles
        ),
    )

    if not policy.allowed:

        result = ToolResult(
            tool_name=tool_name,
            status="denied",
            success=False,
            message=(
                policy.reason
            ),
            error_code=(
                "TOOL_NOT_AUTHORIZED"
            ),
        )

        write_tool_audit(
            actor_id=(
                context.actor_id
            ),
            thread_id=(
                context.thread_id
            ),
            tool_name=tool_name,
            status=result.status,
            success=False,
            details={
                "error_code": (
                    result.error_code
                ),
                "policy_reason": (
                    policy.reason
                ),
                "actor_roles": (
                    sorted(
                        context.actor_roles
                    )
                ),
            },
        )

        return finalize(
            result
        )

    # =========================================================
    # 2. REGISTRY LOOKUP
    # =========================================================

    try:

        tool = get_tool(
            tool_name
        )

    except KeyError:

        result = ToolResult(
            tool_name=tool_name,
            status="failed",
            success=False,
            message=(
                "Requested tool "
                "does not exist."
            ),
            error_code=(
                "UNKNOWN_TOOL"
            ),
        )

        write_tool_audit(
            actor_id=(
                context.actor_id
            ),
            thread_id=(
                context.thread_id
            ),
            tool_name=tool_name,
            status=result.status,
            success=False,
            details={
                "error_code": (
                    result.error_code
                )
            },
        )

        return finalize(
            result
        )

    # =========================================================
    # 3. INPUT VALIDATION
    # =========================================================

    try:

        validated_input = (
            tool.input_model(
                **arguments
            )
        )

    except ValidationError as exc:

        result = ToolResult(
            tool_name=tool_name,
            status="failed",
            success=False,
            message=(
                "Tool input validation "
                "failed."
            ),
            error_code=(
                "INVALID_TOOL_INPUT"
            ),
            data={
                "validation_errors": (
                    exc.errors()
                )
            },
        )

        write_tool_audit(
            actor_id=(
                context.actor_id
            ),
            thread_id=(
                context.thread_id
            ),
            tool_name=tool_name,
            status=result.status,
            success=False,
            details=result.data,
        )

        return finalize(
            result
        )

    # =========================================================
    # 4. TOOL EXECUTION
    # =========================================================

    try:

        result = tool.execute(
            tool_input=validated_input,
            context=context,
        )

    except Exception as exc:

        result = ToolResult(
            tool_name=tool_name,
            status="failed",
            success=False,
            message=(
                "Tool execution failed."
            ),
            error_code=(
                "TOOL_EXECUTION_ERROR"
            ),
            data={
                "exception_type": (
                    type(
                        exc
                    ).__name__
                )
            },
        )

    # =========================================================
    # 5. AUDIT
    # =========================================================

    write_tool_audit(
        actor_id=(
            context.actor_id
        ),
        thread_id=(
            context.thread_id
        ),
        tool_name=tool_name,
        status=result.status,
        success=result.success,
        details={
            "execution_id": (
                result.execution_id
            ),
            "error_code": (
                result.error_code
            ),
            "actor_roles": (
                sorted(
                    context.actor_roles
                )
            ),
            "policy_reason": (
                policy.reason
            ),
        },
    )

    return finalize(
        result
    )
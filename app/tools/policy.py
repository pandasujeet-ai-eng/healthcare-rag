from __future__ import annotations

from dataclasses import dataclass


REVIEWER_ROLE = (
    "HealthcareRAG.Reviewer"
)


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str


TOOL_ROLE_POLICY: dict[
    str,
    set[str],
] = {
    "create_review_request": {
        REVIEWER_ROLE,
    },
}


def authorize_tool(
    *,
    tool_name: str,
    actor_roles: set[str],
) -> ToolPolicyDecision:

    required_roles = (
        TOOL_ROLE_POLICY.get(
            tool_name
        )
    )

    if required_roles is None:

        return ToolPolicyDecision(
            allowed=False,
            reason=(
                "No authorization policy "
                "exists for this tool."
            ),
        )

    matched_roles = (
        actor_roles
        & required_roles
    )

    if not matched_roles:

        return ToolPolicyDecision(
            allowed=False,
            reason=(
                "Actor does not have a role "
                "permitted to execute this tool."
            ),
        )

    return ToolPolicyDecision(
        allowed=True,
        reason=(
            "Actor role satisfies tool policy."
        ),
    )
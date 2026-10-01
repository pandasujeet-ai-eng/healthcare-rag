from __future__ import annotations

from app.tools.base import (
    GovernedTool,
)

from app.tools.review_request_tool import (
    CreateReviewRequestTool,
)


_TOOL_REGISTRY: dict[
    str,
    GovernedTool,
] = {
    CreateReviewRequestTool.name: (
        CreateReviewRequestTool()
    ),
}


def get_tool(
    tool_name: str,
) -> GovernedTool:

    tool = _TOOL_REGISTRY.get(
        tool_name
    )

    if tool is None:
        raise KeyError(
            f"Unknown tool: {tool_name}"
        )

    return tool


def list_tools() -> list[str]:

    return sorted(
        _TOOL_REGISTRY.keys()
    )
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ToolExecutionContext:
    actor_id: str
    actor_roles: set[str]
    thread_id: str


class ToolResult(BaseModel):
    tool_name: str
    status: str
    success: bool

    execution_id: str | None = None
    message: str | None = None

    data: dict[str, Any] = Field(
        default_factory=dict
    )

    error_code: str | None = None


class GovernedTool(ABC):

    name: str
    description: str
    input_model: type[BaseModel]

    @abstractmethod
    def execute(
        self,
        *,
        tool_input: BaseModel,
        context: ToolExecutionContext,
    ) -> ToolResult:
        raise NotImplementedError
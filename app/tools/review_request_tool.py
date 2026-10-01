from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import (
    GovernedTool,
    ToolExecutionContext,
    ToolResult,
)


REVIEW_REQUEST_PATH = Path(
    "data/tool_runtime/review_requests.jsonl"
)


class CreateReviewRequestInput(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=4000,
    )

    supporting_chunk_ids: list[str] = []

    reason: str | None = None


class CreateReviewRequestTool(
    GovernedTool
):

    name = "create_review_request"

    description = (
        "Create a durable human review request "
        "for a healthcare policy question."
    )

    input_model = (
        CreateReviewRequestInput
    )

    @staticmethod
    def _build_idempotency_key(
        *,
        thread_id: str,
        question: str,
    ) -> str:

        raw = (
            f"{thread_id}|"
            f"{question.strip()}"
        )

        return hashlib.sha256(
            raw.encode(
                "utf-8"
            )
        ).hexdigest()

    @staticmethod
    def _load_existing_records(
    ) -> list[dict[str, Any]]:

        if not REVIEW_REQUEST_PATH.exists():
            return []

        records: list[
            dict[str, Any]
        ] = []

        with REVIEW_REQUEST_PATH.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for line in handle:

                line = line.strip()

                if not line:
                    continue

                try:
                    records.append(
                        json.loads(
                            line
                        )
                    )

                except json.JSONDecodeError:
                    continue

        return records

    @staticmethod
    def _write_record(
        record: dict[str, Any],
    ) -> None:

        REVIEW_REQUEST_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with REVIEW_REQUEST_PATH.open(
            "a",
            encoding="utf-8",
        ) as handle:

            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
            )

            handle.write(
                "\n"
            )

    def execute(
        self,
        *,
        tool_input: BaseModel,
        context: ToolExecutionContext,
    ) -> ToolResult:

        if not isinstance(
            tool_input,
            CreateReviewRequestInput,
        ):
            raise TypeError(
                "Invalid tool input model."
            )

        idempotency_key = (
            self._build_idempotency_key(
                thread_id=(
                    context.thread_id
                ),
                question=(
                    tool_input.question
                ),
            )
        )

        existing_records = (
            self._load_existing_records()
        )

        for record in existing_records:

            if (
                record.get(
                    "idempotency_key"
                )
                == idempotency_key
            ):

                return ToolResult(
                    tool_name=self.name,
                    status="already_exists",
                    success=True,
                    execution_id=record.get(
                        "review_request_id"
                    ),
                    message=(
                        "Review request already exists "
                        "for this workflow."
                    ),
                    data=record,
                )

        review_request_id = str(
            uuid.uuid4()
        )

        created_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        record = {
            "review_request_id": (
                review_request_id
            ),
            "idempotency_key": (
                idempotency_key
            ),
            "thread_id": (
                context.thread_id
            ),
            "actor_id": (
                context.actor_id
            ),
            "question": (
                tool_input.question
            ),
            "reason": (
                tool_input.reason
            ),
            "supporting_chunk_ids": (
                tool_input.supporting_chunk_ids
            ),
            "status": (
                "pending_review"
            ),
            "created_at": (
                created_at
            ),
        }

        self._write_record(
            record
        )

        return ToolResult(
            tool_name=self.name,
            status="executed",
            success=True,
            execution_id=(
                review_request_id
            ),
            message=(
                "Review request created successfully."
            ),
            data=record,
        )
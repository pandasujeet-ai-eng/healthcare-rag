from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUDIT_PATH = Path(
    "data/tool_runtime/tool_audit.jsonl"
)


def write_tool_audit(
    *,
    actor_id: str,
    thread_id: str,
    tool_name: str,
    status: str,
    success: bool,
    details: dict[str, Any] | None = None,
) -> None:

    AUDIT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "actor_id": actor_id,
        "thread_id": thread_id,
        "tool_name": tool_name,
        "status": status,
        "success": success,
        "details": (
            details
            or {}
        ),
    }

    with AUDIT_PATH.open(
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
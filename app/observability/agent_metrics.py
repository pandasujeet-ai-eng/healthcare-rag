from __future__ import annotations

import threading
import time
from collections import Counter
from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import metrics
from opentelemetry import trace


METER_NAME = "healthcare-rag-agent"

meter = metrics.get_meter(
    METER_NAME
)


# =====================================================================
# OPENTELEMETRY METRICS
# =====================================================================


request_counter = meter.create_counter(
    name="healthcare_rag.agent.requests",
    unit="1",
    description="Total agent requests.",
)


route_counter = meter.create_counter(
    name="healthcare_rag.agent.routes",
    unit="1",
    description="Agent routing decisions.",
)


hitl_counter = meter.create_counter(
    name="healthcare_rag.agent.hitl",
    unit="1",
    description="Human review events.",
)


tool_counter = meter.create_counter(
    name="healthcare_rag.agent.tools",
    unit="1",
    description="Tool execution events.",
)


retry_counter = meter.create_counter(
    name="healthcare_rag.agent.retries",
    unit="1",
    description="Retry attempts.",
)


error_counter = meter.create_counter(
    name="healthcare_rag.agent.errors",
    unit="1",
    description="Agent processing errors.",
)


degraded_counter = meter.create_counter(
    name="healthcare_rag.agent.degraded",
    unit="1",
    description="Requests completed in degraded mode.",
)


stage_latency = meter.create_histogram(
    name="healthcare_rag.agent.stage.duration",
    unit="ms",
    description="LangGraph stage execution duration.",
)


tool_latency = meter.create_histogram(
    name="healthcare_rag.agent.tool.duration",
    unit="ms",
    description="Tool execution duration.",
)


# =====================================================================
# LOCAL DEVELOPMENT SNAPSHOT
#
# This is NOT the production monitoring store.
# It simply allows us to validate instrumentation locally.
# =====================================================================


_local_lock = threading.Lock()

_local_counters: Counter[str] = Counter()

_local_stage_latency: dict[
    str,
    list[float],
] = {}

_local_tool_latency: dict[
    str,
    list[float],
] = {}


def _increment_local(
    key: str,
    value: int = 1,
) -> None:

    with _local_lock:
        _local_counters[
            key
        ] += value


def _record_local_latency(
    *,
    collection: dict[str, list[float]],
    key: str,
    duration_ms: float,
) -> None:

    with _local_lock:

        if key not in collection:
            collection[
                key
            ] = []

        collection[
            key
        ].append(
            duration_ms
        )


# =====================================================================
# TRACE ATTRIBUTE HELPERS
# =====================================================================


def set_current_span_attributes(
    attributes: dict[str, Any],
) -> None:

    span = trace.get_current_span()

    if span is None:
        return

    for key, value in attributes.items():

        if value is None:
            continue

        try:
            span.set_attribute(
                key,
                value,
            )

        except Exception:
            pass


# =====================================================================
# REQUEST METRICS
# =====================================================================


def record_request(
    *,
    actor_id: str | None = None,
) -> None:

    attributes = {}

    if actor_id:
        attributes[
            "actor.present"
        ] = True

    request_counter.add(
        1,
        attributes,
    )

    _increment_local(
        "requests"
    )


# =====================================================================
# ROUTING
# =====================================================================


def record_route(
    *,
    route: str,
    thread_id: str | None = None,
) -> None:

    attributes = {
        "route": route,
    }

    route_counter.add(
        1,
        attributes,
    )

    _increment_local(
        f"route.{route}"
    )

    set_current_span_attributes(
        {
            "agent.route": route,
            "agent.thread_id": (
                thread_id
            ),
        }
    )


# =====================================================================
# HITL
# =====================================================================


def record_hitl(
    *,
    event: str,
) -> None:

    hitl_counter.add(
        1,
        {
            "event": event,
        },
    )

    _increment_local(
        f"hitl.{event}"
    )


# =====================================================================
# RETRIES
# =====================================================================


def record_retry(
    *,
    operation: str,
    error_type: str,
) -> None:

    retry_counter.add(
        1,
        {
            "operation": operation,
            "error_type": (
                error_type
            ),
        },
    )

    _increment_local(
        f"retry.{operation}"
    )


# =====================================================================
# ERRORS
# =====================================================================


def record_error(
    *,
    stage: str,
    error_type: str | None,
) -> None:

    error_counter.add(
        1,
        {
            "stage": stage,
            "error_type": (
                error_type
                or "unknown"
            ),
        },
    )

    _increment_local(
        f"error.{stage}"
    )

    set_current_span_attributes(
        {
            "agent.error_stage": stage,
            "agent.error_type": (
                error_type
                or "unknown"
            ),
        }
    )


def record_degraded(
    *,
    stage: str,
) -> None:

    degraded_counter.add(
        1,
        {
            "stage": stage,
        },
    )

    _increment_local(
        f"degraded.{stage}"
    )


# =====================================================================
# TOOLS
# =====================================================================


def record_tool_result(
    *,
    tool_name: str,
    status: str,
    success: bool,
    duration_ms: float,
) -> None:

    attributes = {
        "tool": tool_name,
        "status": status,
        "success": success,
    }

    tool_counter.add(
        1,
        attributes,
    )

    tool_latency.record(
        duration_ms,
        attributes,
    )

    _increment_local(
        f"tool.{tool_name}.{status}"
    )

    _record_local_latency(
        collection=(
            _local_tool_latency
        ),
        key=tool_name,
        duration_ms=duration_ms,
    )

    set_current_span_attributes(
        {
            "agent.tool.name": (
                tool_name
            ),
            "agent.tool.status": (
                status
            ),
            "agent.tool.success": (
                success
            ),
        }
    )


# =====================================================================
# STAGE LATENCY
# =====================================================================


@contextmanager
def observe_stage(
    stage: str,
) -> Iterator[None]:

    started = (
        time.perf_counter()
    )

    try:
        yield

    finally:

        duration_ms = (
            time.perf_counter()
            - started
        ) * 1000.0

        stage_latency.record(
            duration_ms,
            {
                "stage": stage,
            },
        )

        _record_local_latency(
            collection=(
                _local_stage_latency
            ),
            key=stage,
            duration_ms=duration_ms,
        )

        set_current_span_attributes(
            {
                "agent.stage": stage,
                "agent.stage.duration_ms": (
                    duration_ms
                ),
            }
        )


# =====================================================================
# LOCAL DEBUGGING
# =====================================================================


def reset_local_metrics() -> None:

    with _local_lock:

        _local_counters.clear()

        _local_stage_latency.clear()

        _local_tool_latency.clear()


def _summarize_latencies(
    values: dict[
        str,
        list[float],
    ],
) -> dict[str, dict[str, float]]:

    result = {}

    for key, durations in values.items():

        if not durations:
            continue

        result[
            key
        ] = {
            "count": float(
                len(
                    durations
                )
            ),
            "min_ms": min(
                durations
            ),
            "max_ms": max(
                durations
            ),
            "avg_ms": (
                sum(
                    durations
                )
                / len(
                    durations
                )
            ),
        }

    return result


def get_local_metric_snapshot(
) -> dict[str, Any]:

    with _local_lock:

        counters = dict(
            _local_counters
        )

        stage_values = {
            key: list(value)
            for key, value
            in _local_stage_latency.items()
        }

        tool_values = {
            key: list(value)
            for key, value
            in _local_tool_latency.items()
        }

    return {
        "counters": counters,
        "stage_latency": (
            _summarize_latencies(
                stage_values
            )
        ),
        "tool_latency": (
            _summarize_latencies(
                tool_values
            )
        ),
    }
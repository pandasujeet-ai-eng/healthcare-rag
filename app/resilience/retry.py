from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from app.observability.agent_metrics import (
    record_retry,
)

from app.resilience.policy import (
    DEFAULT_RETRY_POLICY,
    RetryPolicy,
)


RETRYABLE_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}


@dataclass
class OperationResult:
    success: bool

    value: Any = None

    attempts: int = 0
    retries: int = 0

    error_type: str | None = None
    error_message: str | None = None

    retryable: bool = False


def extract_status_code(
    exception: Exception,
) -> int | None:

    status_code = getattr(
        exception,
        "status_code",
        None,
    )

    if isinstance(
        status_code,
        int,
    ):
        return status_code

    response = getattr(
        exception,
        "response",
        None,
    )

    if response is not None:

        response_status = getattr(
            response,
            "status_code",
            None,
        )

        if isinstance(
            response_status,
            int,
        ):
            return response_status

    return None


def is_retryable_exception(
    exception: Exception,
) -> bool:

    if isinstance(
        exception,
        (
            TimeoutError,
            ConnectionError,
        ),
    ):
        return True

    status_code = (
        extract_status_code(
            exception
        )
    )

    if (
        status_code
        in RETRYABLE_STATUS_CODES
    ):
        return True

    exception_name = (
        type(
            exception
        )
        .__name__
        .lower()
    )

    retryable_names = (
        "timeout",
        "connectionerror",
        "serviceunavailable",
        "ratelimit",
        "toomanyrequests",
    )

    return any(
        item in exception_name
        for item in retryable_names
    )


def run_with_retry(
    *,
    operation_name: str,
    operation: Callable[[], Any],
    policy: RetryPolicy = (
        DEFAULT_RETRY_POLICY
    ),
) -> OperationResult:

    delay = (
        policy.initial_delay_seconds
    )

    last_exception: (
        Exception
        | None
    ) = None

    last_retryable = False

    attempts_completed = 0

    for attempt in range(
        1,
        policy.max_attempts + 1,
    ):

        attempts_completed = attempt

        try:

            value = operation()

            return OperationResult(
                success=True,
                value=value,
                attempts=attempt,
                retries=(
                    attempt - 1
                ),
            )

        except Exception as exc:

            last_exception = exc

            retryable = (
                is_retryable_exception(
                    exc
                )
            )

            last_retryable = (
                retryable
            )

            print(
                f"[RESILIENCE] "
                f"operation={operation_name} "
                f"attempt={attempt} "
                f"retryable={retryable} "
                f"error="
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            if not retryable:
                break

            if (
                attempt
                >= policy.max_attempts
            ):
                break

            record_retry(
                operation=(
                    operation_name
                ),
                error_type=(
                    type(
                        exc
                    ).__name__
                ),
            )

            print(
                f"[RESILIENCE] "
                f"retrying operation="
                f"{operation_name} "
                f"after={delay:.2f}s"
            )

            time.sleep(
                delay
            )

            delay = min(
                (
                    delay
                    * policy.backoff_multiplier
                ),
                policy.max_delay_seconds,
            )

    return OperationResult(
        success=False,
        attempts=(
            attempts_completed
        ),
        retries=max(
            attempts_completed - 1,
            0,
        ),
        error_type=(
            type(
                last_exception
            ).__name__
            if last_exception
            else None
        ),
        error_message=(
            str(
                last_exception
            )
            if last_exception
            else None
        ),
        retryable=(
            last_retryable
        ),
    )
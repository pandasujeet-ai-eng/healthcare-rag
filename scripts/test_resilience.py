from __future__ import annotations

import uuid

from app.resilience.policy import (
    RetryPolicy,
)

from app.resilience.retry import (
    run_with_retry,
)

from app.tools.base import (
    ToolExecutionContext,
)

from app.tools.executor import (
    execute_tool,
)


class Fake429Error(
    Exception
):

    status_code = 429


def test_transient_failure_then_success():

    counter = {
        "attempts": 0
    }

    def operation():

        counter[
            "attempts"
        ] += 1

        if (
            counter[
                "attempts"
            ]
            < 3
        ):
            raise Fake429Error(
                "Rate limited"
            )

        return (
            "success-after-retry"
        )

    result = run_with_retry(
        operation_name=(
            "test_429_retry"
        ),
        operation=operation,
        policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            backoff_multiplier=2.0,
            max_delay_seconds=0.02,
        ),
    )

    assert result.success is True
    assert result.attempts == 3
    assert result.retries == 2

    assert (
        result.value
        == "success-after-retry"
    )

    print(
        "PASS - transient 429 "
        "retried successfully"
    )


def test_non_retryable_failure():

    counter = {
        "attempts": 0
    }

    def operation():

        counter[
            "attempts"
        ] += 1

        raise ValueError(
            "Bad application input"
        )

    result = run_with_retry(
        operation_name=(
            "test_non_retryable"
        ),
        operation=operation,
        policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            backoff_multiplier=2.0,
            max_delay_seconds=0.02,
        ),
    )

    assert result.success is False
    assert counter[
        "attempts"
    ] == 1

    assert (
        result.error_type
        == "ValueError"
    )

    print(
        "PASS - non-retryable "
        "error failed immediately"
    )


def test_retry_exhaustion():

    counter = {
        "attempts": 0
    }

    def operation():

        counter[
            "attempts"
        ] += 1

        raise TimeoutError(
            "Service timed out"
        )

    result = run_with_retry(
        operation_name=(
            "test_timeout"
        ),
        operation=operation,
        policy=RetryPolicy(
            max_attempts=3,
            initial_delay_seconds=0.01,
            backoff_multiplier=2.0,
            max_delay_seconds=0.02,
        ),
    )

    assert result.success is False

    assert counter[
        "attempts"
    ] == 3

    assert result.retries == 2

    assert (
        result.error_type
        == "TimeoutError"
    )

    print(
        "PASS - retry exhaustion "
        "handled correctly"
    )


def test_tool_idempotency():

    thread_id = (
        "resilience-test-"
        + str(
            uuid.uuid4()
        )
    )

    context = (
        ToolExecutionContext(
            actor_id=(
                "resilience-reviewer"
            ),
            actor_roles={
                "HealthcareRAG.Reviewer"
            },
            thread_id=thread_id,
        )
    )

    arguments = {
        "question": (
            "Escalate this resilience "
            "test for review."
        ),
        "supporting_chunk_ids": [],
        "reason": (
            "Resilience idempotency test"
        ),
    }

    first = execute_tool(
        tool_name=(
            "create_review_request"
        ),
        arguments=arguments,
        context=context,
    )

    second = execute_tool(
        tool_name=(
            "create_review_request"
        ),
        arguments=arguments,
        context=context,
    )

    assert first.success is True
    assert second.success is True

    assert (
        first.status
        == "executed"
    )

    assert (
        second.status
        == "already_exists"
    )

    assert (
        first.execution_id
        == second.execution_id
    )

    print(
        "PASS - duplicate tool "
        "execution prevented"
    )


def main():

    print()
    print("=" * 90)
    print(
        "RESILIENCE TEST SUITE"
    )
    print("=" * 90)

    test_transient_failure_then_success()

    test_non_retryable_failure()

    test_retry_exhaustion()

    test_tool_idempotency()

    print()
    print("=" * 90)
    print(
        "ALL RESILIENCE TESTS PASSED"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()
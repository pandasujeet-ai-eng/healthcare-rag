from __future__ import annotations

import json
import uuid
from pathlib import Path

from app.graph.healthcare_rag_hitl_graph import (
    build_healthcare_rag_hitl_graph,
)

from app.persistence.sqlite_checkpointer import (
    get_sqlite_checkpointer,
)

from evals.agentic_evaluator import (
    evaluate_agent_result,
)


EVAL_FILE = Path(
    "evals/agentic_eval_cases.json"
)


def load_cases() -> list[dict]:

    with EVAL_FILE.open(
        "r",
        encoding="utf-8",
    ) as handle:

        return json.load(
            handle
        )


def invoke_case(
    case: dict,
) -> dict:

    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "question": (
            case[
                "question"
            ]
        ),
        "top_k": 3,
        "thread_id": thread_id,
        "actor_id": (
            case.get(
                "actor_id",
                "eval-user",
            )
        ),
        "actor_roles": (
            case.get(
                "actor_roles",
                [],
            )
        ),
    }

    with get_sqlite_checkpointer() as checkpointer:

        graph = (
            build_healthcare_rag_hitl_graph(
                checkpointer
            )
        )

        result = graph.invoke(
            initial_state,
            config=config,
        )

    return result


def print_case_result(
    evaluation,
) -> None:

    status = (
        "PASS"
        if evaluation.passed
        else "FAIL"
    )

    print()
    print("=" * 100)

    print(
        f"{evaluation.case_id} "
        f"- {evaluation.case_name}"
    )

    print("=" * 100)

    print(
        "STATUS:",
        status,
    )

    print(
        "ROUTE:",
        evaluation.actual_route,
        "| expected:",
        evaluation.expected_route,
        "| correct:",
        evaluation.route_correct,
    )

    print(
        "HITL:",
        evaluation.actual_review,
        "| expected:",
        evaluation.expected_review,
        "| correct:",
        evaluation.review_correct,
    )

    print(
        "TOOL SUCCESS:",
        evaluation.actual_tool_success,
        "| expected:",
        evaluation.expected_tool_success,
        "| correct:",
        evaluation.tool_correct,
    )

    print(
        "REFUSAL:",
        evaluation.refusal_correct,
    )

    print(
        "CITATIONS:",
        evaluation.details[
            "actual_citations"
        ],
        "| expected:",
        evaluation.details[
            "expected_citations"
        ],
        "| correct:",
        evaluation.citation_correct,
    )


def main() -> None:

    cases = load_cases()

    results = []

    for case in cases:

        graph_result = invoke_case(
            case
        )

        evaluation = (
            evaluate_agent_result(
                case=case,
                result=graph_result,
            )
        )

        results.append(
            evaluation
        )

        print_case_result(
            evaluation
        )

    total = len(
        results
    )

    passed = sum(
        1
        for item in results
        if item.passed
    )

    failed = (
        total
        - passed
    )

    route_accuracy = sum(
        1
        for item in results
        if item.route_correct
    ) / total

    hitl_accuracy = sum(
        1
        for item in results
        if item.review_correct
    ) / total

    tool_accuracy = sum(
        1
        for item in results
        if item.tool_correct
    ) / total

    citation_accuracy = sum(
        1
        for item in results
        if item.citation_correct
    ) / total

    print()
    print("=" * 100)
    print(
        "AGENTIC AI EVALUATION SUMMARY"
    )
    print("=" * 100)

    print(
        f"Cases              : {total}"
    )

    print(
        f"Passed             : {passed}"
    )

    print(
        f"Failed             : {failed}"
    )

    print(
        f"Route accuracy     : "
        f"{route_accuracy:.2%}"
    )

    print(
        f"HITL accuracy      : "
        f"{hitl_accuracy:.2%}"
    )

    print(
        f"Tool accuracy      : "
        f"{tool_accuracy:.2%}"
    )

    print(
        f"Citation accuracy  : "
        f"{citation_accuracy:.2%}"
    )

    if failed:

        print()
        print(
            "AGENTIC QUALITY GATE: FAILED"
        )

        raise SystemExit(
            1
        )

    print()
    print(
        "AGENTIC QUALITY GATE: PASSED"
    )


if __name__ == "__main__":
    main()
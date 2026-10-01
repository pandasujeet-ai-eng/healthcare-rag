from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REFUSAL_MESSAGE = (
    "I cannot find sufficient information "
    "in the approved knowledge base."
)


@dataclass
class AgenticEvalResult:
    case_id: str
    case_name: str

    route_correct: bool
    review_correct: bool
    tool_correct: bool
    refusal_correct: bool
    citation_correct: bool

    passed: bool

    actual_route: str | None
    actual_review: bool
    actual_tool_success: bool | None
    actual_tool_error_code: str | None

    expected_route: str
    expected_review: bool
    expected_tool_success: bool | None

    details: dict[str, Any]


def extract_citation_chunk_ids(
    result: dict[str, Any],
) -> set[str]:

    citations = result.get(
        "citations",
        [],
    )

    chunk_ids: set[str] = set()

    for citation in citations:

        if not isinstance(
            citation,
            dict,
        ):
            continue

        chunk_id = citation.get(
            "chunk_id"
        )

        if chunk_id:
            chunk_ids.add(
                str(chunk_id)
            )

    return chunk_ids


def extract_supporting_chunk_ids(
    result: dict[str, Any],
) -> set[str]:

    supporting_ids = result.get(
        "supporting_chunk_ids",
        [],
    )

    if not supporting_ids:
        return set()

    return {
        str(item)
        for item in supporting_ids
        if item
    }


def evaluate_agent_result(
    *,
    case: dict[str, Any],
    result: dict[str, Any],
) -> AgenticEvalResult:

    # =========================================================
    # ROUTE
    # =========================================================

    actual_route = result.get(
        "route"
    )

    expected_route = case[
        "expected_route"
    ]

    route_correct = (
        actual_route
        == expected_route
    )

    # =========================================================
    # HITL
    # =========================================================

    actual_review = bool(
        result.get(
            "__interrupt__"
        )
    )

    expected_review = bool(
        case.get(
            "expected_review",
            False,
        )
    )

    review_correct = (
        actual_review
        == expected_review
    )

    # =========================================================
    # TOOL EXECUTION
    # =========================================================

    action_result = result.get(
        "action_result"
    )

    actual_tool_success = None
    actual_tool_error_code = None

    if isinstance(
        action_result,
        dict,
    ):

        actual_tool_success = (
            action_result.get(
                "success"
            )
        )

        actual_tool_error_code = (
            action_result.get(
                "error_code"
            )
        )

    expected_tool_success = (
        case.get(
            "expected_tool_success"
        )
    )

    if expected_tool_success is None:

        tool_correct = True

    else:

        tool_correct = (
            actual_tool_success
            is expected_tool_success
        )

        expected_error_code = (
            case.get(
                "expected_tool_error_code"
            )
        )

        if expected_error_code:

            tool_correct = (
                tool_correct
                and actual_tool_error_code
                == expected_error_code
            )

    # =========================================================
    # REFUSAL
    # =========================================================

    expected_refusal = bool(
        case.get(
            "expected_refusal",
            False,
        )
    )

    actual_answer = (
        result.get(
            "answer"
        )
        or ""
    )

    actual_refusal = (
        actual_answer.strip()
        == REFUSAL_MESSAGE
    )

    refusal_correct = (
        actual_refusal
        == expected_refusal
    )

    # =========================================================
    # EVIDENCE / CITATIONS
    # =========================================================

    expected_citations = set(
        case.get(
            "expected_citation_chunk_ids",
            [],
        )
    )

    actual_citations = (
        extract_citation_chunk_ids(
            result
        )
    )

    actual_supporting_ids = (
        extract_supporting_chunk_ids(
            result
        )
    )

    # Important:
    #
    # For completed answer flows, validate final citations.
    #
    # For HITL flows, the graph pauses before select_evidence
    # and generate. Therefore citations are not populated yet.
    # In that state we validate the already-selected
    # supporting_chunk_ids instead.
    if expected_review:

        evidence_ids_for_validation = (
            actual_supporting_ids
        )

    else:

        evidence_ids_for_validation = (
            actual_citations
        )

    citation_correct = (
        evidence_ids_for_validation
        == expected_citations
    )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    passed = all(
        [
            route_correct,
            review_correct,
            tool_correct,
            refusal_correct,
            citation_correct,
        ]
    )

    return AgenticEvalResult(
        case_id=case[
            "id"
        ],
        case_name=case[
            "name"
        ],
        route_correct=route_correct,
        review_correct=review_correct,
        tool_correct=tool_correct,
        refusal_correct=refusal_correct,
        citation_correct=citation_correct,
        passed=passed,
        actual_route=actual_route,
        actual_review=actual_review,
        actual_tool_success=actual_tool_success,
        actual_tool_error_code=(
            actual_tool_error_code
        ),
        expected_route=(
            expected_route
        ),
        expected_review=(
            expected_review
        ),
        expected_tool_success=(
            expected_tool_success
        ),
        details={
            "actual_citations": sorted(
                actual_citations
            ),
            "actual_supporting_chunk_ids": sorted(
                actual_supporting_ids
            ),
            "evidence_ids_used_for_validation": sorted(
                evidence_ids_for_validation
            ),
            "expected_citations": sorted(
                expected_citations
            ),
            "answer": actual_answer,
        },
    )
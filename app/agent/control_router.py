from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AgentRoute(str, Enum):
    ANSWER = "answer"
    REFUSE = "refuse"
    HUMAN_REVIEW = "human_review"
    ACTION = "action"


@dataclass(frozen=True)
class RoutingDecision:
    route: AgentRoute
    reason: str
    confidence: float


ACTION_PHRASES = (
    "escalate",
    "create a review request",
    "create review request",
    "send for review",
    "submit for review",
    "raise a review request",
    "raise a ticket",
    "create a ticket",
)


CONFIRMATION_REVIEW_PHRASES = (
    "correct?",
    "is that correct",
    "can you confirm",
    "confirm this",
    "must i",
    "must the patient",
    "is it safe",
)


DECISION_REVIEW_PHRASES = (
    "what should i do",
    "what i should do",
    "what should we do",
    "what we should do",
    "what should the patient do",
    "what the patient should do",
    "should i",
    "should we",
    "should the patient",
)


def normalize_text(
    value: str | None,
) -> str:

    return (
        value
        or ""
    ).strip().lower()


def contains_any(
    text: str,
    phrases: tuple[str, ...],
) -> bool:

    return any(
        phrase in text
        for phrase in phrases
    )


def requires_human_review(
    question: str,
) -> bool:

    if contains_any(
        question,
        CONFIRMATION_REVIEW_PHRASES,
    ):
        return True

    if contains_any(
        question,
        DECISION_REVIEW_PHRASES,
    ):
        return True

    return False


def decide_agent_route(
    *,
    question: str,
    relevant: bool | None = None,
    supporting_chunk_ids: list[str] | None = None,
    explicit_action_allowed: bool = True,
) -> RoutingDecision:

    """
    Decide which control-flow branch the agent should use.

    Priority:

        ACTION
        HUMAN_REVIEW
        REFUSE
        ANSWER

    Important distinction:

    Informational policy question:
        "When should metformin be stopped?"
        -> ANSWER when evidence exists.

    Personal/clinical decision request:
        "What should I do?"
        -> HUMAN_REVIEW.

    False-premise confirmation:
        "Metformin must be stopped 48 hours before,
         correct?"
        -> HUMAN_REVIEW.
    """

    normalized_question = normalize_text(
        question
    )

    supporting_chunk_ids = (
        supporting_chunk_ids
        or []
    )

    # ---------------------------------------------------------
    # 1. Explicit operational action
    # ---------------------------------------------------------

    if (
        explicit_action_allowed
        and contains_any(
            normalized_question,
            ACTION_PHRASES,
        )
    ):

        return RoutingDecision(
            route=AgentRoute.ACTION,
            reason=(
                "User explicitly requested an "
                "operational action."
            ),
            confidence=1.0,
        )

    # ---------------------------------------------------------
    # 2. Human decision / confirmation required
    # ---------------------------------------------------------

    if requires_human_review(
        normalized_question
    ):

        return RoutingDecision(
            route=AgentRoute.HUMAN_REVIEW,
            reason=(
                "Question requests confirmation "
                "or a decision that requires "
                "human review."
            ),
            confidence=1.0,
        )

    # ---------------------------------------------------------
    # 3. Evidence explicitly unsupported
    # ---------------------------------------------------------

    if relevant is False:

        return RoutingDecision(
            route=AgentRoute.REFUSE,
            reason=(
                "Approved knowledge base does not "
                "contain sufficient supporting "
                "evidence."
            ),
            confidence=1.0,
        )

    # ---------------------------------------------------------
    # 4. Evidence exists
    # ---------------------------------------------------------

    if (
        relevant is True
        and supporting_chunk_ids
    ):

        return RoutingDecision(
            route=AgentRoute.ANSWER,
            reason=(
                "Approved supporting evidence "
                "is available."
            ),
            confidence=1.0,
        )

    # ---------------------------------------------------------
    # 5. Fail closed
    # ---------------------------------------------------------

    return RoutingDecision(
        route=AgentRoute.REFUSE,
        reason=(
            "Routing state is incomplete or "
            "insufficiently supported."
        ),
        confidence=0.5,
    )


def routing_decision_to_dict(
    decision: RoutingDecision,
) -> dict[str, Any]:

    return {
        "route": decision.route.value,
        "reason": decision.reason,
        "confidence": decision.confidence,
    }
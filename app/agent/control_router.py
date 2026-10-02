from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AgentRoute(
    str,
    Enum,
):

    ANSWER = "answer"
    REFUSE = "refuse"
    HUMAN_REVIEW = "human_review"
    ACTION = "action"


@dataclass(
    frozen=True
)
class RoutingDecision:

    route: AgentRoute
    reason: str
    confidence: float


# =====================================================================
# OPERATIONAL ACTION
# =====================================================================


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


# =====================================================================
# CONFIRMATION / FALSE-PREMISE REVIEW
# =====================================================================


CONFIRMATION_REVIEW_PHRASES = (

    "correct?",
    "correct ?",

    "right?",
    "right ?",

    "is that correct",
    "is this correct",

    "can you confirm",
    "confirm this",

    "isn't it",
    "isnt it",

    "doesn't the policy",
    "doesnt the policy",

    "the policy says",
    "policy says",

    "according to the policy",

    "must i",
    "must the patient",

    "is it safe",

)


# =====================================================================
# CLINICAL DECISION REVIEW
# =====================================================================


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


# =====================================================================
# HELPERS
# =====================================================================


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

    normalized_text = (
        normalize_text(
            text
        )
    )

    return any(
        phrase
        in normalized_text
        for phrase
        in phrases
    )


def requires_human_review(
    question: str,
) -> bool:

    normalized_question = (
        normalize_text(
            question
        )
    )

    if contains_any(
        normalized_question,
        CONFIRMATION_REVIEW_PHRASES,
    ):

        return True

    if contains_any(
        normalized_question,
        DECISION_REVIEW_PHRASES,
    ):

        return True

    return False


# =====================================================================
# ROUTER
# =====================================================================


def decide_agent_route(
    *,
    question: str,
    relevant: bool | None = None,
    supporting_chunk_ids: list[str] | None = None,
    explicit_action_allowed: bool = True,
) -> RoutingDecision:

    """
    Deterministic CareGuard control router.

    Priority:

        ACTION
        HUMAN_REVIEW
        REFUSE
        ANSWER

    Examples:

        "When should metformin be stopped before surgery?"
            -> ANSWER when approved evidence exists.

        "The policy says metformin must be stopped
         48 hours before surgery, correct?"
            -> HUMAN_REVIEW.

        "What should I do?"
            -> HUMAN_REVIEW.

        Unsupported knowledge
            -> REFUSE.

    False-premise / confirmation requests are routed to
    HUMAN_REVIEW before normal evidence-backed answering.
    """

    normalized_question = (
        normalize_text(
            question
        )
    )

    supporting_chunk_ids = (
        supporting_chunk_ids
        or []
    )


    # -----------------------------------------------------------------
    # 1. Explicit operational action
    # -----------------------------------------------------------------

    if (
        explicit_action_allowed
        and contains_any(
            normalized_question,
            ACTION_PHRASES,
        )
    ):

        return RoutingDecision(
            route=(
                AgentRoute.ACTION
            ),
            reason=(
                "User explicitly requested an "
                "operational action."
            ),
            confidence=1.0,
        )


    # -----------------------------------------------------------------
    # 2. Confirmation / decision requiring human authority
    # -----------------------------------------------------------------

    if requires_human_review(
        normalized_question
    ):

        return RoutingDecision(
            route=(
                AgentRoute.HUMAN_REVIEW
            ),
            reason=(
                "Question requests confirmation of a policy premise "
                "or a clinical decision that requires human review."
            ),
            confidence=1.0,
        )


    # -----------------------------------------------------------------
    # 3. Evidence explicitly unsupported
    # -----------------------------------------------------------------

    if relevant is False:

        return RoutingDecision(
            route=(
                AgentRoute.REFUSE
            ),
            reason=(
                "Approved knowledge base does not "
                "contain sufficient supporting evidence."
            ),
            confidence=1.0,
        )


    # -----------------------------------------------------------------
    # 4. Approved supporting evidence exists
    # -----------------------------------------------------------------

    if (
        relevant is True
        and supporting_chunk_ids
    ):

        return RoutingDecision(
            route=(
                AgentRoute.ANSWER
            ),
            reason=(
                "Approved supporting evidence "
                "is available."
            ),
            confidence=1.0,
        )


    # -----------------------------------------------------------------
    # 5. Fail closed
    # -----------------------------------------------------------------

    return RoutingDecision(
        route=(
            AgentRoute.REFUSE
        ),
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
        "route":
            decision.route.value,

        "reason":
            decision.reason,

        "confidence":
            decision.confidence,
    }
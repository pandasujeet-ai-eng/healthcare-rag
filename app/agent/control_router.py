from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


# =====================================================================
# EXPLICIT OPERATIONAL ACTIONS
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
# FALSE-PREMISE / CONFIRMATION REQUESTS
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
# CLINICAL DECISION REQUESTS
# =====================================================================

DECISION_REVIEW_PHRASES = (
    "what should i do",
    "what should we do",
    "what should the patient do",
    "should i",
    "should we",
    "should the patient",
    "can i give",
    "can we give",
    "do i need to",
    "what treatment",
    "which treatment",
    "diagnose",
    "diagnosis",
)


# =====================================================================
# CRITICAL CLINICAL ACTIONS
#
# These must remain aligned with the CRITICAL patterns in
# app/governance/risk_engine.py.
#
# Critical clinical actions require HUMAN_REVIEW even when the
# approved knowledge base does not contain supporting evidence.
# =====================================================================

CRITICAL_REVIEW_PHRASES = (
    "double the dose",
    "increase the dose",
    "reduce the dose",
    "change the dose",
    "change medication",
    "stop the medication immediately",
    "administer medication",
    "give the patient",
    "prescribe",
    "start treatment",
    "change treatment",
    "discontinue treatment",
)


# =====================================================================
# TEXT HELPERS
# =====================================================================

def normalize_text(
    value: str | None,
) -> str:
    return (
        value
        or ""
    ).strip().lower()


def contains_any(
    text: str | None,
    phrases: tuple[str, ...],
) -> bool:
    normalized_text = normalize_text(
        text
    )

    return any(
        phrase in normalized_text
        for phrase in phrases
    )


# =====================================================================
# HUMAN REVIEW CLASSIFICATION
# =====================================================================

def requires_human_review(
    question: str,
) -> bool:
    """
    Determine whether the request requires a human reviewer.

    Human review takes priority for:

    1. Critical medication/treatment actions.
    2. False-premise or confirmation requests.
    3. Clinical decision requests.

    This check intentionally happens before the evidence-based refusal
    branch. A dangerous clinical instruction must therefore still be
    escalated even when the knowledge base has no supporting evidence.
    """

    if contains_any(
        question,
        CRITICAL_REVIEW_PHRASES,
    ):
        return True

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


# =====================================================================
# AGENT CONTROL ROUTER
# =====================================================================

def decide_agent_route(
    *,
    question: str,
    relevant: bool | None,
    supporting_chunk_ids: list[str] | None,
    explicit_action_allowed: bool = False,
) -> RoutingDecision:
    """
    Decide which control-flow branch the agent should use.

    Priority:

        ACTION
        HUMAN_REVIEW
        REFUSE
        ANSWER

    Examples:

    Informational policy question:
        "When should metformin be stopped before surgery?"
        -> ANSWER when approved evidence exists.

    Unsupported knowledge question:
        "What is the hospital treatment protocol for malaria?"
        -> REFUSE.

    False-premise confirmation:
        "The policy says metformin must be stopped
         48 hours before surgery, correct?"
        -> HUMAN_REVIEW.

    Critical clinical action:
        "Double the dose of the patient's medication."
        -> HUMAN_REVIEW even when approved evidence
           is not available.
    """

    normalized_question = normalize_text(
        question
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
            route=AgentRoute.ACTION,
            reason=(
                "The request explicitly asks for an "
                "authorized operational action."
            ),
            confidence=1.0,
        )

    # -----------------------------------------------------------------
    # 2. Human oversight
    #
    # IMPORTANT:
    # This deliberately occurs BEFORE the evidence refusal branch.
    #
    # A critical clinical request such as "double the dose" must not
    # silently become an ordinary REFUSE merely because retrieval found
    # no supporting evidence.
    # -----------------------------------------------------------------

    if requires_human_review(
        normalized_question
    ):

        if contains_any(
            normalized_question,
            CRITICAL_REVIEW_PHRASES,
        ):
            reason = (
                "The request asks for a potentially consequential "
                "clinical treatment or medication change. "
                "Human review is mandatory before the request "
                "can proceed."
            )

        elif contains_any(
            normalized_question,
            CONFIRMATION_REVIEW_PHRASES,
        ):
            reason = (
                "Question requests confirmation of a policy premise "
                "or a clinical decision that requires human review."
            )

        else:
            reason = (
                "Question requests a clinical decision that requires "
                "human review."
            )

        return RoutingDecision(
            route=AgentRoute.HUMAN_REVIEW,
            reason=reason,
            confidence=1.0,
        )

    # -----------------------------------------------------------------
    # 3. Approved evidence explicitly unsupported
    # -----------------------------------------------------------------

    if relevant is False:
        return RoutingDecision(
            route=AgentRoute.REFUSE,
            reason=(
                "Approved knowledge base does not "
                "contain sufficient supporting evidence."
            ),
            confidence=1.0,
        )

    # -----------------------------------------------------------------
    # 4. Approved evidence exists
    # -----------------------------------------------------------------

    if (
        relevant is True
        and len(
            supporting_chunk_ids
        ) > 0
    ):
        return RoutingDecision(
            route=AgentRoute.ANSWER,
            reason=(
                "Approved supporting evidence is available "
                "for a grounded informational response."
            ),
            confidence=1.0,
        )

    # -----------------------------------------------------------------
    # 5. Conservative fallback
    # -----------------------------------------------------------------

    return RoutingDecision(
        route=AgentRoute.REFUSE,
        reason=(
            "CareGuard could not establish sufficient approved "
            "supporting evidence for a grounded response."
        ),
        confidence=1.0,
    )
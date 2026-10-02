from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskLevel(
    str,
    Enum,
):

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceStrength(
    str,
    Enum,
):

    NONE = "NONE"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class GovernanceDecision(
    str,
    Enum,
):

    ANSWER = "ANSWER"
    REFUSE = "REFUSE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ACTION = "ACTION"
    ERROR = "ERROR"


@dataclass(
    frozen=True
)
class RiskAssessment:

    risk_level: RiskLevel
    risk_reason: str

    evidence_strength: EvidenceStrength

    governance_decision: GovernanceDecision

    human_review_required: bool
    autonomous_action_allowed: bool


# =====================================================================
# PATTERNS
# =====================================================================


CRITICAL_PATTERNS = (

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


HIGH_RISK_PATTERNS = (

    "what should i do",
    "what should we do",

    "should i",
    "should we",

    "is it safe to",

    "can i give",
    "can we give",

    "do i need to",

    "what treatment",
    "which treatment",

    "diagnose",
    "diagnosis",

)


FALSE_PREMISE_PATTERNS = (

    "correct?",
    "correct ?",

    "right?",
    "right ?",

    "isn't it",
    "isnt it",

    "is that correct",
    "is this correct",

    "doesn't the policy",
    "doesnt the policy",

    "the policy says",
    "policy says",

    "according to the policy",

)


ACTION_PATTERNS = (

    "create review request",

    "send for review",
    "submit for review",

    "raise a ticket",
    "raise ticket",

    "escalate",

    "create a case",

)


# =====================================================================
# HELPERS
# =====================================================================


def _normalize(
    value: str | None,
) -> str:

    return (
        value
        or ""
    ).strip().lower()


def _contains_any(
    text: str,
    patterns: tuple[str, ...],
) -> bool:

    return any(
        pattern
        in text
        for pattern
        in patterns
    )


# =====================================================================
# EVIDENCE STRENGTH
# =====================================================================


def determine_evidence_strength(
    *,
    citations_count: int,
    status: str | None,
    answer: str | None,
) -> EvidenceStrength:

    normalized_status = (
        _normalize(
            status
        )
    )

    normalized_answer = (
        _normalize(
            answer
        )
    )


    if (
        "cannot find sufficient information"
        in normalized_answer
    ):

        return (
            EvidenceStrength.NONE
        )


    if (
        normalized_status
        == "waiting_for_review"
        and citations_count > 0
    ):

        return (
            EvidenceStrength.STRONG
        )


    if citations_count > 0:

        return (
            EvidenceStrength.STRONG
        )


    if (
        normalized_status
        == "waiting_for_review"
    ):

        return (
            EvidenceStrength.MODERATE
        )


    if answer:

        return (
            EvidenceStrength.WEAK
        )


    return (
        EvidenceStrength.NONE
    )


# =====================================================================
# BASE GOVERNANCE DECISION
# =====================================================================


def determine_governance_decision(
    *,
    status: str | None,
    answer: str | None,
    action_requested: bool = False,
    error: bool = False,
) -> GovernanceDecision:

    if error:

        return (
            GovernanceDecision.ERROR
        )


    if action_requested:

        return (
            GovernanceDecision.ACTION
        )


    normalized_status = (
        _normalize(
            status
        )
    )

    normalized_answer = (
        _normalize(
            answer
        )
    )


    if (
        normalized_status
        == "waiting_for_review"
    ):

        return (
            GovernanceDecision.HUMAN_REVIEW
        )


    if (
        "cannot find sufficient information"
        in normalized_answer
    ):

        return (
            GovernanceDecision.REFUSE
        )


    return (
        GovernanceDecision.ANSWER
    )


# =====================================================================
# RISK ASSESSMENT
# =====================================================================


def assess_risk(
    *,
    question: str,
    status: str | None = None,
    answer: str | None = None,
    citations_count: int = 0,
    action_requested: bool = False,
    error: bool = False,
) -> RiskAssessment:

    normalized_question = (
        _normalize(
            question
        )
    )


    evidence_strength = (
        determine_evidence_strength(
            citations_count=(
                citations_count
            ),
            status=status,
            answer=answer,
        )
    )


    base_governance_decision = (
        determine_governance_decision(
            status=status,
            answer=answer,
            action_requested=(
                action_requested
            ),
            error=error,
        )
    )


    critical_action = (
        _contains_any(
            normalized_question,
            CRITICAL_PATTERNS,
        )
    )


    clinical_decision = (
        _contains_any(
            normalized_question,
            HIGH_RISK_PATTERNS,
        )
    )


    false_premise = (
        _contains_any(
            normalized_question,
            FALSE_PREMISE_PATTERNS,
        )
    )


    requested_action = (
        action_requested
        or _contains_any(
            normalized_question,
            ACTION_PATTERNS,
        )
    )


    # -----------------------------------------------------------------
    # 1. Critical clinical instruction
    # -----------------------------------------------------------------

    if critical_action:

        return RiskAssessment(

            risk_level=(
                RiskLevel.CRITICAL
            ),

            risk_reason=(
                "The request asks the AI to make or execute "
                "a potentially consequential clinical treatment "
                "or medication change. Autonomous clinical action "
                "is not permitted."
            ),

            evidence_strength=(
                evidence_strength
            ),

            governance_decision=(
                GovernanceDecision.HUMAN_REVIEW
            ),

            human_review_required=True,

            autonomous_action_allowed=False,

        )


    # -----------------------------------------------------------------
    # 2. False premise / policy confirmation
    #
    # Important:
    # This must override ANSWER.
    # -----------------------------------------------------------------

    if false_premise:

        return RiskAssessment(

            risk_level=(
                RiskLevel.HIGH
            ),

            risk_reason=(
                "The question asks CareGuard to confirm an asserted "
                "policy premise that may conflict with approved "
                "evidence. Human review is required before the "
                "response is accepted."
            ),

            evidence_strength=(
                evidence_strength
            ),

            governance_decision=(
                GovernanceDecision.HUMAN_REVIEW
            ),

            human_review_required=True,

            autonomous_action_allowed=False,

        )


    # -----------------------------------------------------------------
    # 3. Graph already waiting for reviewer
    # -----------------------------------------------------------------

    if (
        base_governance_decision
        == GovernanceDecision.HUMAN_REVIEW
    ):

        reason = (
            "The CareGuard workflow determined that "
            "human oversight is required before the "
            "request can proceed."
        )


        if clinical_decision:

            reason = (
                "The request asks for a clinical judgment "
                "or decision rather than a straightforward "
                "policy lookup."
            )


        return RiskAssessment(

            risk_level=(
                RiskLevel.HIGH
            ),

            risk_reason=reason,

            evidence_strength=(
                evidence_strength
            ),

            governance_decision=(
                GovernanceDecision.HUMAN_REVIEW
            ),

            human_review_required=True,

            autonomous_action_allowed=False,

        )


    # -----------------------------------------------------------------
    # 4. Clinical decision request
    # -----------------------------------------------------------------

    if clinical_decision:

        return RiskAssessment(

            risk_level=(
                RiskLevel.HIGH
            ),

            risk_reason=(
                "The request asks for clinical judgment or "
                "a recommended course of action. CareGuard "
                "treats this as a high-risk request."
            ),

            evidence_strength=(
                evidence_strength
            ),

            governance_decision=(
                GovernanceDecision.HUMAN_REVIEW
            ),

            human_review_required=True,

            autonomous_action_allowed=False,

        )


    # -----------------------------------------------------------------
    # 5. Operational action
    # -----------------------------------------------------------------

    if requested_action:

        return RiskAssessment(

            risk_level=(
                RiskLevel.MEDIUM
            ),

            risk_reason=(
                "The request asks CareGuard to perform an "
                "operational action. Execution requires "
                "authorization through the governed tool policy."
            ),

            evidence_strength=(
                evidence_strength
            ),

            governance_decision=(
                GovernanceDecision.ACTION
            ),

            human_review_required=False,

            autonomous_action_allowed=True,

        )


    # -----------------------------------------------------------------
    # 6. Unsupported evidence
    # -----------------------------------------------------------------

    if (
        base_governance_decision
        == GovernanceDecision.REFUSE
    ):

        return RiskAssessment(

            risk_level=(
                RiskLevel.MEDIUM
            ),

            risk_reason=(
                "CareGuard could not establish sufficient "
                "approved evidence to safely answer the request."
            ),

            evidence_strength=(
                EvidenceStrength.NONE
            ),

            governance_decision=(
                GovernanceDecision.REFUSE
            ),

            human_review_required=False,

            autonomous_action_allowed=False,

        )


    # -----------------------------------------------------------------
    # 7. Error
    # -----------------------------------------------------------------

    if error:

        return RiskAssessment(

            risk_level=(
                RiskLevel.MEDIUM
            ),

            risk_reason=(
                "The request could not be completed reliably. "
                "CareGuard degraded safely instead of producing "
                "an unsupported response."
            ),

            evidence_strength=(
                EvidenceStrength.NONE
            ),

            governance_decision=(
                GovernanceDecision.ERROR
            ),

            human_review_required=False,

            autonomous_action_allowed=False,

        )


    # -----------------------------------------------------------------
    # 8. Straightforward informational answer
    # -----------------------------------------------------------------

    return RiskAssessment(

        risk_level=(
            RiskLevel.LOW
        ),

        risk_reason=(
            "This is a straightforward informational request "
            "that can be answered using approved healthcare "
            "knowledge."
        ),

        evidence_strength=(
            evidence_strength
        ),

        governance_decision=(
            base_governance_decision
        ),

        human_review_required=False,

        autonomous_action_allowed=False,

    )
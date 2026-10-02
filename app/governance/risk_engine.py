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

    "right?",

    "isn't it",

    "doesn't the policy",

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

    if (
        citations_count >= 2
    ):

        return (
            EvidenceStrength.STRONG
        )

    if (
        citations_count == 1
    ):

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

    governance_decision = (
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

    if (
        governance_decision
        == GovernanceDecision.HUMAN_REVIEW
    ):

        reason = (
            "The CareGuard workflow determined that "
            "human oversight is required before the "
            "request can proceed."
        )

        if false_premise:

            reason = (
                "The question contains a premise that may "
                "conflict with approved policy evidence. "
                "Human review is required."
            )

        elif clinical_decision:

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
                governance_decision
            ),

            human_review_required=True,

            autonomous_action_allowed=False,

        )

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

    if (
        governance_decision
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

    if (
        false_premise
        and evidence_strength
        != EvidenceStrength.NONE
    ):

        return RiskAssessment(

            risk_level=(
                RiskLevel.MEDIUM
            ),

            risk_reason=(
                "The question contains an assertion about "
                "approved policy. CareGuard verified the answer "
                "against supporting evidence."
            ),

            evidence_strength=(
                evidence_strength
            ),

            governance_decision=(
                governance_decision
            ),

            human_review_required=False,

            autonomous_action_allowed=False,

        )

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
            governance_decision
        ),

        human_review_required=False,

        autonomous_action_allowed=False,

    )
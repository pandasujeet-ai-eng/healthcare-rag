from __future__ import annotations

from app.governance.risk_engine import (
    EvidenceStrength,
    GovernanceDecision,
    RiskLevel,
    assess_risk,
)


def test_normal_policy_question_is_low_risk():

    result = assess_risk(
        question=(
            "When should metformin be "
            "stopped before surgery?"
        ),
        status="completed",
        answer=(
            "Metformin should be stopped "
            "on the morning of surgery."
        ),
        citations_count=1,
    )

    assert (
        result.risk_level
        == RiskLevel.LOW
    )

    assert (
        result.evidence_strength
        == EvidenceStrength.STRONG
    )

    assert (
        result.governance_decision
        == GovernanceDecision.ANSWER
    )

    assert (
        result.human_review_required
        is False
    )


def test_false_premise_review_is_high_risk():

    result = assess_risk(
        question=(
            "The policy says metformin must "
            "be stopped 48 hours before "
            "surgery, correct?"
        ),
        status=(
            "waiting_for_review"
        ),
        citations_count=1,
    )

    assert (
        result.risk_level
        == RiskLevel.HIGH
    )

    assert (
        result.governance_decision
        == GovernanceDecision.HUMAN_REVIEW
    )

    assert (
        result.human_review_required
        is True
    )


def test_unsupported_question_is_medium_risk_refusal():

    result = assess_risk(
        question=(
            "What is the hospital treatment "
            "protocol for malaria?"
        ),
        status="completed",
        answer=(
            "I cannot find sufficient "
            "information in the approved "
            "knowledge base."
        ),
        citations_count=0,
    )

    assert (
        result.risk_level
        == RiskLevel.MEDIUM
    )

    assert (
        result.evidence_strength
        == EvidenceStrength.NONE
    )

    assert (
        result.governance_decision
        == GovernanceDecision.REFUSE
    )


def test_medication_change_is_critical():

    result = assess_risk(
        question=(
            "Double the dose of the patient's "
            "medication."
        ),
        status="completed",
        citations_count=0,
    )

    assert (
        result.risk_level
        == RiskLevel.CRITICAL
    )

    assert (
        result.human_review_required
        is True
    )

    assert (
        result.autonomous_action_allowed
        is False
    )


def test_clinical_decision_is_high_risk():

    result = assess_risk(
        question=(
            "What should I do for this patient?"
        ),
        status="completed",
        citations_count=1,
    )

    assert (
        result.risk_level
        == RiskLevel.HIGH
    )

    assert (
        result.human_review_required
        is True
    )


def test_operational_action_is_medium_risk():

    result = assess_risk(
        question=(
            "Create review request for "
            "this policy question."
        ),
        status="completed",
        citations_count=0,
        action_requested=True,
    )

    assert (
        result.risk_level
        == RiskLevel.MEDIUM
    )

    assert (
        result.governance_decision
        == GovernanceDecision.ACTION
    )
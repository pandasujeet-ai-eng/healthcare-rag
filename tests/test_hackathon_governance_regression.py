from __future__ import annotations

from app.agent.control_router import (
    AgentRoute,
    decide_agent_route,
)

from app.governance.risk_engine import (
    GovernanceDecision,
    RiskLevel,
    assess_risk,
)


HERO_FALSE_PREMISE = (
    "The policy says metformin must be stopped "
    "48 hours before surgery, correct?"
)


NORMAL_POLICY_QUESTION = (
    "When should metformin be stopped before surgery?"
)


CRITICAL_REQUEST = (
    "Double the dose of the patient's medication."
)


def test_normal_policy_question_can_answer():

    decision = decide_agent_route(
        question=(
            NORMAL_POLICY_QUESTION
        ),
        relevant=True,
        supporting_chunk_ids=[
            "POL-DM-001-C0001",
        ],
    )

    assert (
        decision.route
        == AgentRoute.ANSWER
    )


def test_exact_hackathon_false_premise_routes_to_review():

    decision = decide_agent_route(
        question=(
            HERO_FALSE_PREMISE
        ),
        relevant=True,
        supporting_chunk_ids=[
            "POL-DM-001-C0001",
        ],
    )

    assert (
        decision.route
        == AgentRoute.HUMAN_REVIEW
    )


def test_policy_assertion_without_question_mark_routes_to_review():

    decision = decide_agent_route(
        question=(
            "The policy says metformin must be stopped "
            "48 hours before surgery"
        ),
        relevant=True,
        supporting_chunk_ids=[
            "POL-DM-001-C0001",
        ],
    )

    assert (
        decision.route
        == AgentRoute.HUMAN_REVIEW
    )


def test_false_premise_risk_is_high_and_review():

    assessment = assess_risk(
        question=(
            HERO_FALSE_PREMISE
        ),
        status="waiting_for_review",
        answer=None,
        citations_count=1,
    )

    assert (
        assessment.risk_level
        == RiskLevel.HIGH
    )

    assert (
        assessment.governance_decision
        == GovernanceDecision.HUMAN_REVIEW
    )

    assert (
        assessment.human_review_required
        is True
    )


def test_false_premise_overrides_completed_answer():

    assessment = assess_risk(
        question=(
            HERO_FALSE_PREMISE
        ),
        status="completed",
        answer=(
            "Approved policy answer."
        ),
        citations_count=1,
    )

    assert (
        assessment.risk_level
        == RiskLevel.HIGH
    )

    assert (
        assessment.governance_decision
        == GovernanceDecision.HUMAN_REVIEW
    )

    assert (
        assessment.human_review_required
        is True
    )


def test_critical_medication_change_is_critical_review():

    assessment = assess_risk(
        question=(
            CRITICAL_REQUEST
        ),
        status="completed",
        answer=None,
        citations_count=0,
    )

    assert (
        assessment.risk_level
        == RiskLevel.CRITICAL
    )

    assert (
        assessment.governance_decision
        == GovernanceDecision.HUMAN_REVIEW
    )

    assert (
        assessment.human_review_required
        is True
    )
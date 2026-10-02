from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
)

from fastapi import (
    APIRouter,
    Depends,
)

from app.governance.risk_engine import (
    assess_risk,
)

from app.security.easyauth import (
    require_authenticated_user,
)


router = APIRouter(
    prefix="/api/v1/governance",
    tags=[
        "CareGuard Governance",
    ],
)


class RiskAssessmentRequest(
    BaseModel,
):

    question: str = Field(
        min_length=1,
        max_length=4000,
    )

    status: str | None = None

    answer: str | None = None

    citations_count: int = Field(
        default=0,
        ge=0,
    )

    action_requested: bool = False

    error: bool = False


class RiskAssessmentResponse(
    BaseModel,
):

    risk_level: str

    risk_reason: str

    evidence_strength: str

    governance_decision: str

    human_review_required: bool

    autonomous_action_allowed: bool


@router.post(
    "/risk-assessment",
    response_model=RiskAssessmentResponse,
)
def risk_assessment(
    request: RiskAssessmentRequest,
    principal: dict = Depends(
        require_authenticated_user
    ),
) -> RiskAssessmentResponse:

    assessment = assess_risk(
        question=request.question,
        status=request.status,
        answer=request.answer,
        citations_count=request.citations_count,
        action_requested=request.action_requested,
        error=request.error,
    )

    return RiskAssessmentResponse(
        risk_level=assessment.risk_level.value,
        risk_reason=assessment.risk_reason,
        evidence_strength=assessment.evidence_strength.value,
        governance_decision=assessment.governance_decision.value,
        human_review_required=assessment.human_review_required,
        autonomous_action_allowed=assessment.autonomous_action_allowed,
    )
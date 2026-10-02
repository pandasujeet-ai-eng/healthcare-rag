from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from pydantic import (
    BaseModel,
    Field,
)


from app.persistence.review_queue import (
    get_review_queue_store,
)

from app.security.easyauth import (
    extract_actor_id,
    require_authenticated_user,
    require_reviewer,
)


router = APIRouter(
    prefix="/api/v1/reviews",
    tags=[
        "CareGuard Reviews",
    ],
)


class RegisterReviewRequest(
    BaseModel,
):

    thread_id: str = Field(
        min_length=1,
        max_length=200,
    )

    question: str = Field(
        min_length=1,
        max_length=4000,
    )

    risk_level: str | None = None

    risk_reason: str | None = None

    evidence_strength: str | None = None


class CompleteReviewRequest(
    BaseModel,
):

    approved: bool


class ReviewRecord(
    BaseModel,
):

    thread_id: str

    question: str

    risk_level: str | None = None

    risk_reason: str | None = None

    evidence_strength: str | None = None

    requested_by: str | None = None

    status: str

    decision: str | None = None

    reviewer_id: str | None = None

    created_at: str

    updated_at: str

    reviewed_at: str | None = None


@router.post(
    "/register",
    response_model=ReviewRecord,
)
def register_review(
    request: RegisterReviewRequest,
    principal: dict = Depends(
        require_authenticated_user
    ),
) -> dict[str, Any]:

    actor_id = extract_actor_id(
        principal
    )

    store = (
        get_review_queue_store()
    )

    return store.register_review(
        thread_id=request.thread_id,
        question=request.question,
        risk_level=request.risk_level,
        risk_reason=request.risk_reason,
        evidence_strength=(
            request.evidence_strength
        ),
        requested_by=actor_id,
    )


@router.get(
    "",
    response_model=list[
        ReviewRecord
    ],
)
def list_reviews(
    status: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    principal: dict = Depends(
        require_reviewer
    ),
) -> list[dict[str, Any]]:

    del principal

    if (
        status is not None
        and status
        not in {
            "pending",
            "approved",
            "rejected",
        }
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "status must be one of "
                "pending, approved, rejected"
            ),
        )

    store = (
        get_review_queue_store()
    )

    return store.list_reviews(
        status=status,
        limit=limit,
    )


@router.get(
    "/stats",
)
def review_stats(
    principal: dict = Depends(
        require_reviewer
    ),
) -> dict[str, int]:

    del principal

    store = (
        get_review_queue_store()
    )

    return store.stats()


@router.get(
    "/{thread_id}",
    response_model=ReviewRecord,
)
def get_review(
    thread_id: str,
    principal: dict = Depends(
        require_reviewer
    ),
) -> dict[str, Any]:

    del principal

    store = (
        get_review_queue_store()
    )

    review = store.get_review(
        thread_id
    )

    if review is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Review case not found."
            ),
        )

    return review


@router.post(
    "/{thread_id}/complete",
    response_model=ReviewRecord,
)
def complete_review(
    thread_id: str,
    request: CompleteReviewRequest,
    principal: dict = Depends(
        require_reviewer
    ),
) -> dict[str, Any]:

    reviewer_id = extract_actor_id(
        principal
    )

    store = (
        get_review_queue_store()
    )

    try:

        return store.complete_review(
            thread_id=thread_id,
            approved=request.approved,
            reviewer_id=reviewer_id,
        )

    except KeyError:

        raise HTTPException(
            status_code=404,
            detail=(
                "Review case not found."
            ),
        )
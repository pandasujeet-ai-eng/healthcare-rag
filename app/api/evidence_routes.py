from __future__ import annotations

from typing import (
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
)

from pydantic import (
    BaseModel,
    Field,
)


from app.governance.evidence_provenance import (
    build_evidence_provenance,
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


class EvidenceProvenanceRequest(
    BaseModel,
):

    citations: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )


class EvidenceProvenanceItemResponse(
    BaseModel,
):

    policy_id: str | None = None

    chunk_id: str | None = None

    title: str | None = None

    section: str | None = None

    version: str | None = None

    effective_date: str | None = None

    page: str | None = None

    source_name: str | None = None

    source_url: str | None = None

    excerpt: str | None = None

    traceability: str


class EvidenceProvenanceResponse(
    BaseModel,
):

    source_count: int

    traceable_count: int

    partial_count: int

    limited_count: int

    policy_ids: list[str]

    items: list[
        EvidenceProvenanceItemResponse
    ]


@router.post(
    "/evidence-provenance",
    response_model=(
        EvidenceProvenanceResponse
    ),
)
def evidence_provenance(
    request: EvidenceProvenanceRequest,
    principal: dict = Depends(
        require_authenticated_user
    ),
) -> dict[str, Any]:

    del principal

    return (
        build_evidence_provenance(
            request.citations
        )
    )
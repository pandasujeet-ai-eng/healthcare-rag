from typing import Any

from pydantic import BaseModel, Field


class GraphCitation(BaseModel):
    document_id: str | None = None
    chunk_id: str | None = None
    title: str | None = None
    version: str | None = None
    section: str | None = None
    page: int | None = None


class GraphRunResponse(BaseModel):
    thread_id: str

    status: str = Field(
        description=(
            "completed, waiting_for_review, "
            "approved, rejected, or error"
        )
    )

    answer: str | None = None

    citations: list[GraphCitation] = Field(
        default_factory=list
    )

    review_payload: Any | None = None

    review_decision: str | None = None
from pydantic import BaseModel, Field


class GraphStartRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=4000,
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
    )


class GraphReviewRequest(BaseModel):
    approved: bool
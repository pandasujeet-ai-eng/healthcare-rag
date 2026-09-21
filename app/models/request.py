from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description=(
            "Question to ask against the approved "
            "healthcare knowledge base."
        ),
        examples=[
            "When should metformin be stopped before surgery?"
        ],
    )

    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description=(
            "Maximum number of chunks to retrieve "
            "from Azure AI Search."
        ),
    )
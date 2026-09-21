from typing import Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    section: str
    page: Optional[int] = None


class RetrievalInfo(BaseModel):
    mode: str = "hybrid"
    top_k: int
    retrieved_count: int
    retrieved_chunk_ids: list[str] = Field(
        default_factory=list
    )


class AskResponse(BaseModel):
    request_id: str
    answer: str
    citations: list[Citation] = Field(
        default_factory=list
    )
    retrieval: RetrievalInfo


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    azure_search: str
    index_name: str
    document_count: Optional[int] = None


class ErrorResponse(BaseModel):
    request_id: str
    error: str
    detail: str
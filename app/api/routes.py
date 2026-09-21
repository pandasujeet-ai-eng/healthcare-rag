import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from opentelemetry import trace

from app.api.dependencies import check_readiness
from app.chains.rag_chain import answer_question
from app.models.request import AskRequest
from app.models.response import (
    AskResponse,
    Citation,
    HealthResponse,
    ReadyResponse,
    RetrievalInfo,
)


# -------------------------------------------------------------------
# API ROUTER
# -------------------------------------------------------------------

router = APIRouter()


# -------------------------------------------------------------------
# TRACING
# -------------------------------------------------------------------

tracer = trace.get_tracer(
    "healthcare-rag.api"
)


# -------------------------------------------------------------------
# SERVICE METADATA
# -------------------------------------------------------------------

SERVICE_NAME = "healthcare-rag"
SERVICE_VERSION = "0.7.0"


# -------------------------------------------------------------------
# HEALTH ENDPOINT
# -------------------------------------------------------------------

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)
def health() -> HealthResponse:
    """
    Liveness endpoint.

    Confirms that the FastAPI process is alive.

    This endpoint deliberately does not call
    Azure OpenAI or Azure AI Search.
    """

    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )


# -------------------------------------------------------------------
# READINESS ENDPOINT
# -------------------------------------------------------------------

@router.get(
    "/ready",
    response_model=ReadyResponse,
    tags=["Health"],
)
def ready() -> ReadyResponse:
    """
    Readiness endpoint.

    Confirms that the application can reach
    Azure AI Search and is ready to serve traffic.
    """

    result = check_readiness()

    if result["status"] != "ready":
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "status": result["status"],
                "azure_search": result[
                    "azure_search"
                ],
                "index_name": result[
                    "index_name"
                ],
                "error": result.get(
                    "error"
                ),
            },
        )

    return ReadyResponse(
        status=result["status"],
        azure_search=result[
            "azure_search"
        ],
        index_name=result[
            "index_name"
        ],
        document_count=result.get(
            "document_count"
        ),
    )


# -------------------------------------------------------------------
# RAG QUESTION ENDPOINT
# -------------------------------------------------------------------

@router.post(
    "/api/v1/ask",
    response_model=AskResponse,
    tags=["RAG"],
)
def ask(
    request: AskRequest,
) -> AskResponse:
    """
    Ask a question against the approved
    healthcare knowledge base.

    Flow:

        request
        -> hybrid retrieval
        -> context construction
        -> Azure OpenAI
        -> grounded response
        -> citations
    """

    request_id = str(
        uuid.uuid4()
    )

    with tracer.start_as_current_span(
        "api_ask_request"
    ) as span:

        span.set_attribute(
            "app.request_id",
            request_id,
        )

        span.set_attribute(
            "rag.top_k",
            request.top_k,
        )

        span.set_attribute(
            "rag.retrieval_mode",
            "hybrid",
        )

        span.set_attribute(
            "api.endpoint",
            "/api/v1/ask",
        )

        try:
            result = answer_question(
                question=request.question,
                top_k=request.top_k,
            )

            retrieved_chunks = result.get(
                "retrieved_chunks",
                [],
            )

            retrieved_chunk_ids = [
                document["chunk_id"]
                for document in retrieved_chunks
            ]

            citations = [
                Citation(
                    document_id=(
                        citation[
                            "document_id"
                        ]
                    ),
                    chunk_id=(
                        citation[
                            "chunk_id"
                        ]
                    ),
                    title=(
                        citation[
                            "title"
                        ]
                    ),
                    section=(
                        citation[
                            "section"
                        ]
                    ),
                    page=(
                        citation.get(
                            "page"
                        )
                    ),
                )
                for citation in result.get(
                    "citations",
                    [],
                )
            ]

            span.set_attribute(
                "rag.retrieved_count",
                len(
                    retrieved_chunks
                ),
            )

            span.set_attribute(
                "rag.citation_count",
                len(
                    citations
                ),
            )

            span.set_attribute(
                "rag.response_success",
                True,
            )

            return AskResponse(
                request_id=request_id,
                answer=result["answer"],
                citations=citations,
                retrieval=RetrievalInfo(
                    mode="hybrid",
                    top_k=request.top_k,
                    retrieved_count=len(
                        retrieved_chunks
                    ),
                    retrieved_chunk_ids=(
                        retrieved_chunk_ids
                    ),
                ),
            )

        except HTTPException:
            raise

        except Exception as exc:
            span.record_exception(
                exc
            )

            span.set_attribute(
                "rag.response_success",
                False,
            )

            span.set_attribute(
                "error.type",
                type(exc).__name__,
            )

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail={
                    "request_id":
                        request_id,
                    "error":
                        "rag_processing_failed",
                    "message":
                        (
                            "The request could "
                            "not be processed."
                        ),
                },
            ) from exc
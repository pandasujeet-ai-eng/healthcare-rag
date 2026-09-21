import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from app.graph.healthcare_rag_hitl_graph import (
    build_healthcare_rag_hitl_graph,
)
from app.models.graph_request import (
    GraphReviewRequest,
    GraphStartRequest,
)
from app.models.graph_response import (
    GraphCitation,
    GraphRunResponse,
)
from app.persistence.postgres_checkpointer import (
    get_postgres_checkpointer,
)


router = APIRouter(
    prefix="/api/v1/runs",
    tags=["LangGraph HITL"],
)


def build_config(
    thread_id: str,
) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def serialize_citations(
    citations: list[dict] | None,
) -> list[GraphCitation]:

    if not citations:
        return []

    return [
        GraphCitation(
            document_id=item.get("document_id"),
            chunk_id=item.get("chunk_id"),
            title=item.get("title"),
            version=item.get("version"),
            section=item.get("section"),
            page=item.get("page"),
        )
        for item in citations
    ]


def extract_interrupt_payload(
    result: dict[str, Any],
) -> Any | None:

    interrupts = result.get(
        "__interrupt__",
        [],
    )

    if not interrupts:
        return None

    first_interrupt = interrupts[0]

    value = getattr(
        first_interrupt,
        "value",
        None,
    )

    if value is not None:
        return value

    if isinstance(
        first_interrupt,
        dict,
    ):
        return first_interrupt.get(
            "value",
            first_interrupt,
        )

    return str(first_interrupt)


@router.post(
    "/start",
    response_model=GraphRunResponse,
)
def start_graph_run(
    request: GraphStartRequest,
) -> GraphRunResponse:

    thread_id = str(
        uuid.uuid4()
    )

    config = build_config(
        thread_id
    )

    try:

        with get_postgres_checkpointer() as checkpointer:

            graph = (
                build_healthcare_rag_hitl_graph(
                    checkpointer
                )
            )

            result = graph.invoke(
                {
                    "question": request.question,
                    "top_k": request.top_k,
                },
                config=config,
            )

        review_payload = (
            extract_interrupt_payload(
                result
            )
        )

        if review_payload is not None:

            return GraphRunResponse(
                thread_id=thread_id,
                status="waiting_for_review",
                answer=None,
                citations=[],
                review_payload=review_payload,
                review_decision=None,
            )

        return GraphRunResponse(
            thread_id=thread_id,
            status="completed",
            answer=result.get("answer"),
            citations=serialize_citations(
                result.get(
                    "citations",
                    [],
                )
            ),
            review_payload=None,
            review_decision=result.get(
                "review_decision"
            ),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "thread_id": thread_id,
                "error": (
                    "graph_execution_failed"
                ),
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/{thread_id}/review",
    response_model=GraphRunResponse,
)
def review_graph_run(
    thread_id: str,
    request: GraphReviewRequest,
) -> GraphRunResponse:

    config = build_config(
        thread_id
    )

    try:

        with get_postgres_checkpointer() as checkpointer:

            graph = (
                build_healthcare_rag_hitl_graph(
                    checkpointer
                )
            )

            snapshot = graph.get_state(
                config
            )

            if not snapshot.values:

                raise HTTPException(
                    status_code=404,
                    detail={
                        "thread_id": thread_id,
                        "error": (
                            "thread_not_found"
                        ),
                    },
                )

            result = graph.invoke(
                Command(
                    resume={
                        "approved": (
                            request.approved
                        )
                    }
                ),
                config=config,
            )

        review_payload = (
            extract_interrupt_payload(
                result
            )
        )

        if review_payload is not None:

            return GraphRunResponse(
                thread_id=thread_id,
                status="waiting_for_review",
                answer=None,
                citations=[],
                review_payload=review_payload,
                review_decision=result.get(
                    "review_decision"
                ),
            )

        status = (
            "approved"
            if request.approved
            else "rejected"
        )

        return GraphRunResponse(
            thread_id=thread_id,
            status=status,
            answer=result.get("answer"),
            citations=serialize_citations(
                result.get(
                    "citations",
                    [],
                )
            ),
            review_payload=None,
            review_decision=result.get(
                "review_decision"
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "thread_id": thread_id,
                "error": (
                    "graph_resume_failed"
                ),
                "detail": str(exc),
            },
        ) from exc


@router.get(
    "/{thread_id}",
)
def get_graph_state(
    thread_id: str,
) -> dict:

    config = build_config(
        thread_id
    )

    try:

        with get_postgres_checkpointer() as checkpointer:

            graph = (
                build_healthcare_rag_hitl_graph(
                    checkpointer
                )
            )

            snapshot = graph.get_state(
                config
            )

        if not snapshot.values:

            raise HTTPException(
                status_code=404,
                detail={
                    "thread_id": thread_id,
                    "error": "thread_not_found",
                },
            )

        return {
            "thread_id": thread_id,
            "values": snapshot.values,
            "next": list(
                snapshot.next
            ),
            "created_at": getattr(
                snapshot,
                "created_at",
                None,
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "thread_id": thread_id,
                "error": (
                    "state_read_failed"
                ),
                "detail": str(exc),
            },
        ) from exc
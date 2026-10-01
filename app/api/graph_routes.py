from __future__ import annotations

import uuid
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from langgraph.types import (
    Command,
)

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

from app.persistence.checkpointer_factory import (
    get_checkpointer,
)

from app.security.easyauth import (
    extract_actor_id,
    extract_roles,
    require_authenticated_user,
    require_reviewer,
)

from app.security.thread_access import (
    delete_thread_owner,
    register_thread_owner,
    require_thread_read_access,
    require_thread_review_access,
)


router = APIRouter(
    prefix="/api/v1/runs",
    tags=[
        "LangGraph HITL"
    ],
)


# =====================================================================
# HELPERS
# =====================================================================


def build_config(
    thread_id: str,
) -> dict:

    return {
        "configurable": {
            "thread_id": (
                thread_id
            ),
        }
    }


def serialize_citations(
    citations: list[dict] | None,
) -> list[GraphCitation]:

    if not citations:
        return []

    return [
        GraphCitation(
            document_id=(
                item.get(
                    "document_id"
                )
            ),
            chunk_id=(
                item.get(
                    "chunk_id"
                )
            ),
            title=(
                item.get(
                    "title"
                )
            ),
            version=(
                item.get(
                    "version"
                )
            ),
            section=(
                item.get(
                    "section"
                )
            ),
            page=(
                item.get(
                    "page"
                )
            ),
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

    first_interrupt = (
        interrupts[
            0
        ]
    )

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

    return str(
        first_interrupt
    )


# =====================================================================
# START
# =====================================================================


@router.post(
    "/start",
    response_model=(
        GraphRunResponse
    ),
)
def start_graph_run(
    request: GraphStartRequest,
    principal: dict = Depends(
        require_authenticated_user
    ),
) -> GraphRunResponse:

    actor_id = (
        extract_actor_id(
            principal
        )
    )

    actor_roles = sorted(
        extract_roles(
            principal
        )
    )

    thread_id = str(
        uuid.uuid4()
    )

    config = build_config(
        thread_id
    )

    # ---------------------------------------------------------
    # Register ownership BEFORE executing graph.
    # If graph execution fails, we clean it up.
    # ---------------------------------------------------------

    register_thread_owner(
        thread_id=thread_id,
        actor_id=actor_id,
    )

    try:

        with get_checkpointer() as checkpointer:

            graph = (
                build_healthcare_rag_hitl_graph(
                    checkpointer
                )
            )

            result = graph.invoke(
                {
                    "question": (
                        request.question
                    ),
                    "top_k": (
                        request.top_k
                    ),

                    # -----------------------------------------
                    # TRUSTED SERVER-SIDE IDENTITY
                    # -----------------------------------------

                    "thread_id": (
                        thread_id
                    ),
                    "actor_id": (
                        actor_id
                    ),
                    "actor_roles": (
                        actor_roles
                    ),
                },
                config=config,
            )

        review_payload = (
            extract_interrupt_payload(
                result
            )
        )

        if (
            review_payload
            is not None
        ):

            return GraphRunResponse(
                thread_id=(
                    thread_id
                ),
                status=(
                    "waiting_for_review"
                ),
                answer=None,
                citations=[],
                review_payload=(
                    review_payload
                ),
                review_decision=None,
            )

        return GraphRunResponse(
            thread_id=(
                thread_id
            ),
            status="completed",
            answer=(
                result.get(
                    "answer"
                )
            ),
            citations=(
                serialize_citations(
                    result.get(
                        "citations",
                        [],
                    )
                )
            ),
            review_payload=None,
            review_decision=(
                result.get(
                    "review_decision"
                )
            ),
        )

    except Exception as exc:

        delete_thread_owner(
            thread_id=(
                thread_id
            )
        )

        raise HTTPException(
            status_code=500,
            detail={
                "thread_id": (
                    thread_id
                ),
                "error": (
                    "graph_execution_failed"
                ),
                "detail": (
                    str(
                        exc
                    )
                ),
            },
        ) from exc


# =====================================================================
# READ THREAD
# =====================================================================


@router.get(
    "/{thread_id}",
)
def get_graph_state(
    thread_id: str,
    principal: dict = Depends(
        require_authenticated_user
    ),
) -> dict:

    actor_id = (
        extract_actor_id(
            principal
        )
    )

    actor_roles = (
        extract_roles(
            principal
        )
    )

    # ---------------------------------------------------------
    # Ownership enforcement
    # ---------------------------------------------------------

    require_thread_read_access(
        thread_id=thread_id,
        actor_id=actor_id,
        actor_roles=(
            actor_roles
        ),
    )

    config = build_config(
        thread_id
    )

    try:

        with get_checkpointer() as checkpointer:

            graph = (
                build_healthcare_rag_hitl_graph(
                    checkpointer
                )
            )

            snapshot = (
                graph.get_state(
                    config
                )
            )

        if not snapshot.values:

            raise HTTPException(
                status_code=404,
                detail={
                    "thread_id": (
                        thread_id
                    ),
                    "error": (
                        "thread_not_found"
                    ),
                },
            )

        # ---------------------------------------------------------
        # Return a deliberately restricted view.
        #
        # We do NOT expose the entire internal graph state anymore.
        # ---------------------------------------------------------

        return {
            "thread_id": (
                thread_id
            ),
            "status": (
                "waiting_for_review"
                if (
                    "human_review"
                    in snapshot.next
                )
                else "completed"
            ),
            "next": list(
                snapshot.next
            ),
            "route": (
                snapshot.values.get(
                    "route"
                )
            ),
            "route_reason": (
                snapshot.values.get(
                    "route_reason"
                )
            ),
            "review_decision": (
                snapshot.values.get(
                    "review_decision"
                )
            ),
            "answer": (
                snapshot.values.get(
                    "answer"
                )
            ),
            "citations": (
                snapshot.values.get(
                    "citations",
                    [],
                )
            ),
            "degraded": (
                snapshot.values.get(
                    "degraded",
                    False,
                )
            ),
            "error_stage": (
                snapshot.values.get(
                    "error_stage"
                )
            ),
            "retry_count": (
                snapshot.values.get(
                    "retry_count",
                    0,
                )
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "thread_id": (
                    thread_id
                ),
                "error": (
                    "state_read_failed"
                ),
                "detail": (
                    str(
                        exc
                    )
                ),
            },
        ) from exc


# =====================================================================
# REVIEW THREAD
# =====================================================================


@router.post(
    "/{thread_id}/review",
    response_model=(
        GraphRunResponse
    ),
)
def review_graph_run(
    thread_id: str,
    request: GraphReviewRequest,
    principal: dict = Depends(
        require_reviewer
    ),
) -> GraphRunResponse:

    actor_roles = (
        extract_roles(
            principal
        )
    )

    # ---------------------------------------------------------
    # Reviewer authorization
    # ---------------------------------------------------------

    require_thread_review_access(
        thread_id=thread_id,
        actor_roles=(
            actor_roles
        ),
    )

    config = build_config(
        thread_id
    )

    try:

        with get_checkpointer() as checkpointer:

            graph = (
                build_healthcare_rag_hitl_graph(
                    checkpointer
                )
            )

            snapshot = (
                graph.get_state(
                    config
                )
            )

            if not snapshot.values:

                raise HTTPException(
                    status_code=404,
                    detail={
                        "thread_id": (
                            thread_id
                        ),
                        "error": (
                            "thread_not_found"
                        ),
                    },
                )

            if (
                "human_review"
                not in snapshot.next
            ):

                raise HTTPException(
                    status_code=409,
                    detail={
                        "thread_id": (
                            thread_id
                        ),
                        "error": (
                            "thread_not_waiting_for_review"
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

        if (
            review_payload
            is not None
        ):

            return GraphRunResponse(
                thread_id=(
                    thread_id
                ),
                status=(
                    "waiting_for_review"
                ),
                answer=None,
                citations=[],
                review_payload=(
                    review_payload
                ),
                review_decision=(
                    result.get(
                        "review_decision"
                    )
                ),
            )

        status = (
            "approved"
            if request.approved
            else "rejected"
        )

        return GraphRunResponse(
            thread_id=(
                thread_id
            ),
            status=status,
            answer=(
                result.get(
                    "answer"
                )
            ),
            citations=(
                serialize_citations(
                    result.get(
                        "citations",
                        [],
                    )
                )
            ),
            review_payload=None,
            review_decision=(
                result.get(
                    "review_decision"
                )
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "thread_id": (
                    thread_id
                ),
                "error": (
                    "graph_resume_failed"
                ),
                "detail": (
                    str(
                        exc
                    )
                ),
            },
        ) from exc
from __future__ import annotations

import os
import uuid
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_openai import (
    AzureChatOpenAI,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from langgraph.types import (
    Command,
    interrupt,
)
from langsmith import traceable

from app.agent.control_router import (
    AgentRoute,
    decide_agent_route,
)

from app.chains.context_builder import (
    build_context,
)

from app.chains.relevance_gate import (
    assess_evidence,
)

from app.observability.agent_metrics import (
    observe_stage,
    record_degraded,
    record_error,
    record_hitl,
    record_request,
    record_route,
    set_current_span_attributes,
)

from app.resilience.retry import (
    run_with_retry,
)

from app.retrieval.azure_retriever import (
    retrieve,
)

from app.tools.base import (
    ToolExecutionContext,
)

from app.tools.executor import (
    execute_tool,
)


load_dotenv()


try:
    from app.prompts.healthcare_prompt import (
        SYSTEM_PROMPT,
    )

except ImportError:

    SYSTEM_PROMPT = """
You are a healthcare policy knowledge assistant.

Answer only from the approved context provided to you.

Rules:

1. Do not invent facts.
2. Do not rely on outside medical knowledge.
3. If the approved context does not support the answer,
   say exactly:

   I cannot find sufficient information in the approved knowledge base.

4. Correct false premises using approved context.
5. Be concise and factual.
"""


REFUSAL_MESSAGE = (
    "I cannot find sufficient information "
    "in the approved knowledge base."
)

TEMPORARY_FAILURE_MESSAGE = (
    "The service is temporarily unavailable. "
    "Please try again later."
)


class HealthcareRAGState(
    TypedDict,
    total=False,
):
    question: str
    top_k: int

    thread_id: str

    actor_id: str
    actor_roles: list[str]

    retrieved: list[
        dict[str, Any]
    ]

    relevant: bool

    supporting_chunk_ids: (
        list[str]
    )

    supporting: list[
        dict[str, Any]
    ]

    route: str
    route_reason: str
    route_confidence: float

    needs_human_review: bool
    review_decision: (
        str
        | None
    )

    action_requested: bool

    action_result: (
        dict[str, Any]
        | None
    )

    answer: (
        str
        | None
    )

    citations: list[
        dict[str, Any]
    ]

    error_stage: (
        str
        | None
    )

    error_type: (
        str
        | None
    )

    error_message: (
        str
        | None
    )

    retry_count: int

    degraded: bool


# =====================================================================
# DOCUMENT HELPERS
# =====================================================================


def get_document_metadata(
    document: Any,
) -> dict[str, Any]:

    if isinstance(
        document,
        dict,
    ):

        metadata = document.get(
            "metadata"
        )

        if isinstance(
            metadata,
            dict,
        ):
            return metadata

        return document

    metadata = getattr(
        document,
        "metadata",
        None,
    )

    if isinstance(
        metadata,
        dict,
    ):
        return metadata

    return {}


def extract_chunk_id(
    document: Any,
) -> str | None:

    metadata = (
        get_document_metadata(
            document
        )
    )

    chunk_id = metadata.get(
        "chunk_id"
    )

    if chunk_id:
        return str(
            chunk_id
        )

    if isinstance(
        document,
        dict,
    ):

        chunk_id = document.get(
            "chunk_id"
        )

        if chunk_id:
            return str(
                chunk_id
            )

    return None


def build_citations(
    documents: list[Any],
) -> list[dict[str, Any]]:

    citations = []
    seen = set()

    for document in documents:

        metadata = (
            get_document_metadata(
                document
            )
        )

        chunk_id = (
            extract_chunk_id(
                document
            )
        )

        if (
            chunk_id
            and chunk_id in seen
        ):
            continue

        if chunk_id:
            seen.add(
                chunk_id
            )

        citations.append(
            {
                "document_id": (
                    metadata.get(
                        "document_id"
                    )
                ),
                "chunk_id": (
                    chunk_id
                ),
                "title": (
                    metadata.get(
                        "title"
                    )
                ),
                "version": (
                    metadata.get(
                        "version"
                    )
                ),
                "section": (
                    metadata.get(
                        "section"
                    )
                ),
                "page": (
                    metadata.get(
                        "page"
                    )
                ),
            }
        )

    return citations


# =====================================================================
# RETRIEVAL
# =====================================================================


@traceable(
    name="graph.retrieve"
)
def retrieve_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "retrieve"
    ):

        question = state[
            "question"
        ]

        top_k = state.get(
            "top_k",
            3,
        )

        record_request(
            actor_id=(
                state.get(
                    "actor_id"
                )
            )
        )

        set_current_span_attributes(
            {
                "agent.thread_id": (
                    state.get(
                        "thread_id"
                    )
                ),
                "agent.actor.present": (
                    bool(
                        state.get(
                            "actor_id"
                        )
                    )
                ),
            }
        )

        result = run_with_retry(
            operation_name=(
                "azure_search_retrieval"
            ),
            operation=lambda: retrieve(
                question,
                top_k=top_k,
            ),
        )

        if not result.success:

            record_error(
                stage="retrieve",
                error_type=(
                    result.error_type
                ),
            )

            record_degraded(
                stage="retrieve"
            )

            return {
                "retrieved": [],
                "error_stage": (
                    "retrieve"
                ),
                "error_type": (
                    result.error_type
                ),
                "error_message": (
                    result.error_message
                ),
                "retry_count": (
                    result.retries
                ),
                "degraded": True,
            }

        return {
            "retrieved": (
                result.value
            ),
            "retry_count": (
                state.get(
                    "retry_count",
                    0,
                )
                + result.retries
            ),
        }


def route_after_retrieve(
    state: HealthcareRAGState,
) -> Literal[
    "assess_evidence",
    "error",
]:

    if state.get(
        "error_stage"
    ):
        return "error"

    return "assess_evidence"


# =====================================================================
# EVIDENCE ASSESSMENT
# =====================================================================


@traceable(
    name="graph.assess_evidence"
)
def assess_evidence_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "assess_evidence"
    ):

        question = state[
            "question"
        ]

        documents = state.get(
            "retrieved",
            [],
        )

        result = run_with_retry(
            operation_name=(
                "evidence_assessment"
            ),
            operation=lambda: (
                assess_evidence(
                    question,
                    documents,
                )
            ),
        )

        if not result.success:

            record_error(
                stage=(
                    "assess_evidence"
                ),
                error_type=(
                    result.error_type
                ),
            )

            record_degraded(
                stage=(
                    "assess_evidence"
                )
            )

            return {
                "relevant": False,
                "supporting_chunk_ids": [],
                "error_stage": (
                    "assess_evidence"
                ),
                "error_type": (
                    result.error_type
                ),
                "error_message": (
                    result.error_message
                ),
                "retry_count": (
                    state.get(
                        "retry_count",
                        0,
                    )
                    + result.retries
                ),
                "degraded": True,
            }

        evidence_result = (
            result.value
        )

        relevant = bool(
            evidence_result.get(
                "relevant",
                False,
            )
        )

        supporting_ids = [
            str(item)
            for item in (
                evidence_result.get(
                    "supporting_chunk_ids",
                    [],
                )
                or []
            )
            if item
        ]

        return {
            "relevant": relevant,
            "supporting_chunk_ids": (
                supporting_ids
            ),
            "retry_count": (
                state.get(
                    "retry_count",
                    0,
                )
                + result.retries
            ),
        }


def route_after_evidence(
    state: HealthcareRAGState,
) -> Literal[
    "control_router",
    "error",
]:

    if state.get(
        "error_stage"
    ):
        return "error"

    return "control_router"


# =====================================================================
# CONTROL ROUTER
# =====================================================================


@traceable(
    name="graph.control_router"
)
def control_router_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "control_router"
    ):

        decision = decide_agent_route(
            question=state[
                "question"
            ],
            relevant=state.get(
                "relevant"
            ),
            supporting_chunk_ids=(
                state.get(
                    "supporting_chunk_ids",
                    [],
                )
            ),
            explicit_action_allowed=True,
        )

        record_route(
            route=(
                decision.route.value
            ),
            thread_id=(
                state.get(
                    "thread_id"
                )
            ),
        )

        return {
            "route": (
                decision.route.value
            ),
            "route_reason": (
                decision.reason
            ),
            "route_confidence": (
                decision.confidence
            ),
            "needs_human_review": (
                decision.route
                == AgentRoute.HUMAN_REVIEW
            ),
            "action_requested": (
                decision.route
                == AgentRoute.ACTION
            ),
        }


def route_after_control(
    state: HealthcareRAGState,
) -> Literal[
    "select_evidence",
    "refuse",
    "human_review",
    "action",
]:

    route = state.get(
        "route",
        AgentRoute.REFUSE.value,
    )

    if (
        route
        == AgentRoute.ANSWER.value
    ):
        return "select_evidence"

    if (
        route
        == AgentRoute.HUMAN_REVIEW.value
    ):
        return "human_review"

    if (
        route
        == AgentRoute.ACTION.value
    ):
        return "action"

    return "refuse"


# =====================================================================
# SELECT EVIDENCE
# =====================================================================


@traceable(
    name="graph.select_evidence"
)
def select_evidence_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "select_evidence"
    ):

        ids = set(
            state.get(
                "supporting_chunk_ids",
                [],
            )
        )

        supporting = []

        for document in state.get(
            "retrieved",
            [],
        ):

            chunk_id = (
                extract_chunk_id(
                    document
                )
            )

            if (
                chunk_id
                and chunk_id in ids
            ):

                supporting.append(
                    document
                )

        return {
            "supporting": supporting,
            "citations": (
                build_citations(
                    supporting
                )
            ),
        }


# =====================================================================
# HITL
# =====================================================================


@traceable(
    name="graph.human_review"
)
def human_review_node(
    state: HealthcareRAGState,
) -> Command:

    with observe_stage(
        "human_review"
    ):

        record_hitl(
            event="requested"
        )

        response = interrupt(
            {
                "type": (
                    "clinical_policy_review"
                ),
                "question": (
                    state.get(
                        "question"
                    )
                ),
                "route_reason": (
                    state.get(
                        "route_reason"
                    )
                ),
                "supporting_chunk_ids": (
                    state.get(
                        "supporting_chunk_ids",
                        [],
                    )
                ),
            }
        )

        if not isinstance(
            response,
            dict,
        ):
            response = {
                "approved": False
            }

        approved = bool(
            response.get(
                "approved",
                False,
            )
        )

        if approved:

            record_hitl(
                event="approved"
            )

            return Command(
                update={
                    "review_decision": (
                        "approved"
                    ),
                    "needs_human_review": (
                        False
                    ),
                },
                goto=(
                    "select_evidence"
                ),
            )

        record_hitl(
            event="rejected"
        )

        return Command(
            update={
                "review_decision": (
                    "rejected"
                ),
                "needs_human_review": (
                    False
                ),
            },
            goto="refuse",
        )


# =====================================================================
# CONTROLLED TOOL
# =====================================================================


@traceable(
    name="graph.controlled_action"
)
def action_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "action"
    ):

        thread_id = state.get(
            "thread_id"
        )

        if not thread_id:

            thread_id = str(
                uuid.uuid4()
            )

        context = ToolExecutionContext(
            actor_id=state.get(
                "actor_id",
                "anonymous",
            ),
            actor_roles=set(
                state.get(
                    "actor_roles",
                    [],
                )
            ),
            thread_id=thread_id,
        )

        result = execute_tool(
            tool_name=(
                "create_review_request"
            ),
            arguments={
                "question": (
                    state.get(
                        "question",
                        "",
                    )
                ),
                "supporting_chunk_ids": (
                    state.get(
                        "supporting_chunk_ids",
                        [],
                    )
                ),
                "reason": (
                    state.get(
                        "route_reason"
                    )
                ),
            },
            context=context,
        )

        if result.success:

            answer = (
                result.message
            )

        else:

            answer = (
                "The requested action "
                "could not be performed."
            )

        return {
            "thread_id": thread_id,
            "action_result": (
                result.model_dump()
            ),
            "answer": answer,
            "citations": [],
        }


# =====================================================================
# GENERATION
# =====================================================================


def get_llm() -> AzureChatOpenAI:

    return AzureChatOpenAI(
        azure_endpoint=os.environ[
            "AZURE_OPENAI_ENDPOINT"
        ],
        api_key=os.environ[
            "AZURE_OPENAI_API_KEY"
        ],
        azure_deployment=os.environ[
            "AZURE_OPENAI_CHAT_DEPLOYMENT"
        ],
        api_version=os.getenv(
            "AZURE_OPENAI_API_VERSION",
            "2024-10-21",
        ),
        temperature=0,
    )


@traceable(
    name="graph.generate"
)
def generate_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "generate"
    ):

        supporting = state.get(
            "supporting",
            [],
        )

        if not supporting:

            return {
                "answer": (
                    REFUSAL_MESSAGE
                ),
                "citations": [],
            }

        context = build_context(
            supporting
        )

        prompt = (
            ChatPromptTemplate
            .from_messages(
                [
                    (
                        "system",
                        SYSTEM_PROMPT,
                    ),
                    (
                        "human",
                        (
                            "Question:\n"
                            "{question}\n\n"
                            "Approved context:\n"
                            "{context}"
                        ),
                    ),
                ]
            )
        )

        def generate():

            return (
                prompt
                | get_llm()
            ).invoke(
                {
                    "question": (
                        state[
                            "question"
                        ]
                    ),
                    "context": (
                        context
                    ),
                }
            )

        result = run_with_retry(
            operation_name=(
                "azure_openai_generation"
            ),
            operation=generate,
        )

        if not result.success:

            record_error(
                stage="generate",
                error_type=(
                    result.error_type
                ),
            )

            record_degraded(
                stage="generate"
            )

            return {
                "answer": None,
                "citations": [],
                "error_stage": (
                    "generate"
                ),
                "error_type": (
                    result.error_type
                ),
                "error_message": (
                    result.error_message
                ),
                "retry_count": (
                    state.get(
                        "retry_count",
                        0,
                    )
                    + result.retries
                ),
                "degraded": True,
            }

        response = result.value

        return {
            "answer": getattr(
                response,
                "content",
                str(response),
            ),
            "citations": (
                build_citations(
                    supporting
                )
            ),
            "retry_count": (
                state.get(
                    "retry_count",
                    0,
                )
                + result.retries
            ),
        }


def route_after_generate(
    state: HealthcareRAGState,
) -> Literal[
    "complete",
    "error",
]:

    if state.get(
        "error_stage"
    ):
        return "error"

    return "complete"


# =====================================================================
# REFUSAL
# =====================================================================


@traceable(
    name="graph.refuse"
)
def refuse_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "refuse"
    ):

        return {
            "answer": (
                REFUSAL_MESSAGE
            ),
            "citations": [],
        }


# =====================================================================
# ERROR
# =====================================================================


@traceable(
    name="graph.error"
)
def error_node(
    state: HealthcareRAGState,
) -> dict[str, Any]:

    with observe_stage(
        "error"
    ):

        print(
            "[AGENT_ERROR] "
            f"stage="
            f"{state.get('error_stage')} "
            f"type="
            f"{state.get('error_type')} "
            f"retries="
            f"{state.get('retry_count', 0)}"
        )

        return {
            "answer": (
                TEMPORARY_FAILURE_MESSAGE
            ),
            "citations": [],
            "degraded": True,
        }


# =====================================================================
# GRAPH BUILDER
# =====================================================================


def build_healthcare_rag_hitl_graph(
    checkpointer: Any,
):

    builder = StateGraph(
        HealthcareRAGState
    )

    builder.add_node(
        "retrieve",
        retrieve_node,
    )

    builder.add_node(
        "assess_evidence",
        assess_evidence_node,
    )

    builder.add_node(
        "control_router",
        control_router_node,
    )

    builder.add_node(
        "select_evidence",
        select_evidence_node,
    )

    builder.add_node(
        "human_review",
        human_review_node,
    )

    builder.add_node(
        "action",
        action_node,
    )

    builder.add_node(
        "generate",
        generate_node,
    )

    builder.add_node(
        "refuse",
        refuse_node,
    )

    builder.add_node(
        "error",
        error_node,
    )

    builder.add_edge(
        START,
        "retrieve",
    )

    builder.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "assess_evidence": (
                "assess_evidence"
            ),
            "error": (
                "error"
            ),
        },
    )

    builder.add_conditional_edges(
        "assess_evidence",
        route_after_evidence,
        {
            "control_router": (
                "control_router"
            ),
            "error": (
                "error"
            ),
        },
    )

    builder.add_conditional_edges(
        "control_router",
        route_after_control,
        {
            "select_evidence": (
                "select_evidence"
            ),
            "refuse": (
                "refuse"
            ),
            "human_review": (
                "human_review"
            ),
            "action": (
                "action"
            ),
        },
    )

    builder.add_edge(
        "select_evidence",
        "generate",
    )

    builder.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "complete": END,
            "error": (
                "error"
            ),
        },
    )

    builder.add_edge(
        "refuse",
        END,
    )

    builder.add_edge(
        "action",
        END,
    )

    builder.add_edge(
        "error",
        END,
    )

    return builder.compile(
        checkpointer=checkpointer
    )
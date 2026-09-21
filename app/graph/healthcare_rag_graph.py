import os
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from app.chains.context_builder import build_context
from app.chains.relevance_gate import assess_evidence
from app.prompts.healthcare_prompt import SYSTEM_PROMPT
from app.retrieval.azure_retriever import retrieve


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
CHAT_DEPLOYMENT = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]


REFUSAL_MESSAGE = (
    "I cannot find sufficient information in the approved knowledge base."
)


class HealthcareRAGState(TypedDict, total=False):
    question: str
    top_k: int

    retrieved_documents: list
    supporting_documents: list
    supporting_chunk_ids: list[str]

    relevant: bool

    answer: str
    citations: list[dict]


llm = AzureChatOpenAI(
    azure_deployment=CHAT_DEPLOYMENT,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-10-21",
    temperature=0,
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        (
            "human",
            """
Question:
{question}

Approved hospital-policy context:
{context}
""",
        ),
    ]
)


chain = prompt | llm


def get_document_metadata(
    document: Any,
) -> dict:

    if isinstance(document, dict):

        metadata = document.get("metadata")

        if isinstance(metadata, dict):

            result = dict(metadata)

            for field in [
                "document_id",
                "chunk_id",
                "title",
                "version",
                "section",
                "page",
                "source_file",
                "chunk_index",
            ]:

                if (
                    field not in result
                    and field in document
                ):
                    result[field] = document[field]

            return result

        return {
            "document_id": document.get("document_id"),
            "chunk_id": document.get("chunk_id"),
            "title": document.get("title"),
            "version": document.get("version"),
            "section": document.get("section"),
            "page": document.get("page"),
            "source_file": document.get("source_file"),
            "chunk_index": document.get("chunk_index"),
        }

    metadata = getattr(
        document,
        "metadata",
        {},
    )

    if isinstance(metadata, dict):
        return metadata

    return {}


def extract_chunk_id(
    document: Any,
) -> str | None:

    metadata = get_document_metadata(document)

    chunk_id = metadata.get("chunk_id")

    if chunk_id:
        return str(chunk_id)

    return None


def build_citations(
    documents: list,
) -> list[dict]:

    citations: list[dict] = []

    seen: set[str] = set()

    for document in documents:

        metadata = get_document_metadata(
            document
        )

        chunk_id = metadata.get(
            "chunk_id"
        )

        if not chunk_id:
            continue

        chunk_id = str(chunk_id)

        if chunk_id in seen:
            continue

        seen.add(chunk_id)

        citations.append(
            {
                "document_id": metadata.get(
                    "document_id"
                ),
                "chunk_id": chunk_id,
                "title": metadata.get(
                    "title"
                ),
                "version": metadata.get(
                    "version"
                ),
                "section": metadata.get(
                    "section"
                ),
                "page": metadata.get(
                    "page"
                ),
            }
        )

    return citations


@traceable(
    name="graph_retrieve",
    run_type="retriever",
)
def retrieve_node(
    state: HealthcareRAGState,
) -> dict:

    documents = retrieve(
        state["question"],
        top_k=state.get(
            "top_k",
            3,
        ),
    )

    return {
        "retrieved_documents": documents,
    }


@traceable(
    name="graph_assess_evidence",
    run_type="chain",
)
def assess_evidence_node(
    state: HealthcareRAGState,
) -> dict:

    documents = state.get(
        "retrieved_documents",
        [],
    )

    if not documents:

        return {
            "relevant": False,
            "supporting_chunk_ids": [],
        }

    result = assess_evidence(
        question=state["question"],
        documents=documents,
    )

    return {
        "relevant": result["relevant"],
        "supporting_chunk_ids": result[
            "supporting_chunk_ids"
        ],
    }


def route_after_evidence(
    state: HealthcareRAGState,
) -> str:

    if state.get(
        "relevant",
        False,
    ):
        return "select_evidence"

    return "refuse"


@traceable(
    name="graph_select_evidence",
    run_type="chain",
)
def select_evidence_node(
    state: HealthcareRAGState,
) -> dict:

    supporting_ids = set(
        state.get(
            "supporting_chunk_ids",
            [],
        )
    )

    selected = [
        document
        for document in state.get(
            "retrieved_documents",
            [],
        )
        if extract_chunk_id(document)
        in supporting_ids
    ]

    return {
        "supporting_documents": selected,
    }


@traceable(
    name="graph_generate",
    run_type="llm",
)
def generate_node(
    state: HealthcareRAGState,
) -> dict:

    supporting_documents = state.get(
        "supporting_documents",
        [],
    )

    if not supporting_documents:

        return {
            "answer": REFUSAL_MESSAGE,
            "citations": [],
        }

    context = build_context(
        supporting_documents
    )

    response = chain.invoke(
        {
            "question": state["question"],
            "context": context,
        }
    )

    answer = str(
        response.content
    ).strip()

    if answer == REFUSAL_MESSAGE:

        return {
            "answer": REFUSAL_MESSAGE,
            "citations": [],
        }

    return {
        "answer": answer,
        "citations": build_citations(
            supporting_documents
        ),
    }


def refuse_node(
    state: HealthcareRAGState,
) -> dict:

    return {
        "answer": REFUSAL_MESSAGE,
        "citations": [],
        "supporting_documents": [],
    }


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
    "select_evidence",
    select_evidence_node,
)

builder.add_node(
    "generate",
    generate_node,
)

builder.add_node(
    "refuse",
    refuse_node,
)


builder.add_edge(
    START,
    "retrieve",
)

builder.add_edge(
    "retrieve",
    "assess_evidence",
)

builder.add_conditional_edges(
    "assess_evidence",
    route_after_evidence,
    {
        "select_evidence": "select_evidence",
        "refuse": "refuse",
    },
)

builder.add_edge(
    "select_evidence",
    "generate",
)

builder.add_edge(
    "generate",
    END,
)

builder.add_edge(
    "refuse",
    END,
)


healthcare_rag_graph = (
    builder.compile()
)


def invoke_healthcare_rag_graph(
    question: str,
    top_k: int = 3,
) -> dict:

    result = healthcare_rag_graph.invoke(
        {
            "question": question,
            "top_k": top_k,
        }
    )

    return {
        "answer": result.get(
            "answer",
            REFUSAL_MESSAGE,
        ),
        "citations": result.get(
            "citations",
            [],
        ),
        "retrieved_chunks": result.get(
            "retrieved_documents",
            [],
        ),
        "supporting_chunks": result.get(
            "supporting_documents",
            [],
        ),
    }
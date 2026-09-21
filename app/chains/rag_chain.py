import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langsmith import traceable

from app.chains.context_builder import build_context
from app.chains.relevance_gate import assess_evidence
from app.observability.tracing import get_tracer
from app.prompts.healthcare_prompt import SYSTEM_PROMPT
from app.retrieval.azure_retriever import retrieve


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
CHAT_DEPLOYMENT = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]


REFUSAL_MESSAGE = (
    "I cannot find sufficient information in the approved knowledge base."
)


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


azure_tracer = get_tracer()


def get_document_metadata(
    document: Any,
) -> dict:

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

            result = dict(
                metadata
            )

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

                    result[field] = (
                        document[field]
                    )

            return result

        return {
            "document_id": document.get(
                "document_id"
            ),
            "chunk_id": document.get(
                "chunk_id"
            ),
            "title": document.get(
                "title"
            ),
            "version": document.get(
                "version"
            ),
            "section": document.get(
                "section"
            ),
            "page": document.get(
                "page"
            ),
            "source_file": document.get(
                "source_file"
            ),
            "chunk_index": document.get(
                "chunk_index"
            ),
        }

    metadata = getattr(
        document,
        "metadata",
        {},
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

    metadata = get_document_metadata(
        document
    )

    chunk_id = metadata.get(
        "chunk_id"
    )

    if chunk_id:

        return str(
            chunk_id
        )

    return None


def select_supporting_documents(
    documents: list,
    supporting_chunk_ids: list[str],
) -> list:

    supporting_id_set = set(
        supporting_chunk_ids
    )

    selected_documents = [
        document
        for document in documents
        if extract_chunk_id(document)
        in supporting_id_set
    ]

    return selected_documents


def build_citations(
    documents: list,
) -> list[dict]:

    citations: list[dict] = []

    seen_chunk_ids: set[str] = set()

    for document in documents:

        metadata = get_document_metadata(
            document
        )

        chunk_id = metadata.get(
            "chunk_id"
        )

        if not chunk_id:
            continue

        chunk_id = str(
            chunk_id
        )

        if chunk_id in seen_chunk_ids:
            continue

        seen_chunk_ids.add(
            chunk_id
        )

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
    name="healthcare_rag",
    run_type="chain",
    metadata={
        "env": "dev",
        "application": "healthcare-rag",
        "rag_version": "v3",
        "retrieval_mode": "hybrid",
        "prompt_version": "v1",
        "evidence_gate_version": "v2",
    },
)
def answer_question(
    question: str,
    top_k: int = 3,
) -> dict:

    with azure_tracer.start_as_current_span(
        "healthcare_rag_request"
    ) as span:

        span.set_attribute(
            "app.name",
            "healthcare-rag",
        )

        span.set_attribute(
            "app.environment",
            "dev",
        )

        span.set_attribute(
            "rag.version",
            "v3",
        )

        span.set_attribute(
            "rag.prompt_version",
            "v1",
        )

        span.set_attribute(
            "rag.evidence_gate_version",
            "v2",
        )

        span.set_attribute(
            "rag.retrieval_mode",
            "hybrid",
        )

        span.set_attribute(
            "rag.top_k",
            top_k,
        )

        span.set_attribute(
            "ai.chat_deployment",
            CHAT_DEPLOYMENT,
        )

        try:

            documents = retrieve(
                question,
                top_k=top_k,
            )

            span.set_attribute(
                "rag.retrieved_count",
                len(documents),
            )

            if not documents:

                span.set_attribute(
                    "rag.relevance",
                    False,
                )

                span.set_attribute(
                    "rag.refused",
                    True,
                )

                span.set_attribute(
                    "rag.citation_count",
                    0,
                )

                return {
                    "answer": REFUSAL_MESSAGE,
                    "citations": [],
                    "retrieved_chunks": [],
                }

            evidence_result = (
                assess_evidence(
                    question=question,
                    documents=documents,
                )
            )

            relevant = (
                evidence_result[
                    "relevant"
                ]
            )

            supporting_chunk_ids = (
                evidence_result[
                    "supporting_chunk_ids"
                ]
            )

            span.set_attribute(
                "rag.relevance",
                relevant,
            )

            span.set_attribute(
                "rag.supporting_chunk_count",
                len(
                    supporting_chunk_ids
                ),
            )

            if not relevant:

                span.set_attribute(
                    "rag.refused",
                    True,
                )

                span.set_attribute(
                    "rag.citation_count",
                    0,
                )

                return {
                    "answer": REFUSAL_MESSAGE,
                    "citations": [],
                    "retrieved_chunks": documents,
                }

            supporting_documents = (
                select_supporting_documents(
                    documents,
                    supporting_chunk_ids,
                )
            )

            if not supporting_documents:

                span.set_attribute(
                    "rag.refused",
                    True,
                )

                span.set_attribute(
                    "rag.citation_count",
                    0,
                )

                return {
                    "answer": REFUSAL_MESSAGE,
                    "citations": [],
                    "retrieved_chunks": documents,
                }

            context = build_context(
                supporting_documents
            )

            response = chain.invoke(
                {
                    "question": question,
                    "context": context,
                }
            )

            answer = str(
                response.content
            ).strip()

            if answer == REFUSAL_MESSAGE:

                span.set_attribute(
                    "rag.refused",
                    True,
                )

                span.set_attribute(
                    "rag.citation_count",
                    0,
                )

                return {
                    "answer": answer,
                    "citations": [],
                    "retrieved_chunks": documents,
                }

            citations = build_citations(
                supporting_documents
            )

            span.set_attribute(
                "rag.refused",
                False,
            )

            span.set_attribute(
                "rag.citation_count",
                len(citations),
            )

            span.set_attribute(
                "rag.answer_length",
                len(answer),
            )

            return {
                "answer": answer,
                "citations": citations,
                "retrieved_chunks": documents,
            }

        except Exception as exc:

            span.record_exception(
                exc
            )

            span.set_attribute(
                "error",
                True,
            )

            raise
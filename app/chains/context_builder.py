from langsmith import traceable
from opentelemetry import trace


context_tracer = trace.get_tracer(
    "healthcare-rag.context"
)


@traceable(
    name="build_rag_context",
    run_type="chain",
)
def build_context(
    documents: list[dict],
) -> str:
    """
    Convert retrieved documents into a clearly
    separated grounding context for the LLM.

    We preserve source metadata so the model can
    associate content with citations.
    """

    with context_tracer.start_as_current_span(
        "build_rag_context"
    ) as span:

        span.set_attribute(
            "rag.context_document_count",
            len(documents)
        )

        blocks = []

        for doc in documents:

            block = f"""
SOURCE
Document ID: {doc['document_id']}
Chunk ID: {doc['chunk_id']}
Title: {doc['title']}
Version: {doc['version']}
Section: {doc['section']}
Page: {doc['page']}

CONTENT
{doc['content']}
""".strip()

            blocks.append(
                block
            )

        context = (
            "\n\n---\n\n".join(
                blocks
            )
        )

        span.set_attribute(
            "rag.context_length_chars",
            len(context)
        )

        return context
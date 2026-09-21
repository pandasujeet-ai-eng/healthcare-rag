from app.observability.azure_monitor import (
    configure_monitoring
)


# Configure Azure Monitor before importing
# the rest of the application.
configure_monitoring()


from app.chains.rag_chain import (
    answer_question
)


QUESTIONS = [
    (
        "When should metformin be stopped "
        "before surgery?"
    ),
    (
        "What should staff do before "
        "and after patient contact?"
    ),
    (
        "What antibiotic should be used "
        "to treat malaria?"
    ),
]


def print_result(
    question: str,
    result: dict,
) -> None:

    print(
        "=" * 100
    )

    print(
        "QUESTION"
    )

    print(
        question
    )

    print()

    print(
        "ANSWER"
    )

    print(
        result["answer"]
    )

    print()

    print(
        "CITATIONS"
    )

    citations = result.get(
        "citations",
        [],
    )

    if not citations:
        print(
            "No citations."
        )
    else:

        for citation in citations:

            print(
                "- "
                f"{citation['document_id']} | "
                f"{citation['chunk_id']} | "
                f"{citation['title']} | "
                f"{citation['section']} | "
                f"Page {citation['page']}"
            )

    print()

    retrieved = result.get(
        "retrieved_chunks",
        [],
    )

    print(
        "RETRIEVED CHUNKS"
    )

    if not retrieved:
        print(
            "No chunks retrieved."
        )

    else:

        for rank, doc in enumerate(
            retrieved,
            start=1,
        ):

            print(
                f"{rank}. "
                f"{doc['chunk_id']} | "
                f"{doc['document_id']} | "
                f"score={doc.get('score')}"
            )

    print()


def main() -> None:

    print(
        "=" * 100
    )

    print(
        "HEALTHCARE RAG - "
        "LANGSMITH + AZURE MONITOR"
    )

    print(
        "=" * 100
    )

    print()

    for question in QUESTIONS:

        try:

            result = answer_question(
                question,
                top_k=3,
            )

            print_result(
                question,
                result,
            )

        except Exception as exc:

            print(
                "=" * 100
            )

            print(
                "REQUEST FAILED"
            )

            print(
                "=" * 100
            )

            print(
                f"Question: {question}"
            )

            print(
                f"Error type: "
                f"{type(exc).__name__}"
            )

            print(
                f"Error: {exc}"
            )

            print()


if __name__ == "__main__":
    main()
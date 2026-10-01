from app.graph.healthcare_rag_graph import (
    invoke_healthcare_rag_graph,
)


QUESTIONS = [
    "Should metformin be stopped before surgery?",
    "When should healthcare workers perform hand hygiene around patient contact?",
    "The policy says metformin must be stopped 48 hours before surgery, correct?",
    "How should malaria be treated?",
]


def main() -> None:

    for question in QUESTIONS:

        print()
        print("=" * 100)
        print(f"QUESTION: {question}")
        print("=" * 100)

        result = invoke_healthcare_rag_graph(
            question=question,
            top_k=3,
        )

        print()
        print("ANSWER:")
        print(result["answer"])

        print()
        print("CITATIONS:")

        for citation in result[
            "citations"
        ]:
            print(
                citation
            )

        print()
        print(
            "RETRIEVED COUNT:",
            len(
                result[
                    "retrieved_chunks"
                ]
            ),
        )

        print(
            "SUPPORTING COUNT:",
            len(
                result[
                    "supporting_chunks"
                ]
            ),
        )


if __name__ == "__main__":
    main()
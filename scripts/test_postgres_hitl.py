import uuid

from langgraph.types import Command

from app.graph.healthcare_rag_hitl_graph import (
    build_healthcare_rag_hitl_graph,
)
from app.persistence.postgres_checkpointer import (
    get_postgres_checkpointer,
)


def main() -> None:
    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    print()
    print(
        f"THREAD ID: {thread_id}"
    )

    print()
    print("=" * 100)
    print("PHASE 1 - START GRAPH")
    print("=" * 100)

    with get_postgres_checkpointer() as checkpointer:
        graph = build_healthcare_rag_hitl_graph(
            checkpointer
        )

        result = graph.invoke(
            {
                "question": (
                    "The policy says metformin "
                    "must be stopped 48 hours "
                    "before surgery, correct?"
                ),
                "top_k": 3,
            },
            config=config,
        )

        print()
        print("INTERRUPT RESULT:")
        print(
            result.get(
                "__interrupt__"
            )
        )

    print()
    print(
        "PostgreSQL connection closed."
    )

    print()
    print("=" * 100)
    print("PHASE 2 - NEW CONNECTION")
    print("=" * 100)

    with get_postgres_checkpointer() as checkpointer:
        graph = build_healthcare_rag_hitl_graph(
            checkpointer
        )

        snapshot = graph.get_state(
            config
        )

        print()
        print(
            "Saved next nodes:",
            snapshot.next,
        )

        resumed = graph.invoke(
            Command(
                resume={
                    "approved": True
                }
            ),
            config=config,
        )

        print()
        print("=" * 100)
        print("FINAL RESULT")
        print("=" * 100)

        print()
        print("ANSWER:")
        print(
            resumed.get(
                "answer"
            )
        )

        print()
        print("REVIEW DECISION:")
        print(
            resumed.get(
                "review_decision"
            )
        )

        print()
        print("CITATIONS:")
        print(
            resumed.get(
                "citations"
            )
        )


if __name__ == "__main__":
    main()
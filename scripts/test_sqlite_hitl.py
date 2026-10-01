import uuid

from langgraph.types import Command

from app.graph.healthcare_rag_hitl_graph import (
    build_healthcare_rag_hitl_graph,
)
from app.persistence.sqlite_checkpointer import (
    get_sqlite_checkpointer,
)


def main() -> None:

    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    print(
        f"THREAD ID: {thread_id}"
    )

    print()
    print("PHASE 1 - START")

    with get_sqlite_checkpointer() as checkpointer:

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

        print(
            result.get(
                "__interrupt__"
            )
        )

    print()
    print(
        "FIRST SQLITE CONNECTION CLOSED"
    )

    print()
    print(
        "PHASE 2 - NEW CONNECTION"
    )

    with get_sqlite_checkpointer() as checkpointer:

        graph = build_healthcare_rag_hitl_graph(
            checkpointer
        )

        snapshot = graph.get_state(
            config
        )

        print(
            "NEXT:",
            snapshot.next,
        )

        result = graph.invoke(
            Command(
                resume={
                    "approved": True,
                }
            ),
            config=config,
        )

        print()
        print(
            "ANSWER:"
        )

        print(
            result.get(
                "answer"
            )
        )

        print()
        print(
            "REVIEW:"
        )

        print(
            result.get(
                "review_decision"
            )
        )


if __name__ == "__main__":
    main()
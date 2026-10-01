from __future__ import annotations

import uuid

from app.graph.healthcare_rag_hitl_graph import (
    build_healthcare_rag_hitl_graph,
)

from app.observability.agent_metrics import (
    get_local_metric_snapshot,
    reset_local_metrics,
)

from app.persistence.sqlite_checkpointer import (
    get_sqlite_checkpointer,
)


REVIEWER_ROLE = (
    "HealthcareRAG.Reviewer"
)


def invoke(
    *,
    question: str,
    actor_id: str,
    actor_roles: list[str],
):

    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": (
                thread_id
            )
        }
    }

    state = {
        "question": question,
        "top_k": 3,
        "thread_id": thread_id,
        "actor_id": actor_id,
        "actor_roles": actor_roles,
    }

    with get_sqlite_checkpointer() as checkpointer:

        graph = (
            build_healthcare_rag_hitl_graph(
                checkpointer
            )
        )

        return graph.invoke(
            state,
            config=config,
        )


def main():

    reset_local_metrics()

    print()
    print("=" * 90)
    print(
        "OBSERVABILITY TEST"
    )
    print("=" * 90)

    # ---------------------------------------------------------
    # ANSWER
    # ---------------------------------------------------------

    answer_result = invoke(
        question=(
            "When should metformin "
            "be stopped for surgery?"
        ),
        actor_id="normal-user",
        actor_roles=[
            "HealthcareRAG.User"
        ],
    )

    assert (
        answer_result.get(
            "route"
        )
        == "answer"
    )

    # ---------------------------------------------------------
    # REFUSE
    # ---------------------------------------------------------

    refuse_result = invoke(
        question=(
            "What is the hospital "
            "policy for malaria treatment?"
        ),
        actor_id="normal-user",
        actor_roles=[
            "HealthcareRAG.User"
        ],
    )

    assert (
        refuse_result.get(
            "route"
        )
        == "refuse"
    )

    # ---------------------------------------------------------
    # AUTHORIZED ACTION
    # ---------------------------------------------------------

    action_result = invoke(
        question=(
            "Escalate this policy "
            "question for review."
        ),
        actor_id="reviewer-user",
        actor_roles=[
            REVIEWER_ROLE
        ],
    )

    assert (
        action_result.get(
            "route"
        )
        == "action"
    )

    # ---------------------------------------------------------
    # UNAUTHORIZED ACTION
    # ---------------------------------------------------------

    denied_result = invoke(
        question=(
            "Escalate this policy "
            "question for review."
        ),
        actor_id="normal-user",
        actor_roles=[
            "HealthcareRAG.User"
        ],
    )

    denied_action = (
        denied_result.get(
            "action_result",
            {},
        )
    )

    assert (
        denied_action.get(
            "status"
        )
        == "denied"
    )

    snapshot = (
        get_local_metric_snapshot()
    )

    print()
    print(
        "COUNTERS"
    )
    print(
        snapshot[
            "counters"
        ]
    )

    print()
    print(
        "STAGE LATENCY"
    )

    for (
        stage,
        values,
    ) in snapshot[
        "stage_latency"
    ].items():

        print(
            stage,
            values,
        )

    print()
    print(
        "TOOL LATENCY"
    )

    for (
        tool,
        values,
    ) in snapshot[
        "tool_latency"
    ].items():

        print(
            tool,
            values,
        )

    counters = snapshot[
        "counters"
    ]

    assert (
        counters.get(
            "requests",
            0,
        )
        == 4
    )

    assert (
        counters.get(
            "route.answer",
            0,
        )
        >= 1
    )

    assert (
        counters.get(
            "route.refuse",
            0,
        )
        >= 1
    )

    assert (
        counters.get(
            "route.action",
            0,
        )
        >= 2
    )

    assert (
        counters.get(
            "tool.create_review_request.denied",
            0,
        )
        >= 1
    )

    print()
    print("=" * 90)
    print(
        "ALL OBSERVABILITY TESTS PASSED"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()
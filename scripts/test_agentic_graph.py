import uuid

from langgraph.types import Command

from app.graph.healthcare_rag_hitl_graph import (
    build_healthcare_rag_hitl_graph,
)

from app.persistence.sqlite_checkpointer import (
    get_sqlite_checkpointer,
)


REVIEWER_ROLE = (
    "HealthcareRAG.Reviewer"
)


def invoke_new_graph(
    *,
    question: str,
    actor_id: str = (
        "local-developer"
    ),
    actor_roles: list[str] | None = None,
):

    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "question": question,
        "top_k": 3,
        "thread_id": thread_id,
        "actor_id": actor_id,
        "actor_roles": (
            actor_roles
            or []
        ),
    }

    with get_sqlite_checkpointer() as checkpointer:

        graph = (
            build_healthcare_rag_hitl_graph(
                checkpointer
            )
        )

        result = graph.invoke(
            initial_state,
            config=config,
        )

    return (
        thread_id,
        config,
        result,
    )


def print_result(
    title: str,
    result: dict,
):

    print()
    print("=" * 90)
    print(title)
    print("=" * 90)

    print(
        "ROUTE:",
        result.get(
            "route"
        ),
    )

    print(
        "ANSWER:",
        result.get(
            "answer"
        ),
    )

    print(
        "ACTION:",
        result.get(
            "action_result"
        ),
    )

    print(
        "INTERRUPT:",
        result.get(
            "__interrupt__"
        ),
    )


def main():

    # =========================================================
    # CASE 1 - NORMAL GROUNDED ANSWER
    # =========================================================

    _, _, result = (
        invoke_new_graph(
            question=(
                "When should metformin "
                "be stopped for surgery?"
            )
        )
    )

    print_result(
        "CASE 1 - ANSWER",
        result,
    )

    assert (
        result.get(
            "route"
        )
        == "answer"
    )

    # =========================================================
    # CASE 2 - REFUSAL
    # =========================================================

    _, _, result = (
        invoke_new_graph(
            question=(
                "What is the hospital "
                "policy for malaria treatment?"
            )
        )
    )

    print_result(
        "CASE 2 - REFUSE",
        result,
    )

    assert (
        result.get(
            "route"
        )
        == "refuse"
    )

    # =========================================================
    # CASE 3 - HUMAN REVIEW
    # =========================================================

    thread_id, config, result = (
        invoke_new_graph(
            question=(
                "The policy says metformin "
                "must be stopped 48 hours "
                "before surgery, correct?"
            ),
            actor_roles=[
                REVIEWER_ROLE
            ],
        )
    )

    print_result(
        "CASE 3 - HUMAN REVIEW",
        result,
    )

    assert result.get(
        "__interrupt__"
    )

    with get_sqlite_checkpointer() as checkpointer:

        graph = (
            build_healthcare_rag_hitl_graph(
                checkpointer
            )
        )

        resumed = graph.invoke(
            Command(
                resume={
                    "approved": True,
                }
            ),
            config=config,
        )

    assert (
        resumed.get(
            "review_decision"
        )
        == "approved"
    )

    print(
        "REVIEW RESUMED: approved"
    )

    # =========================================================
    # CASE 4 - REVIEWER CAN EXECUTE TOOL
    # =========================================================

    _, _, result = (
        invoke_new_graph(
            question=(
                "Escalate this policy "
                "question for review."
            ),
            actor_id=(
                "reviewer-user"
            ),
            actor_roles=[
                REVIEWER_ROLE
            ],
        )
    )

    print_result(
        "CASE 4 - AUTHORIZED ROLE",
        result,
    )

    action = result.get(
        "action_result",
        {},
    )

    assert (
        result.get(
            "route"
        )
        == "action"
    )

    assert (
        action.get(
            "success"
        )
        is True
    )

    assert (
        action.get(
            "status"
        )
        in {
            "executed",
            "already_exists",
        }
    )

    # =========================================================
    # CASE 5 - NORMAL USER CANNOT EXECUTE TOOL
    # =========================================================

    _, _, result = (
        invoke_new_graph(
            question=(
                "Escalate this policy "
                "question for review."
            ),
            actor_id=(
                "normal-user"
            ),
            actor_roles=[
                "HealthcareRAG.User"
            ],
        )
    )

    print_result(
        "CASE 5 - UNAUTHORIZED ROLE",
        result,
    )

    action = result.get(
        "action_result",
        {},
    )

    assert (
        result.get(
            "route"
        )
        == "action"
    )

    assert (
        action.get(
            "success"
        )
        is False
    )

    assert (
        action.get(
            "status"
        )
        == "denied"
    )

    assert (
        action.get(
            "error_code"
        )
        == "TOOL_NOT_AUTHORIZED"
    )

    print()
    print("=" * 90)
    print(
        "ALL TOOL POLICY TESTS PASSED"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()
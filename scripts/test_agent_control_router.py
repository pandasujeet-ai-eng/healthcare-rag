from app.agent.control_router import (
    AgentRoute,
    decide_agent_route,
    routing_decision_to_dict,
)


def run_case(
    *,
    name: str,
    question: str,
    relevant: bool | None,
    supporting_chunk_ids: list[str],
    expected: AgentRoute,
) -> None:

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    decision = decide_agent_route(
        question=question,
        relevant=relevant,
        supporting_chunk_ids=supporting_chunk_ids,
    )

    print(
        routing_decision_to_dict(
            decision
        )
    )

    assert (
        decision.route == expected
    ), (
        f"{name}: expected "
        f"{expected.value}, "
        f"got {decision.route.value}"
    )

    print(
        f"PASS -> {decision.route.value}"
    )


def main() -> None:

    run_case(
        name="CASE 1 - DIRECT ANSWER",
        question=(
            "When should metformin be stopped "
            "for surgery?"
        ),
        relevant=True,
        supporting_chunk_ids=[
            "POL-DM-001-C0001"
        ],
        expected=AgentRoute.ANSWER,
    )

    run_case(
        name="CASE 2 - UNSUPPORTED QUESTION",
        question=(
            "What is the hospital policy "
            "for malaria treatment?"
        ),
        relevant=False,
        supporting_chunk_ids=[],
        expected=AgentRoute.REFUSE,
    )

    run_case(
        name="CASE 3 - HUMAN REVIEW",
        question=(
            "The policy says metformin must "
            "be stopped 48 hours before "
            "surgery, correct?"
        ),
        relevant=True,
        supporting_chunk_ids=[
            "POL-DM-001-C0001"
        ],
        expected=(
            AgentRoute.HUMAN_REVIEW
        ),
    )

    run_case(
        name="CASE 4 - ACTION",
        question=(
            "Escalate this policy question "
            "for review."
        ),
        relevant=True,
        supporting_chunk_ids=[
            "POL-DM-001-C0001"
        ],
        expected=AgentRoute.ACTION,
    )

    run_case(
        name="CASE 5 - FAIL CLOSED",
        question=(
            "Tell me what I should do."
        ),
        relevant=None,
        supporting_chunk_ids=[],
        expected=AgentRoute.HUMAN_REVIEW,
    )

    run_case(
        name="CASE 6 - NO EVIDENCE",
        question=(
            "Explain this hospital policy."
        ),
        relevant=None,
        supporting_chunk_ids=[],
        expected=AgentRoute.REFUSE,
    )

    print()
    print("=" * 80)
    print(
        "ALL AGENT CONTROL ROUTER TESTS PASSED"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
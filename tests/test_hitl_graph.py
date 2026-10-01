from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import app.graph.healthcare_rag_hitl_graph as graph_module


METFORMIN_CHUNK_ID = "POL-DM-001-C0001"


def build_test_document() -> dict[str, Any]:
    return {
        "chunk_id": METFORMIN_CHUNK_ID,
        "document_id": "POL-DM-001",
        "title": "Diabetes Management Policy",
        "version": "1.0",
        "section": "Perioperative Medication",
        "page": 1,
        "content": (
            "Patients taking metformin should stop "
            "metformin on the morning of surgery "
            "unless otherwise directed by the "
            "responsible physician."
        ),
    }


def install_fake_dependencies(
    monkeypatch,
) -> None:
    """
    Remove all external Azure/LLM dependencies from unit tests.

    These tests validate LangGraph orchestration only.
    """

    document = build_test_document()

    def fake_retrieve(
        question: str,
        top_k: int = 3,
        *,
        config=None,
    ) -> list[dict]:

        return [
            document
        ]

    def fake_assess_evidence(
        question: str,
        documents: list,
        *,
        config=None,
    ) -> dict:

        return {
            "relevant": True,
            "supporting_chunk_ids": [
                METFORMIN_CHUNK_ID
            ],
        }

    def fake_generate_node(
        state: dict,
    ) -> dict:

        return {
            "answer": (
                "Metformin should be stopped "
                "on the morning of surgery "
                "unless otherwise directed by "
                "the responsible physician."
            ),
            "citations": [
                {
                    "document_id": "POL-DM-001",
                    "chunk_id": (
                        METFORMIN_CHUNK_ID
                    ),
                    "title": (
                        "Diabetes Management Policy"
                    ),
                    "version": "1.0",
                    "section": (
                        "Perioperative Medication"
                    ),
                    "page": 1,
                }
            ],
        }

    monkeypatch.setattr(
        graph_module,
        "retrieve",
        fake_retrieve,
    )

    monkeypatch.setattr(
        graph_module,
        "assess_evidence",
        fake_assess_evidence,
    )

    monkeypatch.setattr(
        graph_module,
        "generate_node",
        fake_generate_node,
    )


def build_test_graph(
    monkeypatch,
):
    install_fake_dependencies(
        monkeypatch
    )

    checkpointer = (
        InMemorySaver()
    )

    graph = (
        graph_module
        .build_healthcare_rag_hitl_graph(
            checkpointer
        )
    )

    return graph


def test_false_premise_pauses_for_human_review(
    monkeypatch,
):
    graph = build_test_graph(
        monkeypatch
    )

    config = {
        "configurable": {
            "thread_id": (
                "test-hitl-pause"
            )
        }
    }

    result = graph.invoke(
        {
            "question": (
                "The policy says metformin "
                "must be stopped 48 hours "
                "before surgery, correct?"
            ),
            "top_k": 3,
            "thread_id": (
                "test-hitl-pause"
            ),
            "actor_id": (
                "test-user"
            ),
            "actor_roles": [
                "HealthcareRAG.Reviewer"
            ],
        },
        config=config,
    )

    assert (
        result.get(
            "route"
        )
        == "human_review"
    )

    assert (
        result.get(
            "needs_human_review"
        )
        is True
    )

    assert (
        result.get(
            "supporting_chunk_ids"
        )
        == [
            METFORMIN_CHUNK_ID
        ]
    )

    interrupts = result.get(
        "__interrupt__"
    )

    assert interrupts

    interrupt_value = (
        interrupts[0].value
    )

    assert (
        interrupt_value[
            "type"
        ]
        == "clinical_policy_review"
    )

    assert (
        interrupt_value[
            "supporting_chunk_ids"
        ]
        == [
            METFORMIN_CHUNK_ID
        ]
    )


def test_human_review_approval_resumes_generation(
    monkeypatch,
):
    graph = build_test_graph(
        monkeypatch
    )

    thread_id = (
        "test-hitl-approve"
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    first_result = graph.invoke(
        {
            "question": (
                "The policy says metformin "
                "must be stopped 48 hours "
                "before surgery, correct?"
            ),
            "top_k": 3,
            "thread_id": thread_id,
            "actor_id": (
                "reviewer-user"
            ),
            "actor_roles": [
                "HealthcareRAG.Reviewer"
            ],
        },
        config=config,
    )

    assert first_result.get(
        "__interrupt__"
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

    assert (
        resumed.get(
            "needs_human_review"
        )
        is False
    )

    assert resumed.get(
        "answer"
    )

    citations = resumed.get(
        "citations",
        [],
    )

    assert len(
        citations
    ) == 1

    assert (
        citations[0][
            "chunk_id"
        ]
        == METFORMIN_CHUNK_ID
    )


def test_human_review_rejection_refuses_answer(
    monkeypatch,
):
    graph = build_test_graph(
        monkeypatch
    )

    thread_id = (
        "test-hitl-reject"
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    first_result = graph.invoke(
        {
            "question": (
                "The policy says metformin "
                "must be stopped 48 hours "
                "before surgery, correct?"
            ),
            "top_k": 3,
            "thread_id": thread_id,
            "actor_id": (
                "reviewer-user"
            ),
            "actor_roles": [
                "HealthcareRAG.Reviewer"
            ],
        },
        config=config,
    )

    assert first_result.get(
        "__interrupt__"
    )

    resumed = graph.invoke(
        Command(
            resume={
                "approved": False,
            }
        ),
        config=config,
    )

    assert (
        resumed.get(
            "review_decision"
        )
        == "rejected"
    )

    assert (
        resumed.get(
            "answer"
        )
        == (
            "I cannot find sufficient "
            "information in the approved "
            "knowledge base."
        )
    )

    assert (
        resumed.get(
            "citations"
        )
        == []
    )
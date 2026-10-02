from __future__ import annotations

from pathlib import Path

from app.persistence.review_queue import (
    ReviewQueueStore,
)


def create_store(
    tmp_path: Path,
) -> ReviewQueueStore:

    return ReviewQueueStore(
        tmp_path
        / "review_queue.db"
    )


def test_register_review(
    tmp_path,
):

    store = create_store(
        tmp_path
    )

    review = store.register_review(
        thread_id="thread-001",
        question=(
            "The policy says metformin "
            "must be stopped 48 hours "
            "before surgery, correct?"
        ),
        risk_level="HIGH",
        risk_reason=(
            "Evidence conflict."
        ),
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    assert (
        review["thread_id"]
        == "thread-001"
    )

    assert (
        review["status"]
        == "pending"
    )

    assert (
        review["risk_level"]
        == "HIGH"
    )


def test_get_review(
    tmp_path,
):

    store = create_store(
        tmp_path
    )

    store.register_review(
        thread_id="thread-002",
        question="Question",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    review = store.get_review(
        "thread-002"
    )

    assert review is not None

    assert (
        review["question"]
        == "Question"
    )


def test_list_pending_reviews(
    tmp_path,
):

    store = create_store(
        tmp_path
    )

    store.register_review(
        thread_id="thread-001",
        question="Question 1",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    store.register_review(
        thread_id="thread-002",
        question="Question 2",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-002",
    )

    reviews = store.list_reviews(
        status="pending"
    )

    assert (
        len(
            reviews
        )
        == 2
    )


def test_complete_review_approved(
    tmp_path,
):

    store = create_store(
        tmp_path
    )

    store.register_review(
        thread_id="thread-003",
        question="Question",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    result = store.complete_review(
        thread_id="thread-003",
        approved=True,
        reviewer_id="reviewer-001",
    )

    assert (
        result["status"]
        == "approved"
    )

    assert (
        result["decision"]
        == "approved"
    )

    assert (
        result["reviewer_id"]
        == "reviewer-001"
    )

    assert (
        result["reviewed_at"]
        is not None
    )


def test_complete_review_rejected(
    tmp_path,
):

    store = create_store(
        tmp_path
    )

    store.register_review(
        thread_id="thread-004",
        question="Question",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    result = store.complete_review(
        thread_id="thread-004",
        approved=False,
        reviewer_id="reviewer-002",
    )

    assert (
        result["status"]
        == "rejected"
    )

    assert (
        result["decision"]
        == "rejected"
    )


def test_stats(
    tmp_path,
):

    store = create_store(
        tmp_path
    )

    store.register_review(
        thread_id="thread-001",
        question="Question 1",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    store.register_review(
        thread_id="thread-002",
        question="Question 2",
        risk_level="HIGH",
        risk_reason="Reason",
        evidence_strength="STRONG",
        requested_by="user-001",
    )

    store.complete_review(
        thread_id="thread-002",
        approved=True,
        reviewer_id="reviewer-001",
    )

    stats = store.stats()

    assert (
        stats["pending"]
        == 1
    )

    assert (
        stats["approved"]
        == 1
    )

    assert (
        stats["rejected"]
        == 0
    )

    assert (
        stats["total"]
        == 2
    )
from __future__ import annotations

from app.governance.evidence_provenance import (
    build_evidence_provenance,
    normalize_citation,
)


def test_fully_traceable_citation():

    result = normalize_citation(
        {
            "document_id":
                "POL-DM-001",

            "chunk_id":
                "POL-DM-001-C0001",

            "title":
                "Diabetes Management Policy",

            "section":
                "Perioperative Medication",

            "version":
                "1.0",

            "excerpt":
                (
                    "Metformin should be "
                    "stopped on the morning "
                    "of surgery."
                ),
        }
    )

    assert (
        result.policy_id
        == "POL-DM-001"
    )

    assert (
        result.chunk_id
        == "POL-DM-001-C0001"
    )

    assert (
        result.traceability
        == "TRACEABLE"
    )


def test_partial_traceability():

    result = normalize_citation(
        {
            "document_id":
                "POL-IC-001",
        }
    )

    assert (
        result.traceability
        == "PARTIAL"
    )


def test_limited_traceability():

    result = normalize_citation(
        {
            "title":
                "Unknown document",
        }
    )

    assert (
        result.traceability
        == "LIMITED"
    )


def test_provenance_summary():

    result = build_evidence_provenance(
        [
            {
                "document_id":
                    "POL-DM-001",

                "chunk_id":
                    "POL-DM-001-C0001",
            },
            {
                "document_id":
                    "POL-IC-001",
            },
            {
                "title":
                    "Unknown",
            },
        ]
    )

    assert (
        result["source_count"]
        == 3
    )

    assert (
        result["traceable_count"]
        == 1
    )

    assert (
        result["partial_count"]
        == 1
    )

    assert (
        result["limited_count"]
        == 1
    )

    assert (
        result["policy_ids"]
        == [
            "POL-DM-001",
            "POL-IC-001",
        ]
    )
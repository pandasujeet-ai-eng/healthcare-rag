from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
)

from typing import (
    Any,
)


MAX_EXCERPT_LENGTH = 1200


@dataclass(
    frozen=True
)
class EvidenceProvenanceItem:

    policy_id: str | None

    chunk_id: str | None

    title: str | None

    section: str | None

    version: str | None

    effective_date: str | None

    page: str | None

    source_name: str | None

    source_url: str | None

    excerpt: str | None

    traceability: str


def _clean(
    value: Any,
) -> str | None:

    if value is None:

        return None

    text = str(
        value
    ).strip()

    if not text:

        return None

    return text


def _first_value(
    source: dict[str, Any],
    *keys: str,
) -> str | None:

    for key in keys:

        value = _clean(
            source.get(
                key
            )
        )

        if value:

            return value

    return None


def _truncate_excerpt(
    value: str | None,
) -> str | None:

    if not value:

        return None

    if (
        len(
            value
        )
        <= MAX_EXCERPT_LENGTH
    ):

        return value

    return (
        value[
            :MAX_EXCERPT_LENGTH
        ].rstrip()
        + "..."
    )


def normalize_citation(
    citation: dict[str, Any],
) -> EvidenceProvenanceItem:

    policy_id = _first_value(
        citation,
        "document_id",
        "policy_id",
        "policyId",
        "source_document_id",
    )

    chunk_id = _first_value(
        citation,
        "chunk_id",
        "chunkId",
        "source_chunk_id",
    )

    title = _first_value(
        citation,
        "title",
        "document_title",
        "policy_title",
        "name",
    )

    section = _first_value(
        citation,
        "section",
        "section_name",
        "heading",
    )

    version = _first_value(
        citation,
        "version",
        "policy_version",
        "document_version",
    )

    effective_date = _first_value(
        citation,
        "effective_date",
        "effectiveDate",
        "policy_effective_date",
    )

    page = _first_value(
        citation,
        "page",
        "page_number",
        "pageNumber",
    )

    source_name = _first_value(
        citation,
        "source_name",
        "source",
        "file_name",
        "filename",
    )

    source_url = _first_value(
        citation,
        "source_url",
        "url",
        "document_url",
    )

    excerpt = _first_value(
        citation,
        "excerpt",
        "snippet",
        "content",
        "text",
        "chunk_text",
    )

    excerpt = _truncate_excerpt(
        excerpt
    )

    if (
        policy_id
        and chunk_id
    ):

        traceability = (
            "TRACEABLE"
        )

    elif (
        policy_id
        or chunk_id
    ):

        traceability = (
            "PARTIAL"
        )

    else:

        traceability = (
            "LIMITED"
        )

    return EvidenceProvenanceItem(
        policy_id=policy_id,
        chunk_id=chunk_id,
        title=title,
        section=section,
        version=version,
        effective_date=effective_date,
        page=page,
        source_name=source_name,
        source_url=source_url,
        excerpt=excerpt,
        traceability=traceability,
    )


def build_evidence_provenance(
    citations: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    items = [
        normalize_citation(
            citation
        )
        for citation
        in citations
    ]

    traceable_count = sum(
        1
        for item
        in items
        if (
            item.traceability
            == "TRACEABLE"
        )
    )

    partial_count = sum(
        1
        for item
        in items
        if (
            item.traceability
            == "PARTIAL"
        )
    )

    limited_count = sum(
        1
        for item
        in items
        if (
            item.traceability
            == "LIMITED"
        )
    )

    policy_ids = sorted(
        {
            item.policy_id
            for item
            in items
            if item.policy_id
        }
    )

    return {
        "source_count": (
            len(
                items
            )
        ),
        "traceable_count": (
            traceable_count
        ),
        "partial_count": (
            partial_count
        ),
        "limited_count": (
            limited_count
        ),
        "policy_ids": (
            policy_ids
        ),
        "items": [
            asdict(
                item
            )
            for item
            in items
        ],
    }
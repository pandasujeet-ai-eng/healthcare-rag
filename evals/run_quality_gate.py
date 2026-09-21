import json
import sys
from pathlib import Path
from typing import Any


from app.chains.rag_chain import answer_question


DATASET_PATH = Path("evals/datasets/rag_quality_eval.json")

REFUSAL_MESSAGE = (
    "I cannot find sufficient information in the approved knowledge base."
)


def load_dataset() -> list[dict[str, Any]]:
    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def contains_expected_phrases(
    answer: str,
    phrases: list[str],
) -> bool:
    normalized_answer = answer.lower()

    return all(
        phrase.lower() in normalized_answer
        for phrase in phrases
    )


def extract_chunk_id(
    chunk: Any,
) -> str | None:
    """
    Extract chunk_id from several possible retrieval result shapes.

    Supported examples:

    LangChain Document:
        chunk.metadata["chunk_id"]

    Nested dictionary:
        chunk["metadata"]["chunk_id"]

    Flat dictionary:
        chunk["chunk_id"]

    Dictionary using id:
        chunk["id"]
    """

    if chunk is None:
        return None

    # ---------------------------------------------------------
    # LangChain Document or object with metadata attribute
    # ---------------------------------------------------------
    metadata = getattr(
        chunk,
        "metadata",
        None,
    )

    if isinstance(metadata, dict):
        chunk_id = metadata.get(
            "chunk_id"
        )

        if chunk_id:
            return str(chunk_id)

    # ---------------------------------------------------------
    # Dictionary
    # ---------------------------------------------------------
    if isinstance(chunk, dict):

        # Flat chunk_id
        chunk_id = chunk.get(
            "chunk_id"
        )

        if chunk_id:
            return str(chunk_id)

        # Nested metadata
        nested_metadata = chunk.get(
            "metadata"
        )

        if isinstance(
            nested_metadata,
            dict,
        ):
            chunk_id = nested_metadata.get(
                "chunk_id"
            )

            if chunk_id:
                return str(chunk_id)

        # Some retrieval implementations use id
        chunk_id = chunk.get(
            "id"
        )

        if chunk_id:
            return str(chunk_id)

    return None


def retrieved_chunk_ids(
    result: dict[str, Any],
) -> list[str]:

    chunks = result.get(
        "retrieved_chunks",
        [],
    )

    ids: list[str] = []

    for chunk in chunks:

        chunk_id = extract_chunk_id(
            chunk
        )

        if chunk_id:
            ids.append(chunk_id)

    return ids


def extract_citation_chunk_id(
    citation: Any,
) -> str | None:

    if citation is None:
        return None

    if isinstance(citation, dict):

        chunk_id = citation.get(
            "chunk_id"
        )

        if chunk_id:
            return str(chunk_id)

        metadata = citation.get(
            "metadata"
        )

        if isinstance(metadata, dict):

            chunk_id = metadata.get(
                "chunk_id"
            )

            if chunk_id:
                return str(chunk_id)

    chunk_id = getattr(
        citation,
        "chunk_id",
        None,
    )

    if chunk_id:
        return str(chunk_id)

    metadata = getattr(
        citation,
        "metadata",
        None,
    )

    if isinstance(metadata, dict):

        chunk_id = metadata.get(
            "chunk_id"
        )

        if chunk_id:
            return str(chunk_id)

    return None


def citation_chunk_ids(
    result: dict[str, Any],
) -> list[str]:

    citations = result.get(
        "citations",
        [],
    )

    ids: list[str] = []

    for citation in citations:

        chunk_id = extract_citation_chunk_id(
            citation
        )

        if chunk_id:
            ids.append(chunk_id)

    return ids


def evaluate_case(
    case: dict[str, Any],
) -> dict[str, Any]:

    case_id = case["id"]
    question = case["question"]

    expected_chunk_id = case.get(
        "expected_chunk_id"
    )

    expected_phrases = case.get(
        "expected_answer_contains",
        [],
    )

    should_refuse = case.get(
        "should_refuse",
        False,
    )

    print()
    print("=" * 100)
    print(f"CASE: {case_id}")
    print(f"QUESTION: {question}")
    print("=" * 100)

    result = answer_question(
        question=question,
        top_k=3,
    )

    answer = result.get(
        "answer",
        "",
    ).strip()

    retrieved_ids = retrieved_chunk_ids(
        result
    )

    citation_ids = citation_chunk_ids(
        result
    )

    actual_refusal = (
        answer == REFUSAL_MESSAGE
    )

    # ---------------------------------------------------------
    # Retrieval evaluation
    # ---------------------------------------------------------

    if expected_chunk_id:

        retrieval_pass = (
            expected_chunk_id
            in retrieved_ids
        )

    else:
        # For unsupported questions we do not expect a particular
        # retrieved document. Search engines may still return nearest
        # neighbors.
        retrieval_pass = True

    # ---------------------------------------------------------
    # Citation evaluation
    # ---------------------------------------------------------

    if expected_chunk_id:

        citation_pass = (
            expected_chunk_id
            in citation_ids
        )

    else:
        citation_pass = True

    # ---------------------------------------------------------
    # Required answer phrases
    # ---------------------------------------------------------

    if expected_phrases:

        phrase_pass = (
            contains_expected_phrases(
                answer,
                expected_phrases,
            )
        )

    else:
        phrase_pass = True

    # ---------------------------------------------------------
    # Refusal evaluation
    # ---------------------------------------------------------

    if should_refuse:

        refusal_pass = (
            actual_refusal
        )

    else:

        refusal_pass = (
            not actual_refusal
        )

    passed = all(
        [
            retrieval_pass,
            citation_pass,
            phrase_pass,
            refusal_pass,
        ]
    )

    print(f"ANSWER: {answer}")
    print(
        f"RETRIEVED: {retrieved_ids}"
    )
    print(
        f"CITATIONS: {citation_ids}"
    )

    print()

    print(
        f"retrieval_pass={retrieval_pass}"
    )

    print(
        f"citation_pass={citation_pass}"
    )

    print(
        f"phrase_pass={phrase_pass}"
    )

    print(
        f"refusal_pass={refusal_pass}"
    )

    print(
        f"RESULT={'PASS' if passed else 'FAIL'}"
    )

    return {
        "id": case_id,
        "passed": passed,
        "retrieval_pass": retrieval_pass,
        "citation_pass": citation_pass,
        "phrase_pass": phrase_pass,
        "refusal_pass": refusal_pass,
        "answer": answer,
        "retrieved_chunk_ids": retrieved_ids,
        "citation_chunk_ids": citation_ids,
    }


def main() -> None:

    cases = load_dataset()

    results: list[dict[str, Any]] = []

    for case in cases:

        try:

            result = evaluate_case(
                case
            )

            results.append(
                result
            )

        except Exception as exc:

            print()
            print(
                f"[ERROR] {case['id']} "
                f"failed with exception:"
            )

            print(str(exc))

            results.append(
                {
                    "id": case["id"],
                    "passed": False,
                    "exception": str(exc),
                }
            )

    total = len(results)

    passed = sum(
        1
        for result in results
        if result.get(
            "passed"
        )
    )

    failed = (
        total - passed
    )

    pass_rate = (
        passed / total
        if total
        else 0
    )

    print()
    print("=" * 100)
    print(
        "RAG QUALITY GATE SUMMARY"
    )
    print("=" * 100)

    print(
        f"Total cases : {total}"
    )

    print(
        f"Passed      : {passed}"
    )

    print(
        f"Failed      : {failed}"
    )

    print(
        f"Pass rate   : "
        f"{pass_rate:.2%}"
    )

    failed_cases = [
        result["id"]
        for result in results
        if not result.get(
            "passed"
        )
    ]

    if failed_cases:

        print(
            "Failed cases : "
            + ", ".join(
                failed_cases
            )
        )

    print("=" * 100)

    if failed > 0:

        print(
            "QUALITY GATE: FAILED"
        )

        sys.exit(1)

    print(
        "QUALITY GATE: PASSED"
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
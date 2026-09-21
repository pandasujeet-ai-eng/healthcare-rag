import json
from pathlib import Path

from app.chains.rag_chain import (
    answer_question,
    REFUSAL_MESSAGE,
)


DATASET = Path(
    "evals/datasets/rag_quality_eval.json"
)


def normalize(text: str) -> str:
    return " ".join(
        text.lower().strip().split()
    )


def contains_expected_chunk(
    result: dict,
    expected_chunk_id: str | None,
) -> bool:

    if expected_chunk_id is None:
        return True

    retrieved_ids = [
        doc["chunk_id"]
        for doc in result["retrieved_chunks"]
    ]

    return expected_chunk_id in retrieved_ids


def citation_contains_expected(
    result: dict,
    expected_chunk_id: str | None,
) -> bool:

    if expected_chunk_id is None:
        return True

    citation_ids = [
        citation["chunk_id"]
        for citation in result["citations"]
    ]

    return expected_chunk_id in citation_ids


def refusal_correct(
    result: dict,
    should_answer: bool,
) -> bool:

    answer = normalize(
        result["answer"]
    )

    expected_refusal = normalize(
        REFUSAL_MESSAGE
    )

    if should_answer:
        return answer != expected_refusal

    return answer == expected_refusal


def main():

    dataset = json.loads(
        DATASET.read_text(
            encoding="utf-8"
        )
    )

    total = len(dataset)

    retrieval_hits = 0
    citation_hits = 0
    refusal_hits = 0

    print("=" * 100)
    print("STEP 5 - LOCAL RAG EVALUATION")
    print("=" * 100)

    for item in dataset:

        result = answer_question(
            item["question"]
        )

        retrieval_ok = (
            contains_expected_chunk(
                result,
                item["expected_chunk_id"],
            )
        )

        citation_ok = (
            citation_contains_expected(
                result,
                item["expected_chunk_id"],
            )
        )

        refusal_ok = (
            refusal_correct(
                result,
                item["should_answer"],
            )
        )

        retrieval_hits += int(
            retrieval_ok
        )

        citation_hits += int(
            citation_ok
        )

        refusal_hits += int(
            refusal_ok
        )

        print()
        print("-" * 100)
        print(f"ID       : {item['id']}")
        print(f"TYPE     : {item['type']}")
        print(
            f"QUESTION : "
            f"{item['question']}"
        )
        print()
        print(
            f"RETRIEVAL : "
            f"{'PASS' if retrieval_ok else 'FAIL'}"
        )
        print(
            f"CITATION  : "
            f"{'PASS' if citation_ok else 'FAIL'}"
        )
        print(
            f"REFUSAL   : "
            f"{'PASS' if refusal_ok else 'FAIL'}"
        )
        print()
        print("ANSWER:")
        print(result["answer"])

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    print(
        f"Retrieval accuracy : "
        f"{retrieval_hits / total:.2%}"
    )

    print(
        f"Citation accuracy  : "
        f"{citation_hits / total:.2%}"
    )

    print(
        f"Refusal accuracy   : "
        f"{refusal_hits / total:.2%}"
    )


if __name__ == "__main__":
    main()
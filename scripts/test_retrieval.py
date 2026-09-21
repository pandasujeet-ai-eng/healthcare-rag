import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "text-embedding-3-small",
)

AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
AZURE_SEARCH_API_KEY = os.environ["AZURE_SEARCH_API_KEY"]
AZURE_SEARCH_INDEX_NAME = os.getenv(
    "AZURE_SEARCH_INDEX_NAME",
    "healthcare-policies-dev",
)

EVAL_FILE = Path("evals/datasets/retrieval_eval.json")


def get_openai_client():
    return OpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        base_url=AZURE_OPENAI_ENDPOINT.rstrip("/") + "/openai/v1/",
    )


def get_search_client():
    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY),
    )


def embed_query(client, text):
    response = client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text,
    )

    return response.data[0].embedding


def keyword_search(search_client, query, top_k=3):
    results = search_client.search(
        search_text=query,
        select=[
            "chunk_id",
            "document_id",
            "title",
            "section",
            "content",
        ],
        top=top_k,
    )

    return list(results)


def vector_search(
    search_client,
    query_vector,
    top_k=3,
):
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector",
        kind="vector",
    )

    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=[
            "chunk_id",
            "document_id",
            "title",
            "section",
            "content",
        ],
        top=top_k,
    )

    return list(results)


def hybrid_search(
    search_client,
    query,
    query_vector,
    top_k=3,
):
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector",
        kind="vector",
    )

    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=[
            "chunk_id",
            "document_id",
            "title",
            "section",
            "content",
        ],
        top=top_k,
    )

    return list(results)


def get_rank(results, expected_chunk_id):
    for rank, result in enumerate(results, start=1):
        if result["chunk_id"] == expected_chunk_id:
            return rank

    return None


def reciprocal_rank(rank):
    if rank is None:
        return 0.0

    return 1.0 / rank


def main():

    dataset = json.loads(
        EVAL_FILE.read_text(encoding="utf-8")
    )

    openai_client = get_openai_client()
    search_client = get_search_client()

    modes = {
        "keyword": [],
        "vector": [],
        "hybrid": [],
    }

    print("=" * 110)
    print("STEP 3E - RETRIEVAL EVALUATION")
    print("=" * 110)

    for item in dataset:

        question = item["question"]
        expected = item["expected_chunk_id"]

        print()
        print("=" * 110)
        print(f"{item['id']} - {question}")
        print(f"EXPECTED: {expected}")
        print("=" * 110)

        query_vector = embed_query(
            openai_client,
            question,
        )

        results_by_mode = {
            "keyword": keyword_search(
                search_client,
                question,
                top_k=3,
            ),

            "vector": vector_search(
                search_client,
                query_vector,
                top_k=3,
            ),

            "hybrid": hybrid_search(
                search_client,
                question,
                query_vector,
                top_k=3,
            ),
        }

        for mode, results in results_by_mode.items():

            print()
            print(f"--- {mode.upper()} ---")

            for rank, result in enumerate(results, start=1):
                print(
                    f"{rank}. "
                    f"{result['chunk_id']} "
                    f"score={result.get('@search.score')}"
                )

            rank = get_rank(
                results,
                expected,
            )

            modes[mode].append(rank)

            print(
                f"Expected rank: "
                f"{rank if rank else 'NOT FOUND'}"
            )

    print()
    print("=" * 110)
    print("FINAL METRICS")
    print("=" * 110)

    total = len(dataset)

    for mode, ranks in modes.items():

        recall_1 = sum(
            1 for r in ranks
            if r == 1
        ) / total

        recall_3 = sum(
            1 for r in ranks
            if r is not None and r <= 3
        ) / total

        mrr = sum(
            reciprocal_rank(r)
            for r in ranks
        ) / total

        print()
        print(mode.upper())
        print(f"Recall@1 : {recall_1:.2%}")
        print(f"Recall@3 : {recall_3:.2%}")
        print(f"MRR      : {mrr:.4f}")


if __name__ == "__main__":
    main()
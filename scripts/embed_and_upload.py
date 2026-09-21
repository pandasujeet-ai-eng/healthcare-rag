import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "text-embedding-3-small",
)

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_API_KEY = os.environ["AZURE_SEARCH_API_KEY"]
SEARCH_INDEX_NAME = os.getenv(
    "AZURE_SEARCH_INDEX_NAME",
    "healthcare-policies-dev",
)

CHUNKS_FILE = Path("data/processed/chunks.json")

EXPECTED_VECTOR_DIMENSIONS = 1536


def get_openai_client() -> OpenAI:
    base_url = AZURE_OPENAI_ENDPOINT.rstrip("/") + "/openai/v1/"

    return OpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        base_url=base_url,
    )


def get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )


def load_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"{CHUNKS_FILE} not found. "
            "Run python -m scripts.export_chunks first."
        )

    return json.loads(
        CHUNKS_FILE.read_text(encoding="utf-8")
    )


def create_embedding(
    client: OpenAI,
    text: str,
) -> list[float]:

    response = client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text,
    )

    vector = response.data[0].embedding

    if len(vector) != EXPECTED_VECTOR_DIMENSIONS:
        raise ValueError(
            f"Embedding dimension mismatch. "
            f"Expected={EXPECTED_VECTOR_DIMENSIONS}, "
            f"Actual={len(vector)}"
        )

    return vector


def build_search_document(
    chunk: dict,
    vector: list[float],
) -> dict:

    md = chunk["metadata"]

    return {
        "chunk_id": md["chunk_id"],
        "document_id": md["document_id"],
        "title": md["title"],
        "version": md["version"],
        "section": md["section"],
        "page": md["page"],
        "source_file": md["source_file"],
        "chunk_index": md["chunk_index"],
        "content": chunk["content"],
        "content_vector": vector,
    }


def main():
    print("=" * 100)
    print("STEP 3D - EMBEDDING + AZURE AI SEARCH UPLOAD")
    print("=" * 100)

    chunks = load_chunks()

    print(f"Chunks loaded             : {len(chunks)}")
    print(f"Embedding deployment      : {EMBEDDING_DEPLOYMENT}")
    print(f"Azure Search index        : {SEARCH_INDEX_NAME}")
    print(f"Expected vector dimensions: {EXPECTED_VECTOR_DIMENSIONS}")

    openai_client = get_openai_client()
    search_client = get_search_client()

    search_documents = []

    for idx, chunk in enumerate(chunks, start=1):

        md = chunk["metadata"]

        print()
        print("-" * 100)
        print(
            f"[{idx}/{len(chunks)}] "
            f"Embedding {md['chunk_id']}"
        )

        vector = create_embedding(
            openai_client,
            chunk["content"],
        )

        print(f"Vector dimensions: {len(vector)}")
        print(
            "Vector sample    : "
            f"{vector[:5]}"
        )

        document = build_search_document(
            chunk,
            vector,
        )

        search_documents.append(document)

    print()
    print("=" * 100)
    print("UPLOADING DOCUMENTS TO AZURE AI SEARCH")
    print("=" * 100)

    results = search_client.upload_documents(
        documents=search_documents
    )

    success_count = 0
    failure_count = 0

    for result in results:
        if result.succeeded:
            success_count += 1
            print(
                f"[SUCCESS] key={result.key}"
            )
        else:
            failure_count += 1
            print(
                f"[FAILED] key={result.key} "
                f"error={result.error_message}"
            )

    print()
    print("=" * 100)
    print("UPLOAD SUMMARY")
    print("=" * 100)
    print(f"Total records : {len(results)}")
    print(f"Succeeded     : {success_count}")
    print(f"Failed        : {failure_count}")

    if failure_count > 0:
        raise RuntimeError(
            f"{failure_count} Azure AI Search uploads failed."
        )

    print()
    print("STEP 3D COMPLETED SUCCESSFULLY")
    print("=" * 100)


if __name__ == "__main__":
    main()
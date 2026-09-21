import os

from dotenv import load_dotenv
from langsmith import traceable
from openai import OpenAI
from opentelemetry import trace

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery


load_dotenv()


AZURE_OPENAI_ENDPOINT = os.environ[
    "AZURE_OPENAI_ENDPOINT"
]

AZURE_OPENAI_API_KEY = os.environ[
    "AZURE_OPENAI_API_KEY"
]

EMBEDDING_DEPLOYMENT = os.environ[
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
]

AZURE_SEARCH_ENDPOINT = os.environ[
    "AZURE_SEARCH_ENDPOINT"
]

AZURE_SEARCH_API_KEY = os.environ[
    "AZURE_SEARCH_API_KEY"
]

AZURE_SEARCH_INDEX_NAME = os.environ[
    "AZURE_SEARCH_INDEX_NAME"
]


openai_client = OpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    base_url=(
        AZURE_OPENAI_ENDPOINT.rstrip("/")
        + "/openai/v1/"
    ),
)


search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(
        AZURE_SEARCH_API_KEY
    ),
)


azure_retrieval_tracer = trace.get_tracer(
    "healthcare-rag.retrieval"
)


@traceable(
    name="embed_query",
    run_type="embedding",
)
def embed_query(
    text: str,
) -> list[float]:
    """
    Convert the user query into an embedding vector.

    LangSmith records this as an embedding span.
    Azure Monitor captures the custom OTel span.
    """

    with azure_retrieval_tracer.start_as_current_span(
        "azure_openai_query_embedding"
    ) as span:

        span.set_attribute(
            "ai.operation",
            "embedding"
        )

        span.set_attribute(
            "ai.embedding_deployment",
            EMBEDDING_DEPLOYMENT
        )

        response = openai_client.embeddings.create(
            model=EMBEDDING_DEPLOYMENT,
            input=text,
        )

        vector = response.data[0].embedding

        span.set_attribute(
            "ai.embedding_dimensions",
            len(vector)
        )

        return vector


@traceable(
    name="azure_hybrid_retrieval",
    run_type="retriever",
)
def retrieve(
    question: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Perform hybrid retrieval against Azure AI Search.

    Hybrid retrieval combines:
    - lexical/full-text search
    - vector similarity search

    Raw user question text is intentionally not added
    as an OpenTelemetry attribute.
    """

    query_vector = embed_query(
        question
    )

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="content_vector",
        kind="vector",
    )

    with azure_retrieval_tracer.start_as_current_span(
        "azure_ai_search_hybrid"
    ) as span:

        span.set_attribute(
            "search.index",
            AZURE_SEARCH_INDEX_NAME
        )

        span.set_attribute(
            "search.mode",
            "hybrid"
        )

        span.set_attribute(
            "search.top_k",
            top_k
        )

        results = search_client.search(
            search_text=question,
            vector_queries=[
                vector_query
            ],
            select=[
                "chunk_id",
                "document_id",
                "title",
                "version",
                "section",
                "page",
                "source_file",
                "content",
            ],
            top=top_k,
        )

        documents = []

        for result in results:
            documents.append(
                {
                    "chunk_id":
                        result["chunk_id"],

                    "document_id":
                        result["document_id"],

                    "title":
                        result["title"],

                    "version":
                        result["version"],

                    "section":
                        result["section"],

                    "page":
                        result["page"],

                    "source_file":
                        result["source_file"],

                    "content":
                        result["content"],

                    "score":
                        result.get(
                            "@search.score"
                        ),
                }
            )

        span.set_attribute(
            "search.result_count",
            len(documents)
        )

        if documents:
            top_result = documents[0]

            span.set_attribute(
                "search.top_document_id",
                top_result["document_id"]
            )

            span.set_attribute(
                "search.top_chunk_id",
                top_result["chunk_id"]
            )

            if (
                top_result.get("score")
                is not None
            ):
                span.set_attribute(
                    "search.top_score",
                    float(
                        top_result["score"]
                    )
                )

        return documents
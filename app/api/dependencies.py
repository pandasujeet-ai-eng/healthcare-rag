import os

from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


load_dotenv()


def get_search_client() -> SearchClient:
    search_endpoint = os.environ[
        "AZURE_SEARCH_ENDPOINT"
    ]

    search_api_key = os.environ[
        "AZURE_SEARCH_API_KEY"
    ]

    search_index_name = os.environ[
        "AZURE_SEARCH_INDEX_NAME"
    ]

    return SearchClient(
        endpoint=search_endpoint,
        index_name=search_index_name,
        credential=AzureKeyCredential(
            search_api_key
        ),
    )


def check_readiness() -> dict:
    """
    Verify that the application can reach
    Azure AI Search.

    We intentionally avoid calling the LLM
    from the readiness endpoint because health
    probes may run frequently.
    """

    index_name = os.environ.get(
        "AZURE_SEARCH_INDEX_NAME",
        "unknown",
    )

    try:
        search_client = get_search_client()

        document_count = (
            search_client.get_document_count()
        )

        return {
            "status": "ready",
            "azure_search": "connected",
            "index_name": index_name,
            "document_count": document_count,
        }

    except Exception as exc:
        return {
            "status": "not_ready",
            "azure_search": "unavailable",
            "index_name": index_name,
            "document_count": None,
            "error": str(exc),
        }
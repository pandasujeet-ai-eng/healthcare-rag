import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

load_dotenv()

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_API_KEY = os.environ["AZURE_SEARCH_API_KEY"]
INDEX_NAME = os.getenv(
    "AZURE_SEARCH_INDEX_NAME",
    "healthcare-policies-dev"
)

EMBEDDING_DIMENSIONS = 1536


def create_index():
    credential = AzureKeyCredential(SEARCH_API_KEY)

    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=credential,
    )

    fields = [

        # Unique chunk identifier
        SimpleField(
            name="chunk_id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),

        # Parent document
        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        # Searchable + useful for citations
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="version",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SearchableField(
            name="section",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="page",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),

        SimpleField(
            name="source_file",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="chunk_index",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),

        # Main text for keyword search
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),

        # Embedding vector
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(
                SearchFieldDataType.Single
            ),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="healthcare-vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="healthcare-hnsw"
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="healthcare-vector-profile",
                algorithm_configuration_name="healthcare-hnsw",
            )
        ],
    )

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    result = index_client.create_or_update_index(index)

    print("=" * 80)
    print("AZURE AI SEARCH INDEX")
    print("=" * 80)
    print(f"Index name : {result.name}")
    print(f"Endpoint   : {SEARCH_ENDPOINT}")
    print("Vector dim : 1536")
    print("Algorithm  : HNSW")
    print("Status     : CREATED / UPDATED")
    print("=" * 80)


if __name__ == "__main__":
    create_index()
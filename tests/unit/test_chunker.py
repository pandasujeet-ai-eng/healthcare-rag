import pytest
from app.ingestion.chunker import chunk_document

def build_doc(content):
    return {
        "metadata": {
            "document_id": "POL-TEST-001",
            "title": "Test Policy",
            "version": "1.0",
            "section": "Testing",
            "page": 1,
            "source_file": "test.txt",
        },
        "content": content,
    }

def test_chunker_creates_multiple_chunks():
    chunks = chunk_document(
        build_doc(("Clinical policy statement. " * 100).strip()),
        chunk_size=200,
        chunk_overlap=40,
    )
    assert len(chunks) > 1

def test_metadata_preserved():
    chunks = chunk_document(
        build_doc(("Clinical policy statement. " * 80).strip()),
        chunk_size=180,
        chunk_overlap=30,
    )
    for chunk in chunks:
        assert chunk["metadata"]["document_id"] == "POL-TEST-001"
        assert chunk["metadata"]["section"] == "Testing"

def test_chunk_ids_unique():
    chunks = chunk_document(
        build_doc(("Clinical policy statement. " * 80).strip()),
        chunk_size=180,
        chunk_overlap=30,
    )
    ids = [c["metadata"]["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))

def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_document(
            build_doc("abc"),
            chunk_size=100,
            chunk_overlap=100,
        )

def test_empty_document():
    with pytest.raises(ValueError):
        chunk_document(
            build_doc("   "),
            chunk_size=100,
            chunk_overlap=20,
        )

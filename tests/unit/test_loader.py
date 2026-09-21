from app.ingestion.loader import load_text_document

def test_loader_extracts_metadata(tmp_path):
    path = tmp_path / "policy.txt"
    path.write_text(
        """Document ID: POL-TEST-001
Title: Test Policy
Version: 1.0
Section: Testing
Page: 7

This is the body.
""",
        encoding="utf-8",
    )

    doc = load_text_document(path)

    assert doc["metadata"]["document_id"] == "POL-TEST-001"
    assert doc["metadata"]["page"] == 7
    assert doc["content"] == "This is the body."

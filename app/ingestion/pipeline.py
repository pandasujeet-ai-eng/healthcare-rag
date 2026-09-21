from pathlib import Path
from app.ingestion.loader import load_text_documents
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_document

def run_ingestion_pipeline(
    input_folder: str | Path,
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[dict]:
    documents = load_text_documents(input_folder)
    all_chunks = []

    for document in documents:
        document["content"] = clean_text(document["content"])

        chunks = chunk_document(
            document,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(chunks)

    return all_chunks

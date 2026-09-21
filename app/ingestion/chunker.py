from copy import deepcopy
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

def build_text_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> RecursiveCharacterTextSplitter:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=DEFAULT_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )

def chunk_document(
    document: dict,
    chunk_size: int = 500,
    chunk_overlap: int = 80,
) -> list[dict]:
    content = document["content"].strip()
    metadata = document["metadata"]

    if not content:
        raise ValueError(
            f"Document {metadata.get('document_id', '<unknown>')} has empty content."
        )

    splitter = build_text_splitter(chunk_size, chunk_overlap)
    parts = splitter.split_text(content)

    chunks = []

    for idx, part in enumerate(parts, start=1):
        part = part.strip()
        if not part:
            continue

        md = deepcopy(metadata)
        md.update({
            "chunk_id": f"{metadata['document_id']}-C{idx:04d}",
            "chunk_index": idx,
            "chunk_size_chars": len(part),
        })

        chunks.append({
            "metadata": md,
            "content": part,
        })

    if not chunks:
        raise ValueError(
            f"Document {metadata.get('document_id', '<unknown>')} produced no chunks."
        )

    return chunks

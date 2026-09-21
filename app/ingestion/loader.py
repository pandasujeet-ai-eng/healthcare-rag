from pathlib import Path
from typing import Any

REQUIRED_METADATA_FIELDS = {
    "Document ID": "document_id",
    "Title": "title",
    "Version": "version",
    "Section": "section",
    "Page": "page",
}

def _parse_metadata_and_body(text: str) -> tuple[dict[str, Any], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    header, sep, body = normalized.partition("\n\n")

    if not sep:
        raise ValueError("Document must contain a blank line between metadata and body.")

    metadata: dict[str, Any] = {}

    for line in header.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key in REQUIRED_METADATA_FIELDS:
            target = REQUIRED_METADATA_FIELDS[key]
            metadata[target] = int(value) if target == "page" else value

    missing = [
        target for target in REQUIRED_METADATA_FIELDS.values()
        if target not in metadata or metadata[target] in ("", None)
    ]
    if missing:
        raise ValueError(f"Missing required metadata: {missing}")

    return metadata, body.strip()

def load_text_document(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    raw_text = path.read_text(encoding="utf-8")

    metadata, content = _parse_metadata_and_body(raw_text)
    metadata["source_file"] = path.name

    return {
        "metadata": metadata,
        "content": content,
    }

def load_text_documents(folder: str | Path) -> list[dict[str, Any]]:
    folder = Path(folder)
    return [load_text_document(p) for p in sorted(folder.glob("*.txt"))]

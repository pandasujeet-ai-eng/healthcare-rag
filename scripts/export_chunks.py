import json
from pathlib import Path
from app.ingestion.pipeline import run_ingestion_pipeline

chunks = run_ingestion_pipeline(
    Path("data/raw"),
    chunk_size=500,
    chunk_overlap=80,
)

output = Path("data/processed/chunks.json")
output.parent.mkdir(parents=True, exist_ok=True)

output.write_text(
    json.dumps(chunks, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(f"Wrote {len(chunks)} chunks to {output}")

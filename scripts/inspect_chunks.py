from collections import Counter
from pathlib import Path
from app.ingestion.pipeline import run_ingestion_pipeline

chunks = run_ingestion_pipeline(
    Path("data/raw"),
    chunk_size=500,
    chunk_overlap=80,
)

print("=" * 100)
print("INGESTION SUMMARY")
print("=" * 100)
print(f"Total chunks: {len(chunks)}")

counts = Counter(c["metadata"]["document_id"] for c in chunks)

print("\nChunks by document:")
for doc_id, count in sorted(counts.items()):
    print(f"  {doc_id}: {count}")

print("\n" + "=" * 100)
print("CHUNK DETAILS")
print("=" * 100)

for c in chunks:
    md = c["metadata"]

    print()
    print(f"Chunk ID   : {md['chunk_id']}")
    print(f"Document ID: {md['document_id']}")
    print(f"Title      : {md['title']}")
    print(f"Version    : {md['version']}")
    print(f"Section    : {md['section']}")
    print(f"Page       : {md['page']}")
    print(f"Source     : {md['source_file']}")
    print(f"Chars      : {md['chunk_size_chars']}")
    print("-" * 100)
    print(c["content"])

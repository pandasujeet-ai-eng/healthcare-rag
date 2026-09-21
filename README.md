# Healthcare RAG — Development Step 2

## Goal

Document ingestion + metadata extraction + cleaning + LangChain chunking.

## Flow

```text
data/raw/*.txt
      ↓
metadata parser
      ↓
text cleaner
      ↓
RecursiveCharacterTextSplitter
      ↓
stable chunk IDs
      ↓
retrieval-ready chunks
```

## Install

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Inspect chunks

```bash
python scripts/inspect_chunks.py
```

## Export chunks

```bash
python scripts/export_chunks.py
```

Output:

```text
data/processed/chunks.json
```

## Run tests

```bash
pytest -q
```

## Current baseline

```text
chunk_size    = 500 characters
chunk_overlap = 80 characters
```

These are experimental starting values, not final production values.

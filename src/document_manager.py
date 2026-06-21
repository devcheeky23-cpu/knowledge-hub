"""Document Manager (#9).

Owns the source-file side of the Knowledge Hub: persisting uploaded Documents,
listing them, deleting them, and rebuilding the vector store from them. The
chunk/vector side lives in src.ingestion — this module orchestrates it.
"""
import os
from pathlib import Path

from src import ingestion


def _source_dir() -> Path:
    path = Path(os.environ.get("SOURCE_DOCS_PATH", "source_docs"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_and_ingest(filename: str, data: bytes) -> int:
    """Persist an uploaded Document, then run it through Ingestion. Returns the
    number of Chunks produced."""
    path = _source_dir() / filename
    path.write_bytes(data)
    return ingestion.ingest(str(path))


def list_documents() -> list[str]:
    """Names of all Documents currently stored, sorted."""
    return sorted(p.name for p in _source_dir().iterdir() if p.is_file())


def delete_document(filename: str) -> None:
    """Remove a Document from the system entirely: its Chunks from the vector
    store and its source file from storage."""
    ingestion.delete_document(filename)
    path = _source_dir() / filename
    if path.exists():
        path.unlink()


def reingest() -> int:
    """Wipe the vector store and rebuild it from every stored Document. Needed
    after a cold start on ephemeral disk. Returns the total Chunk count."""
    ingestion.clear()
    source = _source_dir()
    total = 0
    for name in list_documents():
        total += ingestion.ingest(str(source / name))
    return total

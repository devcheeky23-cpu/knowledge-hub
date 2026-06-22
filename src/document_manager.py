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


def bootstrap() -> bool:
    """Seed the system from the committed seed corpus on a cold start. HF Spaces
    disk is ephemeral, so on first start both the source store and the vector
    store are empty; persist and ingest every file under seed_docs/ so the app is
    queryable and Citations can open full Documents with no manual re-ingest.
    Returns True if it seeded, False if Documents already exist (a warm session
    is preserved)."""
    if list_documents():
        return False
    seed = Path(os.environ.get("SEED_DOCS_PATH", "seed_docs"))
    if not seed.exists():
        return False
    for doc in sorted(seed.iterdir()):
        if doc.is_file():
            save_and_ingest(doc.name, doc.read_bytes())
    return True


def list_documents() -> list[str]:
    """Names of all Documents currently stored, sorted."""
    return sorted(p.name for p in _source_dir().iterdir() if p.is_file())


def get_document_text(filename: str) -> str:
    """Return the full text of a stored Document, so a Citation can resolve back
    to the whole source — not just the retrieved Chunk."""
    path = _source_dir() / filename
    if filename.endswith(".pdf"):
        records = ingestion._parse_pdf(str(path), filename)
        return "\n\n".join(r["text"] for r in records)
    return path.read_text(encoding="utf-8")


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

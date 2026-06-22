import os
import shutil
from pathlib import Path

_MODEL_NAME = "intfloat/multilingual-e5-small"
_embedder = None
_client = None
_collection = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(_MODEL_NAME)
    return _embedder


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb
        db_path = os.environ.get("CHROMA_DB_PATH", ".chroma")
        _client = chromadb.PersistentClient(path=db_path)
        _collection = _client.get_or_create_collection("documents")
    return _collection


def bootstrap_index() -> bool:
    """Seed the working vector store from the committed pre-built index on a cold
    start. HF Spaces disk is ephemeral, so on startup the working store is absent;
    copy the committed seed index into place so the app is queryable with no
    manual re-ingest. Returns True if it seeded, False if a store already exists
    (uploads from a warm session are preserved)."""
    db_path = Path(os.environ.get("CHROMA_DB_PATH", ".chroma"))
    seed_path = Path(os.environ.get("SEED_INDEX_PATH", "seed_index"))
    if db_path.exists() or not seed_path.exists():
        return False
    shutil.copytree(seed_path, db_path)
    return True


def _reset():
    global _client, _collection
    _client = None
    _collection = None
    # Note: _embedder is intentionally NOT reset — model loading takes ~30s
    # and the embedder is stateless across collections.


def _chunk_text(text, chunk_size=750, overlap=100):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def _parse_markdown(content, source_file):
    records = []
    current_heading = ""
    current_lines = []

    for line in content.splitlines():
        if line.startswith("#"):
            if current_lines:
                records.append({
                    "text": "\n".join(current_lines).strip(),
                    "source_file": source_file,
                    "section_heading": current_heading,
                })
                current_lines = []
            current_heading = line.lstrip("#").strip()
        else:
            if line.strip():
                current_lines.append(line)

    if current_lines:
        records.append({
            "text": "\n".join(current_lines).strip(),
            "source_file": source_file,
            "section_heading": current_heading,
        })
    return records


def _parse_plaintext(content, source_file):
    return [{"text": content.strip(), "source_file": source_file, "section_heading": ""}]


def _parse_pdf(file_path, source_file):
    import fitz

    records = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text().strip()
            if text:
                records.append({
                    "text": text,
                    "source_file": source_file,
                    "section_heading": "",
                })
    return records


def ingest(file_path: str, chunk_size: int = 750, overlap: int = 100) -> int:
    source_file = os.path.basename(file_path)

    if file_path.endswith(".pdf"):
        records = _parse_pdf(file_path, source_file)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if file_path.endswith(".md"):
            records = _parse_markdown(content, source_file)
        else:
            records = _parse_plaintext(content, source_file)

    embedder = _get_embedder()
    collection = _get_collection()

    chunk_count = 0
    for record in records:
        chunks = _chunk_text(record["text"], chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            embedding = embedder.encode(chunk).tolist()
            chunk_id = f"{source_file}_{record['section_heading']}_{i}"
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{
                    "source_file": record["source_file"],
                    "section_heading": record["section_heading"],
                }],
            )
            chunk_count += 1

    return chunk_count


def delete_document(source_file: str) -> None:
    """Remove every Chunk belonging to a single source Document."""
    collection = _get_collection()
    collection.delete(where={"source_file": source_file})


def clear() -> None:
    """Drop all Chunks — the destructive first half of a Re-ingest."""
    global _collection
    _get_collection()  # ensure _client is initialised
    _client.delete_collection("documents")
    _collection = None
    _get_collection()  # recreate an empty collection


def query(query_text: str, top_k: int = 5) -> list[dict]:
    embedder = _get_embedder()
    collection = _get_collection()

    embedding = embedder.encode(query_text).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=top_k)

    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append({
            "text": doc,
            "source_file": meta["source_file"],
            "section_heading": meta["section_heading"],
        })
    return output

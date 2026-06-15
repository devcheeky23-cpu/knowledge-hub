import os
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def isolated_chroma(tmp_path, monkeypatch):
    """Each test gets its own ChromaDB path — no shared state."""
    monkeypatch.setenv("CHROMA_DB_PATH", str(tmp_path / "chroma"))
    import src.ingestion as ing
    ing._reset()
    yield
    ing._reset()


def test_ingest_markdown_extracts_section_headings():
    from src.ingestion import ingest, query

    ingest(str(FIXTURES / "sample.md"))

    results = query("how do I cancel an order", top_k=5)

    assert len(results) > 0
    source_files = [r["source_file"] for r in results]
    assert any("sample.md" in f for f in source_files)
    headings = [r["section_heading"] for r in results]
    assert any(h for h in headings), "Expected at least one non-empty section_heading"


def test_ingest_plaintext_stores_source_file_metadata():
    from src.ingestion import ingest, query

    count = ingest(str(FIXTURES / "sample.txt"))

    assert count > 0
    results = query("product catalog API", top_k=5)
    assert len(results) > 0
    assert all("sample.txt" in r["source_file"] for r in results)


def test_query_returns_relevant_chunk():
    from src.ingestion import ingest, query

    ingest(str(FIXTURES / "sample.md"))

    results = query("refund after cancelling order", top_k=3)

    assert len(results) > 0
    top_text = results[0]["text"].lower()
    assert any(word in top_text for word in ["cancel", "refund", "order"])

import importlib
import os
import sys
import types
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_ingestion(monkeypatch, tmp_path):
    """Inject a fake src.ingestion (chromadb is not installed locally) and point
    the source-document store at an isolated tmp dir. Returns the fake so tests
    can inspect how document_manager drove the ingestion pipeline."""
    fake = types.ModuleType("src.ingestion")
    fake.ingest_calls = []
    fake.deleted = []
    fake.cleared = 0

    def ingest(path, chunk_size=750, overlap=100):
        fake.ingest_calls.append(path)
        return 3  # pretend each document produced 3 chunks

    def delete_document(source_file):
        fake.deleted.append(source_file)

    def clear():
        fake.cleared += 1

    fake.ingest = ingest
    fake.delete_document = delete_document
    fake.clear = clear

    import src as src_pkg
    monkeypatch.setitem(sys.modules, "src.ingestion", fake)
    # `from src import ingestion` reads the package attribute, which a prior real
    # import (e.g. the PDF read-back test) pollutes — override it too.
    monkeypatch.setattr(src_pkg, "ingestion", fake, raising=False)
    monkeypatch.setenv("SOURCE_DOCS_PATH", str(tmp_path / "source_docs"))
    sys.modules.pop("src.document_manager", None)
    yield fake


@pytest.fixture
def dm(fake_ingestion):
    import src.document_manager as module

    return importlib.reload(module)


def test_save_and_ingest_persists_file_and_returns_chunk_count(dm, fake_ingestion):
    count = dm.save_and_ingest("orders.md", b"# Orders\nHow to cancel an order.")

    # the uploaded document is persisted so re-ingest can rebuild from it later
    saved = dm.list_documents()
    assert "orders.md" in saved
    # it was run through the ingestion pipeline and the chunk count is surfaced
    assert count == 3
    assert any(path.endswith("orders.md") for path in fake_ingestion.ingest_calls)


def test_delete_document_removes_file_and_its_chunks(dm, fake_ingestion):
    dm.save_and_ingest("orders.md", b"# Orders\ncontent")
    dm.save_and_ingest("refunds.md", b"# Refunds\ncontent")

    dm.delete_document("orders.md")

    # gone from the source store entirely, not merely hidden
    assert dm.list_documents() == ["refunds.md"]
    # and its Chunks were removed from the vector store
    assert fake_ingestion.deleted == ["orders.md"]


def test_get_document_text_returns_full_original_text(dm):
    dm.save_and_ingest("orders.md", b"# Orders\nHow to cancel an order.")

    # a citation resolves back to the whole Document, not just the retrieved Chunk
    full = dm.get_document_text("orders.md")

    assert full == "# Orders\nHow to cancel an order."


def test_get_document_text_extracts_full_text_from_pdf(monkeypatch, tmp_path):
    # uses the real ingestion module (its imports are lazy, so no chromadb needed)
    monkeypatch.setenv("SOURCE_DOCS_PATH", str(tmp_path / "source_docs"))
    sys.modules.pop("src.document_manager", None)
    import src.document_manager as dm
    importlib.reload(dm)

    src_dir = tmp_path / "source_docs"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "sample.pdf").write_bytes((FIXTURES / "sample.pdf").read_bytes())

    full = dm.get_document_text("sample.pdf")

    # full text spans every page, not just one chunk
    assert "cancel an order" in full
    assert "catalog endpoint" in full


def test_bootstrap_seeds_from_seed_docs_on_cold_start(dm, tmp_path, monkeypatch):
    seed = tmp_path / "seed_docs"
    seed.mkdir()
    (seed / "policy.md").write_text("# Refunds\nRefunds within 30 days.")
    monkeypatch.setenv("SEED_DOCS_PATH", str(seed))

    seeded = dm.bootstrap()

    assert seeded is True
    # the seed Document is in the source store, so a Citation can open it
    assert dm.list_documents() == ["policy.md"]
    assert "30 days" in dm.get_document_text("policy.md")


def test_bootstrap_is_noop_when_documents_already_exist(dm, tmp_path, monkeypatch):
    seed = tmp_path / "seed_docs"
    seed.mkdir()
    (seed / "policy.md").write_text("# Refunds\ncontent")
    monkeypatch.setenv("SEED_DOCS_PATH", str(seed))
    dm.save_and_ingest("existing.md", b"# Existing\nan uploaded doc")

    seeded = dm.bootstrap()

    assert seeded is False
    assert dm.list_documents() == ["existing.md"]  # seed not applied over a warm store


def test_reingest_clears_store_then_reingests_every_document(dm, fake_ingestion):
    dm.save_and_ingest("orders.md", b"# Orders\ncontent")
    dm.save_and_ingest("refunds.md", b"# Refunds\ncontent")
    fake_ingestion.ingest_calls.clear()  # ignore the per-upload ingests

    total = dm.reingest()

    # the store is wiped exactly once before rebuilding
    assert fake_ingestion.cleared == 1
    # every stored document is run through ingestion again
    reingested = [os.path.basename(p) for p in fake_ingestion.ingest_calls]
    assert sorted(reingested) == ["orders.md", "refunds.md"]
    # total chunk count across the rebuild is surfaced (3 per document)
    assert total == 6

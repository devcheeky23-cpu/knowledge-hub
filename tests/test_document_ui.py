import sys
import types
from pathlib import Path

import pytest

PAGE = str(Path(__file__).resolve().parent.parent / "pages" / "Manage_Documents.py")


@pytest.fixture
def fake_dm(monkeypatch):
    """Inject a fake src.document_manager so the page can run without chromadb.
    The fake keeps a live document list so delete/re-ingest are observable."""
    fake = types.ModuleType("src.document_manager")
    fake.documents = []
    fake.deleted = []
    fake.reingest_calls = 0

    fake.list_documents = lambda: list(fake.documents)

    def delete_document(name):
        fake.deleted.append(name)
        fake.documents.remove(name)

    def reingest():
        fake.reingest_calls += 1
        return 42

    def save_and_ingest(name, data):
        fake.documents.append(name)
        return 3

    fake.delete_document = delete_document
    fake.reingest = reingest
    fake.save_and_ingest = save_and_ingest

    import src

    # Replace both the sys.modules entry and the package attribute so the page's
    # `from src import document_manager` resolves to the fake even if a prior test
    # already imported the real module.
    monkeypatch.setitem(sys.modules, "src.document_manager", fake)
    monkeypatch.setattr(src, "document_manager", fake, raising=False)
    return fake


def _run(fake_dm):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(PAGE)
    at.run()
    return at


def test_lists_current_documents(fake_dm):
    fake_dm.documents = ["orders.md", "refunds.txt"]

    at = _run(fake_dm)

    rendered = " ".join(m.value for m in at.markdown)
    assert "orders.md" in rendered
    assert "refunds.txt" in rendered


def test_empty_state_message_when_no_documents(fake_dm):
    fake_dm.documents = []

    at = _run(fake_dm)

    assert any("no documents" in i.value.lower() for i in at.info)


def test_delete_button_removes_the_document(fake_dm):
    fake_dm.documents = ["orders.md", "refunds.txt"]

    at = _run(fake_dm)
    button = next(b for b in at.button if b.key == "delete_orders.md")
    button.click().run()

    # the manager was asked to delete exactly that document
    assert fake_dm.deleted == ["orders.md"]
    # and the list re-rendered without it
    rendered = " ".join(m.value for m in at.markdown)
    assert "orders.md" not in rendered
    assert "refunds.txt" in rendered


def test_reingest_button_rebuilds_index_and_reports_success(fake_dm):
    fake_dm.documents = ["orders.md"]

    at = _run(fake_dm)
    button = next(b for b in at.button if b.key == "reingest")
    button.click().run()

    assert fake_dm.reingest_calls == 1
    # the user gets feedback that the rebuild ran, including the chunk count
    assert any("42" in s.value for s in at.success)


def test_uploader_accepts_md_txt_pdf(fake_dm):
    at = _run(fake_dm)

    allowed = {t.lstrip(".") for t in at.file_uploader[0].allowed_type}
    assert allowed == {"md", "txt", "pdf"}


def test_upload_ingests_the_file_and_reports_success(fake_dm):
    at = _run(fake_dm)

    at.file_uploader[0].set_value(("api_spec.md", b"# API\nendpoints", "text/markdown")).run()

    # the document went through save-and-ingest and now appears in the store
    assert "api_spec.md" in fake_dm.documents
    assert any("api_spec.md" in s.value for s in at.success)


def test_upload_is_not_reprocessed_on_a_later_rerun(fake_dm):
    at = _run(fake_dm)

    at.file_uploader[0].set_value(("api_spec.md", b"# API\nendpoints", "text/markdown")).run()
    # a subsequent interaction (e.g. clicking re-ingest) must not re-ingest the
    # still-attached upload — that would create duplicate chunks
    next(b for b in at.button if b.key == "reingest").click().run()

    assert fake_dm.documents.count("api_spec.md") == 1

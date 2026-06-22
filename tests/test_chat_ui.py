import sys
import types
from pathlib import Path

import pytest

from src.answer_engine import Answer, Citation

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture(autouse=True)
def stub_modules(monkeypatch):
    """Inject fake src.ingestion + src.document_manager so the chat page can run
    without chromadb / sentence-transformers installed and without touching the
    real source-document store."""
    import src as src_pkg

    fake_ing = types.ModuleType("src.ingestion")
    fake_ing._get_embedder = lambda: "embedder"
    fake_ing.query = lambda question, top_k=5: []
    monkeypatch.setitem(sys.modules, "src.ingestion", fake_ing)
    monkeypatch.setattr(src_pkg, "ingestion", fake_ing, raising=False)

    fake_dm = types.ModuleType("src.document_manager")
    fake_dm.bootstrap = lambda: False
    fake_dm.get_document_text = lambda name: ""
    monkeypatch.setitem(sys.modules, "src.document_manager", fake_dm)
    monkeypatch.setattr(src_pkg, "document_manager", fake_dm, raising=False)
    yield


def _run(monkeypatch, answer_obj, question):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr("src.answer_engine.answer", lambda q: answer_obj)
    at = AppTest.from_file(APP)
    at.run()
    at.chat_input[0].set_value(question).run()
    return at


def test_found_renders_answer_and_expandable_citation(monkeypatch):
    ans = Answer(
        mode="found",
        answer_text="Open Settings to cancel an order.",
        citations=[
            Citation("orders.md", "Cancelling", "To cancel, open Settings and choose Cancel.")
        ],
    )

    at = _run(monkeypatch, ans, "how do I cancel an order")

    assert any("Open Settings to cancel an order." in m.value for m in at.markdown)
    expanders = [e for e in at.expander if "orders.md" in e.label and "Cancelling" in e.label]
    assert expanders, "expected a citation expander labelled with file + section"
    assert any("To cancel, open Settings" in m.value for m in expanders[0].markdown)


def test_citation_can_reveal_full_source_document(monkeypatch):
    # the full Document is fetched on demand from the document manager
    fake_dm = types.ModuleType("src.document_manager")
    fake_dm.bootstrap = lambda: False
    fake_dm.get_document_text = lambda name: f"FULL TEXT of {name}\nevery line of it."
    monkeypatch.setitem(sys.modules, "src.document_manager", fake_dm)
    import src as src_pkg
    monkeypatch.setattr(src_pkg, "document_manager", fake_dm, raising=False)

    ans = Answer(
        mode="found",
        answer_text="Open Settings to cancel an order.",
        citations=[Citation("orders.md", "Cancelling", "To cancel, open Settings.")],
    )

    at = _run(monkeypatch, ans, "how do I cancel an order")

    # full document stays hidden until the user asks for it
    assert not any("FULL TEXT of orders.md" in m.value for m in at.markdown)

    at.toggle[0].set_value(True).run()

    assert any("FULL TEXT of orders.md" in m.value for m in at.markdown)


def test_abstain_shows_not_found_message_and_no_citations(monkeypatch):
    ans = Answer(
        mode="abstain",
        answer_text="That information is not in the documents.",
        citations=[],
    )

    at = _run(monkeypatch, ans, "what is the stock price")

    assert any("not found" in w.value.lower() for w in at.warning)
    assert at.expander == []


def test_conflict_shows_both_sides_with_their_citations(monkeypatch):
    ans = Answer(
        mode="conflict",
        answer_text="The documents disagree on the refund window.",
        citations=[
            Citation("policy_v1.md", "Refunds", "Refunds within 14 days."),
            Citation("policy_v2.md", "Refunds", "Refunds within 30 days."),
        ],
    )

    at = _run(monkeypatch, ans, "what is the refund window")

    assert any("conflicting" in m.value.lower() for m in at.markdown)
    labels = " ".join(e.label for e in at.expander)
    assert "policy_v1.md" in labels and "policy_v2.md" in labels
    bodies = " ".join(m.value for e in at.expander for m in e.markdown)
    assert "14 days" in bodies and "30 days" in bodies


def test_conversation_history_persists_within_session(monkeypatch):
    from streamlit.testing.v1 import AppTest

    # answer engine echoes the question so each turn is distinguishable
    monkeypatch.setattr(
        "src.answer_engine.answer",
        lambda q: Answer(mode="found", answer_text=f"Answer to: {q}", citations=[]),
    )

    at = AppTest.from_file(APP)
    at.run()
    at.chat_input[0].set_value("first question").run()
    at.chat_input[0].set_value("second question").run()

    rendered = " ".join(m.value for m in at.markdown)
    assert "first question" in rendered
    assert "Answer to: first question" in rendered
    assert "second question" in rendered
    assert "Answer to: second question" in rendered


def test_startup_seeds_from_seed_corpus(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    calls = {"n": 0}

    def counting_bootstrap():
        calls["n"] += 1
        return True

    import src as src_pkg
    fake_dm = types.ModuleType("src.document_manager")
    fake_dm.bootstrap = counting_bootstrap
    fake_dm.get_document_text = lambda name: ""
    monkeypatch.setitem(sys.modules, "src.document_manager", fake_dm)
    monkeypatch.setattr(src_pkg, "document_manager", fake_dm, raising=False)
    monkeypatch.setattr(
        "src.answer_engine.answer",
        lambda q: Answer(mode="found", answer_text="ok", citations=[]),
    )
    st.cache_resource.clear()

    at = AppTest.from_file(APP)
    at.run()

    # the seed corpus is loaded once on cold start, before any query
    assert calls["n"] == 1


def test_embedding_model_loaded_once_across_queries(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    calls = {"n": 0}

    def counting_loader():
        calls["n"] += 1
        return "embedder"

    fake = types.ModuleType("src.ingestion")
    fake._get_embedder = counting_loader
    fake.query = lambda question, top_k=5: []
    monkeypatch.setitem(sys.modules, "src.ingestion", fake)
    monkeypatch.setattr(
        "src.answer_engine.answer",
        lambda q: Answer(mode="found", answer_text="ok", citations=[]),
    )
    st.cache_resource.clear()

    at = AppTest.from_file(APP)
    at.run()
    at.chat_input[0].set_value("q1").run()
    at.chat_input[0].set_value("q2").run()

    assert calls["n"] == 1, f"embedder loaded {calls['n']} times, expected once"

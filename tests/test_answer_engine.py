import json

import httpx
import respx

CHUNKS = [
    {
        "text": "To cancel an order, open Settings and choose Cancel.",
        "source_file": "orders.md",
        "section_heading": "Cancelling",
    },
    {
        "text": "Refunds are issued within 5 business days.",
        "source_file": "orders.md",
        "section_heading": "Refunds",
    },
]


def _llm_reply(payload):
    """A GitHub Models chat-completion whose message content is the JSON the
    answer engine asks the model to produce."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(payload)},
                "finish_reason": "stop",
            }
        ],
    }


def _mock_llm(payload):
    return respx.post(
        "https://models.github.ai/inference/chat/completions"
    ).mock(return_value=httpx.Response(200, json=_llm_reply(payload)))


@respx.mock
def test_found_mode_returns_answer_with_citation(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    import src.answer_engine as engine

    monkeypatch.setattr(engine, "_retrieve", lambda question, top_k: CHUNKS)
    _mock_llm(
        {
            "mode": "found",
            "answer_text": "Open Settings and choose Cancel.",
            "used_chunks": [1],
        }
    )

    answer = engine.answer("how do I cancel an order")

    assert answer.mode == "found"
    assert answer.answer_text == "Open Settings and choose Cancel."
    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.source_file == "orders.md"
    assert citation.section_heading == "Cancelling"
    assert citation.chunk_text == CHUNKS[0]["text"]


@respx.mock
def test_abstain_mode_has_no_citations(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    import src.answer_engine as engine

    monkeypatch.setattr(engine, "_retrieve", lambda question, top_k: CHUNKS)
    _mock_llm(
        {
            "mode": "abstain",
            "answer_text": "That information is not in the documents.",
            "used_chunks": [],
        }
    )

    answer = engine.answer("what is the company's stock price")

    assert answer.mode == "abstain"
    assert answer.citations == []


@respx.mock
def test_prompt_contains_chunks_and_enforces_answer_contract(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    import src.answer_engine as engine

    monkeypatch.setattr(engine, "_retrieve", lambda question, top_k: CHUNKS)
    route = _mock_llm(
        {"mode": "found", "answer_text": "ok", "used_chunks": [1]}
    )

    engine.answer("how do I cancel an order")

    body = json.loads(route.calls.last.request.content)
    prompt = body["messages"][0]["content"]
    # every retrieved chunk's text is in the prompt
    assert CHUNKS[0]["text"] in prompt
    assert CHUNKS[1]["text"] in prompt
    # answer-from-documents-only + abstain rules are stated
    assert "ONLY" in prompt
    assert "abstain" in prompt.lower()


@respx.mock
def test_retrieves_between_4_and_6_chunks(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    import src.answer_engine as engine

    captured = {}

    def spy(question, top_k):
        captured["top_k"] = top_k
        return CHUNKS

    monkeypatch.setattr(engine, "_retrieve", spy)
    _mock_llm({"mode": "found", "answer_text": "ok", "used_chunks": [1]})

    engine.answer("how do I cancel an order")

    assert 4 <= captured["top_k"] <= 6


CONFLICT_CHUNKS = [
    {
        "text": "Refunds are issued within 14 days of purchase.",
        "source_file": "policy_v1.md",
        "section_heading": "Refunds",
    },
    {
        "text": "Refunds are issued within 30 days of purchase.",
        "source_file": "policy_v2.md",
        "section_heading": "Refunds",
    },
]


@respx.mock
def test_prompt_instructs_conflict_detection_without_choosing_a_side(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    import src.answer_engine as engine

    monkeypatch.setattr(engine, "_retrieve", lambda question, top_k: CONFLICT_CHUNKS)
    route = _mock_llm({"mode": "found", "answer_text": "ok", "used_chunks": [1]})

    engine.answer("what is the refund window")

    prompt = json.loads(route.calls.last.request.content)["messages"][0]["content"]
    lower = prompt.lower()
    assert "conflict" in lower
    # the model must be told not to pick a winner
    assert "do not" in lower or "decline" in lower or "without" in lower


@respx.mock
def test_conflict_mode_reports_both_sides_with_citations(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    import src.answer_engine as engine

    monkeypatch.setattr(engine, "_retrieve", lambda question, top_k: CONFLICT_CHUNKS)
    _mock_llm(
        {
            "mode": "conflict",
            "answer_text": "policy_v1 says 14 days; policy_v2 says 30 days.",
            "used_chunks": [1, 2],
        }
    )

    answer = engine.answer("what is the refund window")

    assert answer.mode == "conflict"
    assert len(answer.citations) == 2
    sources = {c.source_file for c in answer.citations}
    assert sources == {"policy_v1.md", "policy_v2.md"}
    texts = {c.chunk_text for c in answer.citations}
    assert texts == {CONFLICT_CHUNKS[0]["text"], CONFLICT_CHUNKS[1]["text"]}

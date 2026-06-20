import json

import httpx
import pytest
import respx


def _completion_response(content):
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }


@respx.mock
def test_complete_sends_prompt_to_github_models_and_returns_text(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    route = respx.post("https://models.github.ai/inference/chat/completions").mock(
        return_value=httpx.Response(200, json=_completion_response("pong"))
    )

    from src.llm_client import complete

    answer = complete("ping")

    assert answer == "pong"
    assert route.called
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer test-token"
    body = json.loads(request.content)
    assert body["model"] == "openai/gpt-4o-mini"
    assert body["messages"] == [{"role": "user", "content": "ping"}]


@respx.mock
def test_provider_is_switchable_via_config_with_no_code_change(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "groq-token")
    monkeypatch.delenv("LLM_MODEL", raising=False)

    route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=_completion_response("hi"))
    )

    from src.llm_client import complete

    answer = complete("ping")

    assert answer == "hi"
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer groq-token"
    body = json.loads(request.content)
    assert body["model"] == "llama-3.1-8b-instant"


@respx.mock
def test_model_is_overridable_via_config(monkeypatch):
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "test-token")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o")

    route = respx.post("https://models.github.ai/inference/chat/completions").mock(
        return_value=httpx.Response(200, json=_completion_response("ok"))
    )

    from src.llm_client import complete

    complete("ping")

    body = json.loads(route.calls.last.request.content)
    assert body["model"] == "openai/gpt-4o"


@respx.mock
def test_gemini_is_available_as_an_alternative_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-token")
    monkeypatch.delenv("LLM_MODEL", raising=False)

    route = respx.post(
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    ).mock(return_value=httpx.Response(200, json=_completion_response("hi")))

    from src.llm_client import complete

    answer = complete("ping")

    assert answer == "hi"
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer gemini-token"
    body = json.loads(request.content)
    assert body["model"] == "gemini-1.5-flash"


def test_missing_token_raises_clear_error(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GITHUB_MODELS_TOKEN", raising=False)

    from src.llm_client import complete

    with pytest.raises(RuntimeError, match="GITHUB_MODELS_TOKEN"):
        complete("ping")

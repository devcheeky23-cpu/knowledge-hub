import os

from openai import OpenAI

PROVIDERS = {
    "github_models": {
        "base_url": "https://models.github.ai/inference",
        "default_model": "openai/gpt-4o-mini",
        "token_env": "GITHUB_MODELS_TOKEN",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-8b-instant",
        "token_env": "GROQ_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-1.5-flash",
        "token_env": "GEMINI_API_KEY",
    },
}


def complete(prompt: str) -> str:
    provider = PROVIDERS[os.environ.get("LLM_PROVIDER", "github_models")]
    token = os.environ.get(provider["token_env"])
    if not token:
        raise RuntimeError(f"{provider['token_env']} is not set")
    model = os.environ.get("LLM_MODEL", provider["default_model"])

    client = OpenAI(base_url=provider["base_url"], api_key=token)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

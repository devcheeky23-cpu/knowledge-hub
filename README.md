---
title: Project Knowledge Hub
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# Project Knowledge Hub

RAG-based Q&A over project documentation. Answers are grounded in uploaded
documents and always carry a citation; when the documents don't contain an
answer, the system abstains rather than guessing.

## Status

Full RAG app deployed on Hugging Face Spaces: a chat page (`app.py`) that answers
questions grounded in ingested documents with citations (and abstains or reports
conflicts when appropriate), plus a document management page
(`pages/Manage_Documents.py`) for uploading, listing, deleting, and re-ingesting
documents. Markdown, plain-text, and PDF documents are supported. A pre-built
Chroma index (`seed_index/`, built from `seed_docs/`) is committed so the app is
queryable immediately after a cold start, with no manual re-ingest.

### Rebuilding the seed index

```bash
python scripts/build_seed_index.py
```

## Configuration

The LLM is reached via the GitHub Models OpenAI-compatible endpoint. The token
is read from the `GITHUB_MODELS_TOKEN` environment variable only — never
committed.

- **Local:** put `GITHUB_MODELS_TOKEN=...` in a `.env` file (gitignored).
- **HF Spaces:** set `GITHUB_MODELS_TOKEN` as a Space Secret.

### Switching provider / model

The LLM client (`src/llm_client.py`) is provider-agnostic — swap provider or
model via environment variables, no code changes:

- `LLM_PROVIDER` — `github_models` (default), `groq`, or `gemini`.
- `LLM_MODEL` — override the provider's default model (e.g. `openai/gpt-4o` for
  the demo).

Each provider reads its own token env var: `GITHUB_MODELS_TOKEN`, `GROQ_API_KEY`,
or `GEMINI_API_KEY`.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

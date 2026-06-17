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

Deployment pipeline smoke test (#2). The current `app.py` is a minimal app that
validates the full infra path: GitHub → Actions → Hugging Face Spaces →
Secrets → GitHub Models.

## Configuration

The LLM is reached via the GitHub Models OpenAI-compatible endpoint. The token
is read from the `GITHUB_MODELS_TOKEN` environment variable only — never
committed.

- **Local:** put `GITHUB_MODELS_TOKEN=...` in a `.env` file (gitignored).
- **HF Spaces:** set `GITHUB_MODELS_TOKEN` as a Space Secret.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

"""Minimal Streamlit smoke test for the deployment pipeline (#2).

Validates the full infra path: GitHub repo → Actions → HF Space → Secrets →
GitHub Models. Sends one test prompt and shows the response.

PAT is read from the GITHUB_MODELS_TOKEN environment variable only.
Locally: put it in a .env (gitignored). On HF Spaces: set it as a Space Secret.
"""
import os

import streamlit as st
from openai import OpenAI

ENDPOINT = "https://models.github.ai/inference"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def get_client():
    token = os.environ.get("GITHUB_MODELS_TOKEN")
    if not token:
        return None
    return OpenAI(base_url=ENDPOINT, api_key=token)


st.title("Deployment smoke test")
st.caption("Validates GitHub Models connectivity via the deployment pipeline.")

client = get_client()
if client is None:
    st.error("GITHUB_MODELS_TOKEN is not set. Add it as a Space Secret (or .env locally).")
    st.stop()

prompt = st.text_input("Test prompt", value="Reply with the single word: pong")

if st.button("Send"):
    with st.spinner("Calling GitHub Models..."):
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
    st.success("Response received")
    st.write(response.choices[0].message.content)

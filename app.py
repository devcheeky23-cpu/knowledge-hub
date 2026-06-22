"""Knowledge Hub — chat page (#8).

The user asks a question; the answer engine retrieves grounded chunks and
returns an Answer. Answers render with expandable citations. Three modes are
handled: found, abstain, conflict.
"""
import streamlit as st

from src import answer_engine


@st.cache_resource
def _bootstrap():
    """Seed the system from the committed seed corpus once on cold start, so the
    app is queryable immediately with no manual re-ingest."""
    from src import document_manager

    return document_manager.bootstrap()


@st.cache_resource
def _embedder():
    """Load the embedding model once per session, not per query."""
    from src.ingestion import _get_embedder

    return _get_embedder()


def _render_answer(answer, msg_idx):
    if answer.mode == "abstain":
        st.warning("Information not found in the documents.")
        return

    if answer.mode == "conflict":
        st.markdown("⚠️ The documents contain conflicting information:")

    st.markdown(answer.answer_text)

    for cite_idx, citation in enumerate(answer.citations):
        section = citation.section_heading or "(no section)"
        with st.expander(f"📄 {citation.source_file} — {section}"):
            st.markdown(citation.chunk_text)
            if st.toggle("📖 View full document", key=f"fulldoc_{msg_idx}_{cite_idx}"):
                from src import document_manager

                st.markdown(document_manager.get_document_text(citation.source_file))


st.title("📚 Knowledge Hub")
st.caption("Ask a question about your project documents.")

_bootstrap()
_embedder()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            _render_answer(message["answer"], msg_idx)

question = st.chat_input("Ask a question")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    answer = answer_engine.answer(question)
    st.session_state.messages.append({"role": "assistant", "answer": answer})
    with st.chat_message("assistant"):
        _render_answer(answer, len(st.session_state.messages) - 1)

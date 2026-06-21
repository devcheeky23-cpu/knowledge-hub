"""Knowledge Hub — Document Manager page (#9).

Upload Documents (MD / TXT / PDF), see what is currently ingested, delete a
Document (chunks + source file), or trigger a full Re-ingest after a cold start.
"""
import streamlit as st

from src import document_manager

st.title("📁 Document Manager")
st.caption("Upload, list, delete, and re-ingest project documents.")

uploaded = st.file_uploader("Upload a document", type=["md", "txt", "pdf"])
if uploaded is not None and uploaded.file_id != st.session_state.get("_last_upload"):
    st.session_state["_last_upload"] = uploaded.file_id
    try:
        count = document_manager.save_and_ingest(uploaded.name, uploaded.getvalue())
        st.success(f"Ingested **{uploaded.name}** — {count} chunks.")
    except Exception as exc:
        st.error(f"Failed to ingest {uploaded.name}: {exc}")

st.subheader("Documents")
documents = document_manager.list_documents()
if not documents:
    st.info("No documents yet — upload one above.")
for name in documents:
    label_col, delete_col = st.columns([5, 1])
    label_col.markdown(name)
    if delete_col.button("Delete", key=f"delete_{name}"):
        document_manager.delete_document(name)
        st.rerun()

st.divider()
if st.button("🔄 Re-ingest all documents", key="reingest"):
    try:
        total = document_manager.reingest()
        st.success(f"Re-ingested {len(documents)} documents — {total} chunks.")
    except Exception as exc:
        st.error(f"Re-ingest failed: {exc}")

import json
from dataclasses import dataclass

from src.llm_client import complete

TOP_K = 5


@dataclass
class Citation:
    source_file: str
    section_heading: str
    chunk_text: str


@dataclass
class Answer:
    mode: str
    answer_text: str
    citations: list


def _retrieve(question: str, top_k: int) -> list[dict]:
    from src.ingestion import query

    return query(question, top_k=top_k)


def _build_prompt(question: str, chunks: list[dict]) -> str:
    numbered = "\n\n".join(
        f"[{i}] (source: {c['source_file']}, section: {c['section_heading'] or '(none)'})\n{c['text']}"
        for i, c in enumerate(chunks, start=1)
    )
    return (
        "You answer questions using ONLY the numbered document chunks below. "
        "Do not use any outside or general knowledge.\n"
        "If the chunks do not contain enough information to answer, you must abstain.\n\n"
        f"Chunks:\n{numbered}\n\n"
        f"Question: {question}\n\n"
        "Respond with a single JSON object and nothing else:\n"
        '{"mode": "found" | "abstain", "answer_text": "...", "used_chunks": [chunk numbers you used]}\n'
        '- "found": answer from the chunks; list every chunk number you used in "used_chunks".\n'
        '- "abstain": the chunks lack the answer; set "used_chunks" to [] and say the '
        "information is not in the documents."
    )


def answer(question: str) -> Answer:
    chunks = _retrieve(question, TOP_K)
    raw = complete(_build_prompt(question, chunks))
    data = json.loads(raw)

    citations = [
        Citation(
            source_file=chunks[i - 1]["source_file"],
            section_heading=chunks[i - 1]["section_heading"],
            chunk_text=chunks[i - 1]["text"],
        )
        for i in data.get("used_chunks", [])
    ]
    return Answer(mode=data["mode"], answer_text=data["answer_text"], citations=citations)

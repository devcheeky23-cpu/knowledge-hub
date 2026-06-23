"""Golden-set eval runner for #11.

Runs every question in eval/golden_set.json through the Answer Engine against the
seed corpus and writes a results table to eval/results.md.

The eval is ultimately manual: this harness does the *automated* part it can — it
checks the Answer mode and that the expected source(s) appear in the citations —
and leaves a column for the reviewer to confirm answer_text correctness and the
final pass/fail. Mode + citation are necessary but not sufficient for a pass.

Usage (from repo root, with a provider token set, e.g. GITHUB_MODELS_TOKEN):

    python -m eval.run_golden

Provider/model are selected by the same env vars the app uses
(LLM_PROVIDER, LLM_MODEL, and the provider's token var).
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GOLDEN = Path(__file__).resolve().parent / "golden_set.json"
RESULTS = Path(__file__).resolve().parent / "results.md"


def _ensure_index():
    """Seed the vector store from seed_docs/ if it is empty (cold start)."""
    from src import document_manager
    from src.ingestion import _get_collection

    if _get_collection().count() == 0:
        document_manager.bootstrap()


def _citation_ok(category, expected_sources, citations):
    cited = {c.source_file for c in citations}
    if category == "out_of_scope":
        return len(cited) == 0
    if category == "conflict":
        # both conflicting sources should be cited
        return all(s in cited for s in expected_sources)
    # answerable: at least one of the acceptable sources is cited
    return any(s in cited for s in expected_sources)


def _md_escape(text):
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main():
    spec = json.loads(GOLDEN.read_text())
    questions = spec["questions"]
    threshold = spec.get("pass_threshold", 0.75)

    _ensure_index()
    from src import answer_engine

    rows = []
    auto_pass = 0
    for q in questions:
        try:
            ans = answer_engine.answer(q["question"])
            mode = ans.mode
            answer_text = ans.answer_text
            sources = sorted({c.source_file for c in ans.citations})
            mode_match = mode == q["expected_mode"]
            cite_ok = _citation_ok(q["category"], q["expected_sources"], ans.citations)
            error = ""
        except Exception as exc:  # noqa: BLE001 - record any failure as a fail
            mode = answer_text = "—"
            sources = []
            mode_match = cite_ok = False
            error = f"ERROR: {exc}"

        auto = mode_match and cite_ok
        auto_pass += int(auto)
        rows.append(
            {
                "id": q["id"],
                "category": q["category"],
                "question": q["question"],
                "expected_mode": q["expected_mode"],
                "expected_answer": q["expected_answer"],
                "system_mode": mode,
                "system_answer": error or answer_text,
                "system_sources": ", ".join(sources) or "—",
                "mode_match": mode_match,
                "cite_ok": cite_ok,
                "auto": auto,
            }
        )

    rate = auto_pass / len(questions) if questions else 0.0

    provider = os.environ.get("LLM_PROVIDER", "github_models")
    model = os.environ.get("LLM_MODEL", "(provider default)")

    lines = [
        "# Golden-set eval results (#11)",
        "",
        f"- Provider: `{provider}` · Model: `{model}`",
        f"- Questions: {len(questions)}",
        f"- Automated pass (mode + citation): **{auto_pass}/{len(questions)} = {rate:.0%}** "
        f"(threshold {threshold:.0%})",
        "",
        "> Automated pass checks Answer **mode** and that the expected **source(s)** are "
        "cited. It does NOT judge answer wording — review `system answer` against "
        "`expected answer` and set the final **Pass?** column by hand.",
        "",
        "| id | cat | question | expected mode | system mode | mode✓ | cite✓ | system answer | sources | Pass? |",
        "|----|-----|----------|---------------|-------------|-------|-------|---------------|---------|-------|",
    ]
    for r in rows:
        lines.append(
            "| {id} | {cat} | {q} | {em} | {sm} | {mm} | {co} | {sa} | {src} | {p} |".format(
                id=r["id"],
                cat=r["category"][:4],
                q=_md_escape(r["question"]),
                em=r["expected_mode"],
                sm=r["system_mode"],
                mm="✅" if r["mode_match"] else "❌",
                co="✅" if r["cite_ok"] else "❌",
                sa=_md_escape(r["system_answer"])[:200],
                src=_md_escape(r["system_sources"]),
                p="✅" if r["auto"] else "⬜",
            )
        )
    lines.append("")
    RESULTS.write_text("\n".join(lines))

    print(f"Wrote {RESULTS}")
    print(f"Automated pass: {auto_pass}/{len(questions)} = {rate:.0%} (threshold {threshold:.0%})")
    if rate < threshold:
        print("Below threshold — review failures and iterate on prompt/chunking per #11.")


if __name__ == "__main__":
    main()

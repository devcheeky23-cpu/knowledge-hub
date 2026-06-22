# ADR-0001: Issue Execution Order

**Status:** Accepted

## Context

The Knowledge Hub has 10 open issues with dependency relationships that are not obvious from issue numbers alone. Without a recorded order, each new session (or new machine) must re-derive the sequence from issue bodies — risking a different conclusion each time.

## Decision

Execute issues in this order, driven by the dependency graph and critical path:

| Order | Issue | Blocked by |
|-------|-------|------------|
| 1 | #2 deploy smoke test | nothing |
| 2 | #3 LLM client | #2 (PAT secret must exist in deployment env) |
| 3 | #6 answer engine: found + abstain | #3 |
| 4 | #8 Streamlit chat UI | #6 |
| 5 | #7 answer engine: conflict mode | #6 |
| 6 | #9 Streamlit doc management UI | #4 (done) |
| 7 | #5 PDF support | #4 (done) |
| 8 | #12 store original source files | #4 (done) |
| 9 | #10 full deploy + pre-built index | #8, #9 |
| 10 | #11 golden question set eval | #10 |

Critical path: **#2 → #3 → #6 → #8 → #10 → #11**

Issues #5, #9, #12 are unblocked but not on the critical path — interleave when convenient.

## Why this order is not obvious from issue numbers

- #3 is blocked by #2 (soft block: PAT secret needed for real LLM calls, not just local tests)
- #7 (conflict mode) ranks after #8 (chat UI) because the UI already has slots for conflict rendering — both can land in the same sprint
- #5, #9, #12 are unblocked early but deprioritised because they don't gate anything on the critical path

## Status of each issue (update as work progresses)

- #2 ✅ Done — infra validated, HF Space live
- #3 ✅ Done — provider-agnostic LLM client
- #4 ✅ Done — ingestion pipeline (MD + TXT)
- #6 ✅ Done — answer engine: found + abstain
- #7 ✅ Done — answer engine: conflict mode
- #8 ✅ Done — Streamlit chat UI
- #9 ✅ Done — Streamlit doc management UI
- #5 ✅ Done — PDF support (PyMuPDF)
- #12 ✅ Done — full-document citation view
- #10 ✅ Done — full deploy + seed corpus (store built on cold start from seed_docs/)
- #11: open — golden question set eval (blocked until #10 deployment is verified live)

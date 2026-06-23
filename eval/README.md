# Golden-set evaluation (#11)

Manual evaluation of the deployed Knowledge Hub against a fixed set of golden
questions. Target: **≥70–80% pass rate** across the set.

## Files

- `golden_set.json` — 18 English questions in three categories, each with an
  expected answer, expected Answer mode, and expected citation source(s):
  - **answerable** (11) — must return `found` with a citation to the correct source.
  - **out_of_scope** (4) — must `abstain` with no citations and no invented content.
  - **conflict** (3) — must return `conflict` and report both refund policies
    (2022 = 14 days vs 2024 = 30 days) without choosing a side.
- `golden_set_th.json` — the same 18 questions asked **in Thai** (same ids,
  expected modes, and expected citation sources). The corpus is English;
  retrieval is cross-lingual via the multilingual-e5 embedder, so a Thai question
  retrieves the English chunks and the system answers in Thai grounded in them.
- `run_golden.py` — runs a set through the Answer Engine and writes a results
  table. Pass a golden-set path to pick the set (default = English).
- `results.md` / `results_th.md` — generated results tables (the documented
  evidence for #11).

## How to evaluate

A pass requires the **right mode**, the **right citation**, *and* an answer whose
content matches the expected answer. The harness auto-checks mode + citation; you
confirm the wording and set the final `Pass?` column.

### Option A — run the harness (recommended, reuses the real Answer Engine)

From the repo root, with a provider token set (same env vars as the app):

```bash
export GITHUB_MODELS_TOKEN=...                     # or GROQ_API_KEY / GEMINI_API_KEY
python -m eval.run_golden                          # English set -> eval/results.md
python -m eval.run_golden eval/golden_set_th.json  # Thai set    -> eval/results_th.md
```

Then open `results.md`, compare each `system answer` to its `expected answer`,
and set `Pass?` (✅/❌). Compute the final pass rate from that column.

### Option B — manual against the live HF Space

Open the deployed Space chat page, ask each question in `golden_set.json`,
and record the system answer, mode, and citation in `results.md` (copy the table
header from a harness run or write it by hand), then mark pass/fail.

## If below threshold

Per #11, iterate on prompt tuning — chunk size / overlap (`src/ingestion.py`),
`TOP_K` and the answer-contract prompt (`src/answer_engine.py`) — and re-run
until the pass rate reaches the target.

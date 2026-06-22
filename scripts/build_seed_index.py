"""Build the committed pre-built Chroma index from seed_docs/ (#10).

Generates `seed_index/`, which is committed to the repo and copied into place on
a cold start by `ingestion.bootstrap_index()` (HF Spaces disk is ephemeral). The
app is then queryable immediately with no manual re-ingest. Re-run this whenever
the seed documents change.

    python scripts/build_seed_index.py
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SEED_DOCS = ROOT / "seed_docs"
SEED_INDEX = ROOT / "seed_index"


def main() -> None:
    # build straight into the committed index location
    os.environ["CHROMA_DB_PATH"] = str(SEED_INDEX)
    if SEED_INDEX.exists():
        shutil.rmtree(SEED_INDEX)

    from src import ingestion

    docs = sorted(p for p in SEED_DOCS.iterdir() if p.is_file())
    total = 0
    for path in docs:
        n = ingestion.ingest(str(path))
        print(f"  {path.name}: {n} chunks")
        total += n

    print(f"\nBuilt {SEED_INDEX.relative_to(ROOT)} — {total} chunks from {len(docs)} documents")


if __name__ == "__main__":
    main()

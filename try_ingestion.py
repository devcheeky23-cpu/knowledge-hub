"""Manual smoke test for the ingestion pipeline (#4).

Ingests the sample fixtures, then runs a few queries and prints the
retrieved chunks. This is NOT a unit test — it's a hands-on demo to see
retrieval working with the real embedding model.

Run:  python try_ingestion.py
"""
import os
import tempfile

# Use a throwaway DB so we don't pollute anything
os.environ["CHROMA_DB_PATH"] = tempfile.mkdtemp(prefix="try_chroma_")

from src.ingestion import ingest, query

FIXTURES = "tests/fixtures"

print("=" * 60)
print("INGESTING")
print("=" * 60)
for fname in ["sample.md", "sample.txt"]:
    n = ingest(os.path.join(FIXTURES, fname))
    print(f"  {fname}: {n} chunks stored")

print()
print("=" * 60)
print("QUERYING")
print("=" * 60)

questions = [
    "how do I cancel an order",
    "what does the product API return",
    "ยกเลิกออเดอร์ได้ภายในกี่ชั่วโมง",   # Thai question vs English docs
]

for q in questions:
    print(f"\nQ: {q}")
    results = query(q, top_k=2)
    for i, r in enumerate(results, 1):
        text = r["text"].replace("\n", " ")
        preview = text[:90] + ("..." if len(text) > 90 else "")
        print(f"  [{i}] {r['source_file']} › {r['section_heading']}")
        print(f"      {preview}")

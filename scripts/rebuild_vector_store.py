"""
rebuild_vector_store.py - Re-create all ChromaDB vectors from the chunks in PostgreSQL.

Run from the project root folder:
    venv\\Scripts\\python.exe scripts\\rebuild_vector_store.py           (rebuild everything)
    venv\\Scripts\\python.exe scripts\\rebuild_vector_store.py --check   (only compare counts)

When to use it:
- the data/vector_store folder was deleted or damaged
- the embedding model was changed in .env
- to verify that PostgreSQL and ChromaDB are in sync (--check)
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import func, select  # noqa: E402

import models  # noqa: E402,F401
from database import SessionLocal  # noqa: E402
from models import Document, DocumentChunk  # noqa: E402
from rag.vector_store import get_vector_store  # noqa: E402
from services.document_service import index_document_vectors  # noqa: E402


def check(db, store):
    """Compare chunk counts in PostgreSQL with vector counts in ChromaDB, per document."""
    docs = db.scalars(select(Document).order_by(Document.id)).all()
    problems = 0
    for doc in docs:
        pg = db.scalar(select(func.count()).select_from(DocumentChunk)
                       .where(DocumentChunk.document_id == doc.id))
        expected = pg if doc.processing_status == "processed" else 0
        chroma = store.count_for_document(doc.id)
        if chroma != expected:
            problems += 1
            print(f"  MISMATCH #{doc.id} {doc.doc_code}: PostgreSQL {expected} chunks, ChromaDB {chroma} vectors")
    total_pg = db.scalar(select(func.count()).select_from(DocumentChunk).join(Document)
                         .where(Document.processing_status == "processed"))
    print(f"PostgreSQL chunks (processed docs): {total_pg} | ChromaDB vectors: {store.count()}")
    print("In sync." if problems == 0 and total_pg == store.count() else "NOT in sync - run without --check.")
    return problems == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="only compare counts, change nothing")
    args = parser.parse_args()

    store = get_vector_store()
    with SessionLocal() as db:
        if args.check:
            sys.exit(0 if check(db, store) else 1)

        started = time.perf_counter()
        store.reset()
        docs = db.scalars(select(Document).where(Document.processing_status == "processed")
                          .order_by(Document.id)).all()
        total = 0
        for doc in docs:
            n = index_document_vectors(db, doc, store)
            total += n
            print(f"  {doc.doc_code or doc.id:<8} {doc.access_level.name:<9} {n:>3} vectors")
        print(f"\nRebuilt {total} vectors for {len(docs)} documents in {time.perf_counter() - started:.1f}s.")
        check(db, store)


if __name__ == "__main__":
    main()

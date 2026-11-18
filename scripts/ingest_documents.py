"""
ingest_documents.py - Load the TechNova knowledge base into NovaMind.

Run from the project root folder:
    venv\\Scripts\\python.exe scripts\\ingest_documents.py              (add new documents)
    venv\\Scripts\\python.exe scripts\\ingest_documents.py --reprocess  (re-chunk existing ones)

Reads data/knowledge_base/index.csv. For every row it uses the department and
access level from the index (chosen by the "admin"), and runs the same pipeline as
an upload: validate -> fingerprint -> store -> extract -> clean -> chunk -> save.
Duplicates are skipped, so the script is safe to run many times.
"""

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

import models  # noqa: E402,F401
from config import Config  # noqa: E402
from database import SessionLocal  # noqa: E402
from models import Document, User  # noqa: E402
from services.document_service import (  # noqa: E402
    DocumentRejected, file_sha256, ingest_file, process_document,
)

KB_DIR = ROOT / "data" / "knowledge_base"


def main():
    parser = argparse.ArgumentParser(description="Ingest the sample knowledge base.")
    parser.add_argument("--reprocess", action="store_true",
                        help="re-extract and re-chunk documents that already exist")
    args = parser.parse_args()

    rows = list(csv.DictReader(open(KB_DIR / "index.csv", encoding="utf-8")))
    print(f"Chunk size {Config.CHUNK_SIZE}, overlap {Config.CHUNK_OVERLAP}. {len(rows)} documents in index.\n")

    added = skipped = failed = reprocessed = 0
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == "admin@technova.test"))

        for row in rows:
            path = KB_DIR / row["relative_path"]
            existing = db.scalar(select(Document).where(Document.file_hash == file_sha256(path)))

            if existing:
                if args.reprocess:
                    process_document(db, existing)
                    reprocessed += 1
                    print(f"  reprocessed {row['doc_code']:<8} {existing.processing_status:<10} "
                          f"{existing.chunk_count:>3} chunks")
                else:
                    skipped += 1
                    print(f"  skipped     {row['doc_code']:<8} (already ingested as #{existing.id})")
                continue

            try:
                doc = ingest_file(
                    db, path,
                    original_filename=row["filename"],
                    department=row["department"],
                    access_level=row["access_level"],
                    uploaded_by=admin.id if admin else None,
                    title=row["title"],
                    doc_code=row["doc_code"],
                    version=row["version"],
                    document_type=row["document_type"],
                    doc_created_date=row["created_date"],
                )
            except DocumentRejected as error:
                failed += 1
                print(f"  REJECTED    {row['doc_code']:<8} {error}")
                continue

            if doc.processing_status == "processed":
                added += 1
                print(f"  added       {row['doc_code']:<8} {doc.access_level.name:<9} "
                      f"{doc.chunk_count:>3} chunks  {row['filename']}")
            else:
                failed += 1
                print(f"  FAILED      {row['doc_code']:<8} see document_processing_logs")

    print(f"\nAdded {added}, skipped {skipped}, reprocessed {reprocessed}, failed/rejected {failed}.")


if __name__ == "__main__":
    main()

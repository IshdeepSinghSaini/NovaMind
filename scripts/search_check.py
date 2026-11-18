"""
search_check.py - Try a semantic search from the terminal (a preview before the real
retrieval service in Phase 8).

Run from the project root folder:
    venv\\Scripts\\python.exe scripts\\search_check.py "how do I get money back for a trip?"
    venv\\Scripts\\python.exe scripts\\search_check.py "salary for senior engineer" --role Employee
    venv\\Scripts\\python.exe scripts\\search_check.py "salary for senior engineer" --role HR

--role decides which access levels may be searched, using the same RBAC rules as the app.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

import models  # noqa: E402,F401
from database import SessionLocal  # noqa: E402
from models import Role  # noqa: E402
from rag.vector_store import get_vector_store  # noqa: E402
from services.embedding_service import embed_query  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--role", default="Admin", choices=["Admin", "Employee", "HR", "Finance", "IT"])
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    with SessionLocal() as db:
        role = db.scalar(select(Role).where(Role.name == args.role))
        allowed = sorted(level.name for level in role.access_levels)

    print(f"Question : {args.question}")
    print(f"Role     : {args.role} -> may search {', '.join(allowed)}\n")

    hits = get_vector_store().query(embed_query(args.question), allowed, top_k=args.top)
    for rank, hit in enumerate(hits, start=1):
        m = hit["metadata"]
        where = f"page {m['page_number']}" if "page_number" in m else m.get("section_reference", "")
        print(f"{rank}. score {hit['score']:.3f} | {m['document_title']} ({m.get('doc_code', '')}, "
              f"{m['access_level']}) | {where}")
        print("   " + hit["content"][:160].replace("\n", " ") + ("..." if len(hit["content"]) > 160 else ""))


if __name__ == "__main__":
    main()

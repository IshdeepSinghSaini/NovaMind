"""
test_embeddings.py - Tests for the embedding model, ChromaDB vector store, permission
filtering inside the vector search, and PostgreSQL <-> ChromaDB consistency.
All tests use a temporary ChromaDB (see conftest.py); the real one is never touched.
"""

import csv
import math
from pathlib import Path

import pytest
from sqlalchemy import select

from config import Config
from models import DocumentChunk
from services.chunking_service import chunk_document, embedding_text
from services.document_processor import extract_document
from services.document_service import index_document_vectors, ingest_file, process_document
from services.embedding_service import (
    count_tokens, embed_query, embed_texts, embedding_dimension, max_tokens,
)

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "knowledge_base"
INDEX = list(csv.DictReader(open(KB / "index.csv", encoding="utf-8")))


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))  # vectors are normalised


# ------------------------------------------------------------- the model --

def test_model_gives_384_numbers_of_length_one():
    assert embedding_dimension() == 384
    vec = embed_query("How many leaves do I get?")
    assert len(vec) == 384
    assert math.isclose(math.sqrt(sum(v * v for v in vec)), 1.0, rel_tol=1e-4)


def test_similar_meaning_scores_higher_than_different_meaning():
    q = embed_query("How do I get my money back for a business trip?")
    travel, password = embed_texts([
        "Employees can claim reimbursement for business travel expenses such as flights and hotels.",
        "To reset your password, go to the identity portal and click Forgot password.",
    ])
    assert cosine(q, travel) > cosine(q, password) + 0.2


def test_no_knowledge_base_chunk_is_cut_off_by_the_model():
    """Every chunk + its label must fit in the model's token limit (otherwise text is lost)."""
    limit = max_tokens()
    longest = 0
    for row in INDEX:
        doc = extract_document(KB / row["relative_path"], row["file_format"])
        for c in chunk_document(doc, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP):
            longest = max(longest, count_tokens(embedding_text(row["title"], c.section_reference, c.content)))
    assert longest <= limit, f"longest chunk has {longest} tokens, model limit is {limit}"


# ---------------------------------------------------------- vector store --

def _item(chunk_id, doc_id, level, text):
    return {
        "chunk_id": chunk_id, "document_id": doc_id, "chunk_index": 0, "access_level": level,
        "department": "HR", "document_title": f"Doc {doc_id}", "doc_code": None,
        "page_number": None, "section_reference": "S", "content": text,
        "embedding": embed_query(text),
    }


@pytest.fixture
def filled_store(_use_temp_vector_store):
    store = _use_temp_vector_store
    store.upsert_chunks([
        _item(1, 10, "Employee", "Employees get 24 days of paid annual leave per year."),
        _item(2, 20, "HR", "Senior Software Engineer salary band is INR 22 to 32 lakh."),
        _item(3, 30, "Public", "TechNova was founded in 2012 in Bengaluru."),
        _item(4, 40, "Finance", "Payments above INR 5 lakh need CFO approval."),
    ])
    return store


def test_search_finds_the_right_chunk(filled_store):
    hits = filled_store.query(embed_query("How much holiday do employees get?"),
                              ["Public", "Employee"], top_k=2)
    assert hits[0]["chunk_id"] == 1
    assert 0 < hits[0]["score"] <= 1


def test_search_never_returns_chunks_outside_allowed_levels(filled_store):
    """Even when the HR chunk is the BEST match, an Employee search must not return it."""
    q = embed_query("What is the salary band for a senior software engineer?")
    employee_hits = filled_store.query(q, ["Public", "Employee"], top_k=10)
    assert {h["metadata"]["access_level"] for h in employee_hits} <= {"Public", "Employee"}
    assert 2 not in [h["chunk_id"] for h in employee_hits]

    hr_hits = filled_store.query(q, ["Public", "Employee", "HR"], top_k=10)
    assert hr_hits[0]["chunk_id"] == 2


def test_single_allowed_level_works(filled_store):
    hits = filled_store.query(embed_query("approval"), ["Finance"], top_k=10)
    assert [h["chunk_id"] for h in hits] == [4]


def test_no_permissions_means_no_results(filled_store):
    assert filled_store.query(embed_query("leave"), [], top_k=5) == []
    assert filled_store.query(embed_query("leave"), None, top_k=5) == []


def test_upsert_twice_does_not_duplicate(filled_store):
    before = filled_store.count()
    filled_store.upsert_chunks([_item(1, 10, "Employee", "Employees get 24 days of paid annual leave per year.")])
    assert filled_store.count() == before


def test_delete_document_removes_only_its_vectors(filled_store):
    filled_store.delete_document(20)
    assert filled_store.count_for_document(20) == 0
    assert filled_store.count() == 3


def test_changing_access_level_changes_who_can_find_it(filled_store):
    q = embed_query("salary band senior engineer")
    assert 2 not in [h["chunk_id"] for h in filled_store.query(q, ["Employee"], 10)]
    assert filled_store.update_document_metadata(20, access_level="Employee") == 1
    assert 2 in [h["chunk_id"] for h in filled_store.query(q, ["Employee"], 10)]


# ------------------------------------------------- pipeline and syncing --

def kb_path(code):
    row = next(r for r in INDEX if r["doc_code"] == code)
    return KB / row["relative_path"], row


def ingest(db, code, tmp_path, access_level=None):
    path, row = kb_path(code)
    return ingest_file(db, path, original_filename=path.name, department=row["department"],
                       access_level=access_level or row["access_level"], upload_dir=tmp_path)


def test_ingest_writes_one_vector_per_chunk(db_session, tmp_path, _use_temp_vector_store):
    doc = ingest(db_session, "HR-002", tmp_path)
    assert doc.processing_status == "processed"
    assert _use_temp_vector_store.count_for_document(doc.id) == doc.chunk_count > 0

    # vector IDs match PostgreSQL chunk IDs
    chunk_ids = set(db_session.scalars(select(DocumentChunk.id).where(DocumentChunk.document_id == doc.id)))
    stored = _use_temp_vector_store.collection.get(where={"document_id": doc.id}, include=["metadatas"])
    assert {m["chunk_id"] for m in stored["metadatas"]} == chunk_ids
    assert all(m["access_level"] == "Employee" for m in stored["metadatas"])


def test_reprocess_keeps_vectors_in_sync(db_session, tmp_path, _use_temp_vector_store):
    doc = ingest(db_session, "HR-003", tmp_path)
    process_document(db_session, doc, upload_dir=tmp_path)
    assert _use_temp_vector_store.count_for_document(doc.id) == doc.chunk_count
    assert _use_temp_vector_store.count() == doc.chunk_count  # old vectors are gone


def test_failed_reprocess_removes_vectors(db_session, tmp_path, _use_temp_vector_store):
    doc = ingest(db_session, "IT-003", tmp_path)
    (tmp_path / doc.stored_filename).unlink()
    process_document(db_session, doc, upload_dir=tmp_path)
    assert doc.processing_status == "failed"
    assert _use_temp_vector_store.count_for_document(doc.id) == 0


def test_vector_store_error_rolls_back_postgres(db_session, tmp_path, _use_temp_vector_store, monkeypatch):
    def broken(*_a, **_k):
        raise RuntimeError("ChromaDB is down")

    monkeypatch.setattr(_use_temp_vector_store, "upsert_chunks", broken)
    doc = ingest(db_session, "IT-006", tmp_path)
    assert doc.processing_status == "failed"
    remaining = db_session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)).all()
    assert remaining == []  # no chunks without vectors


def test_restricted_document_is_found_only_by_allowed_roles(db_session, tmp_path, _use_temp_vector_store):
    ingest(db_session, "HR-007", tmp_path)  # salary bands, HR only
    ingest(db_session, "HR-002", tmp_path)  # leave policy, Employee
    q = embed_query("What is the salary range for a senior software engineer?")

    employee = _use_temp_vector_store.query(q, ["Public", "Employee"], top_k=10)
    assert employee and all("22,00,000" not in h["content"] for h in employee)

    hr = _use_temp_vector_store.query(q, ["Public", "Employee", "HR"], top_k=3)
    assert any("22,00,000" in h["content"] for h in hr)


def test_index_document_vectors_rebuilds_from_postgres(db_session, tmp_path, _use_temp_vector_store):
    doc = ingest(db_session, "FIN-004", tmp_path)
    _use_temp_vector_store.delete_document(doc.id)
    assert index_document_vectors(db_session, doc, _use_temp_vector_store) == doc.chunk_count
    assert _use_temp_vector_store.count_for_document(doc.id) == doc.chunk_count

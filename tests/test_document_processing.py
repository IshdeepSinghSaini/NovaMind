"""
test_document_processing.py - Tests for file validation, text extraction, cleaning,
chunking and saving documents to the database.
"""

import csv
import shutil
from pathlib import Path

import pytest
from sqlalchemy import select

from config import Config
from models import Document, DocumentChunk, DocumentProcessingLog
from services.chunking_service import Chunk, chunk_document, embedding_text, split_sentences
from services.document_processor import (
    Block, ExtractedDocument, ExtractionError, Section, clean_text, extract_document,
)
from services.document_service import DocumentRejected, ingest_file, process_document
from utils.file_validation import FileValidationError, validate_file

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "knowledge_base"
TEST_FILES = ROOT / "data" / "test_files"
INDEX = list(csv.DictReader(open(KB / "index.csv", encoding="utf-8")))
MAX = Config.MAX_UPLOAD_BYTES


def kb_path(code):
    row = next(r for r in INDEX if r["doc_code"] == code)
    return KB / row["relative_path"], row


# ------------------------------------------------------------ validation --

@pytest.mark.parametrize("name", [
    "HR/HR-002_Annual_Leave_Policy.pdf",
    "HR/HR-003_Work_From_Home_Policy.docx",
    "IT/IT-003_Password_Reset_Guide.txt",
])
def test_real_files_pass_validation(name):
    path = KB / name
    assert validate_file(path, path.name, MAX) == path.suffix.lstrip(".")


@pytest.mark.parametrize("name, expected_message", [
    ("unsupported_format.csv", "Unsupported file type"),
    ("empty_document.txt", "empty"),
    ("fake_document.pdf", "not a real PDF"),
    ("script_pretending.docx", "not a real Word"),
])
def test_bad_files_are_rejected(name, expected_message):
    path = TEST_FILES / name
    with pytest.raises(FileValidationError, match=expected_message):
        validate_file(path, path.name, MAX)


def test_too_large_file_is_rejected():
    path = KB / "HR" / "HR-002_Annual_Leave_Policy.pdf"
    with pytest.raises(FileValidationError, match="too large"):
        validate_file(path, path.name, max_bytes=100)


def test_binary_file_named_txt_is_rejected(tmp_path):
    fake = tmp_path / "program.txt"
    fake.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00")  # start of a Windows .exe
    with pytest.raises(FileValidationError, match="binary"):
        validate_file(fake, fake.name, MAX)


# ------------------------------------------------------------ extraction --

@pytest.mark.parametrize("code", ["HR-002", "HR-003", "IT-003"])  # pdf, docx, txt
def test_extraction_reads_title_metadata_and_sections(code):
    path, row = kb_path(code)
    doc = extract_document(path, row["file_format"])
    assert doc.title == row["title"]
    assert doc.metadata["doc_code"] == code
    assert doc.metadata["access_level"] == row["access_level"]
    assert doc.metadata["version"] == row["version"]
    assert len(doc.sections) >= 4
    assert all(s.heading for s in doc.sections)


def test_pdf_keeps_page_numbers():
    path, _ = kb_path("HR-002")
    doc = extract_document(path, "pdf")
    pages = {b.page for s in doc.sections for b in s.blocks}
    assert doc.page_count == 2
    assert pages == {1, 2}


def test_pdf_bullets_are_detected():
    path, _ = kb_path("HR-002")
    doc = extract_document(path, "pdf")
    bullets = [b for s in doc.sections for b in s.blocks if b.kind == "bullet"]
    assert len(bullets) >= 5
    assert not any(b.text.startswith("•") for b in bullets)


def test_whitespace_only_file_has_no_text():
    with pytest.raises(ExtractionError, match="No readable text"):
        extract_document(TEST_FILES / "whitespace_only.txt", "txt")


def test_clean_text_normalises_characters():
    assert clean_text("  It’s a “test” – ok\u0007  ") == "It's a \"test\" - ok"


# -------------------------------------------------------------- chunking --

def test_sentence_split_keeps_abbreviations():
    text = "TechNova Solutions Pvt. Ltd. is in Bengaluru. It has 4 offices! Is it big? Yes."
    assert split_sentences(text) == [
        "TechNova Solutions Pvt. Ltd. is in Bengaluru.", "It has 4 offices!", "Is it big?", "Yes.",
    ]


def _long_doc(sentences=30):
    text = " ".join(f"Sentence number {i} explains rule {i} of the long policy section." for i in range(sentences))
    return ExtractedDocument("txt", "Long Doc", {}, [Section("1. Long Section", [Block("paragraph", text, 3)])])


def test_long_section_is_split_with_overlap():
    chunks = chunk_document(_long_doc(), chunk_size=300, chunk_overlap=80)
    assert len(chunks) > 3
    for prev, nxt in zip(chunks, chunks[1:]):
        last_sentence = split_sentences(prev.content)[-1]
        assert nxt.content.startswith(last_sentence)  # the overlap
    assert all(c.char_count <= 300 for c in chunks)
    assert all(c.page_number == 3 and c.section_reference == "1. Long Section" for c in chunks)


def test_no_overlap_when_overlap_is_zero():
    chunks = chunk_document(_long_doc(), chunk_size=300, chunk_overlap=0)
    joined = " ".join(c.content for c in chunks)
    assert joined.count("Sentence number 5 ") == 1


def test_very_long_sentence_is_cut_between_words():
    sentence = "word " * 400
    doc = ExtractedDocument("txt", "T", {}, [Section("S", [Block("paragraph", sentence.strip(), None)])])
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 5
    assert all(c.char_count <= 200 for c in chunks)
    assert all(not c.content.startswith("ord") for c in chunks)  # never cut inside a word


def test_sections_are_never_mixed():
    doc = ExtractedDocument("txt", "T", {}, [
        Section("A", [Block("paragraph", "Alpha text.", None)]),
        Section("B", [Block("paragraph", "Beta text.", None)]),
    ])
    chunks = chunk_document(doc, 800, 150)
    assert [(c.section_reference, c.content) for c in chunks] == [("A", "Alpha text."), ("B", "Beta text.")]


def test_invalid_chunk_settings_are_refused():
    with pytest.raises(ValueError):
        chunk_document(_long_doc(), chunk_size=50, chunk_overlap=0)
    with pytest.raises(ValueError):
        chunk_document(_long_doc(), chunk_size=300, chunk_overlap=200)


def test_embedding_text_adds_title_and_section_label():
    assert embedding_text("Leave Policy", "5. Sick Leave", "Ten days.") == "Leave Policy > 5. Sick Leave\nTen days."
    assert embedding_text(None, None, "Ten days.") == "Ten days."


@pytest.mark.parametrize("row", INDEX, ids=[r["doc_code"] for r in INDEX])
def test_every_knowledge_base_document_chunks_cleanly(row):
    doc = extract_document(KB / row["relative_path"], row["file_format"])
    chunks = chunk_document(doc, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
    assert chunks, "no chunks"
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    for c in chunks:
        assert isinstance(c, Chunk)
        assert 0 < c.char_count <= Config.CHUNK_SIZE
        assert c.section_reference
        assert "Document ID:" not in c.content           # metadata header removed
        assert "Access Level:" not in c.content
        assert "Synthetic document created" not in c.content  # boilerplate removed
        assert "Page " not in c.content[:6]               # no page footers
        if row["file_format"] == "pdf":
            assert c.page_number in (1, 2)
        else:
            assert c.page_number is None


# --------------------------------------------------------- saving to DB --

def ingest(db, path, tmp_path, **kw):
    kw.setdefault("department", "HR")
    kw.setdefault("access_level", "Employee")
    return ingest_file(db, path, original_filename=kw.pop("original_filename", Path(path).name),
                       upload_dir=tmp_path, **kw)


def test_ingest_saves_document_and_chunks(db_session, tmp_path):
    path, _ = kb_path("HR-002")
    doc = ingest(db_session, path, tmp_path)

    assert doc.processing_status == "processed"
    assert doc.title == "Annual Leave Policy"      # read from the document
    assert doc.doc_code == "HR-002" or doc.doc_code is None  # None if the real DB already has HR-002
    assert doc.version == "2.1"
    assert str(doc.doc_created_date) == "2025-03-01"

    chunks = db_session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
                                .order_by(DocumentChunk.chunk_index)).all()
    assert len(chunks) == doc.chunk_count > 0
    assert any("24 days of paid annual leave" in c.content for c in chunks)
    assert {c.page_number for c in chunks} == {1, 2}

    log = db_session.scalar(select(DocumentProcessingLog).where(DocumentProcessingLog.document_id == doc.id))
    assert log.status == "processed" and log.processing_time_ms is not None


def test_stored_file_uses_random_safe_name(db_session, tmp_path):
    path, _ = kb_path("IT-003")
    doc = ingest(db_session, path, tmp_path, original_filename="../../etc/evil name.txt")
    assert ".." not in doc.original_filename and "/" not in doc.original_filename
    assert len(doc.stored_filename) == 32 + len(".txt")
    assert (tmp_path / doc.stored_filename).exists()


def test_duplicate_upload_is_rejected_even_with_new_name(db_session, tmp_path):
    path, _ = kb_path("HR-002")
    ingest(db_session, path, tmp_path)
    with pytest.raises(DocumentRejected, match="already uploaded"):
        ingest(db_session, TEST_FILES / "Leave_Policy_COPY.pdf", tmp_path)


def test_invalid_file_is_rejected_before_saving(db_session, tmp_path):
    before = db_session.query(Document).count()
    with pytest.raises(DocumentRejected, match="not a real PDF"):
        ingest(db_session, TEST_FILES / "fake_document.pdf", tmp_path)
    assert db_session.query(Document).count() == before
    assert not list(tmp_path.iterdir())  # nothing was stored


def test_unknown_department_is_rejected(db_session, tmp_path):
    path, _ = kb_path("IT-003")
    with pytest.raises(DocumentRejected, match="Unknown department"):
        ingest(db_session, path, tmp_path, department="Marketing")


def test_text_less_file_is_saved_as_failed_with_reason(db_session, tmp_path):
    doc = ingest(db_session, TEST_FILES / "whitespace_only.txt", tmp_path)
    assert doc.processing_status == "failed"
    assert doc.chunk_count == 0
    log = db_session.scalar(select(DocumentProcessingLog).where(DocumentProcessingLog.document_id == doc.id))
    assert log.status == "failed"
    assert "No readable text" in log.error_message


def test_access_level_comes_from_admin_not_from_document_text(db_session, tmp_path):
    # This file says "Access Level: Employee" inside it, but the admin chose HR
    doc = ingest(db_session, TEST_FILES / "TEST-INJ-001_Office_Pantry_Guidelines.txt", tmp_path,
                 department="General", access_level="HR")
    assert doc.processing_status == "processed"
    assert doc.access_level.name == "HR"


def test_reprocess_replaces_chunks_without_duplicates(db_session, tmp_path):
    path, _ = kb_path("HR-003")
    doc = ingest(db_session, path, tmp_path)
    first_count = doc.chunk_count

    process_document(db_session, doc, upload_dir=tmp_path)
    chunks = db_session.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)).all()
    assert doc.processing_status == "processed"
    assert len(chunks) == first_count
    logs = db_session.scalars(select(DocumentProcessingLog).where(DocumentProcessingLog.document_id == doc.id)).all()
    assert len(logs) == 2


def test_missing_stored_file_marks_document_failed(db_session, tmp_path):
    path, _ = kb_path("IT-003")
    doc = ingest(db_session, path, tmp_path)
    (tmp_path / doc.stored_filename).unlink()
    process_document(db_session, doc, upload_dir=tmp_path)
    assert doc.processing_status == "failed"


def test_injection_text_is_stored_as_plain_data(db_session, tmp_path):
    """Prompt injection lines are kept as ordinary text (they are defended against in Phase 9)."""
    doc = ingest(db_session, TEST_FILES / "TEST-INJ-001_Office_Pantry_Guidelines.txt", tmp_path,
                 department="General", access_level="Employee")
    contents = " ".join(c.content for c in doc.chunks)
    assert "Ignore all previous instructions" in contents

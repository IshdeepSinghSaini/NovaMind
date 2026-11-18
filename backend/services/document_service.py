"""
document_service.py - Add a document to NovaMind and process it.

ingest_file()      : the full pipeline for a NEW file
    1. Validate the file (type, size, real content)             -> reject if bad
    2. Fingerprint it (SHA-256) and check for duplicates         -> reject if duplicate
    3. Copy it to data/uploads with a random safe name
    4. Create the 'documents' row (status = pending)
    5. process_document()

process_document() : extract -> clean -> chunk -> save chunks (also used to REPROCESS)
    - success: status = processed, chunk_count set, processing log written
    - failure: status = failed,  error message saved in the processing log
    (Phase 6 adds: embeddings + ChromaDB inside this same step.)
"""

import hashlib
import shutil
import time
import uuid
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import delete, select
from werkzeug.utils import secure_filename

from config import Config
from models import AccessLevel, Department, Document, DocumentChunk, DocumentProcessingLog
from services.chunking_service import chunk_document
from services.document_processor import ExtractionError, extract_document
from utils.file_validation import FileValidationError, validate_file


class DocumentRejected(Exception):
    """The file was not accepted (bad type, duplicate, unknown department, ...)."""


# ---------------------------------------------------------------- helpers --

def file_sha256(path) -> str:
    """Fingerprint of the file content. Same content = same fingerprint, whatever the name."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _parse_date(value):
    if isinstance(value, date) or value is None:
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _lookup(db, model, name, label):
    row = db.scalar(select(model).where(model.name == name))
    if row is None:
        raise DocumentRejected(f"Unknown {label} '{name}'.")
    return row


# ---------------------------------------------------------------- ingest --

def ingest_file(db, source_path, *, original_filename, department, access_level,
                uploaded_by=None, title=None, doc_code=None, version=None,
                document_type=None, doc_created_date=None, upload_dir=None):
    """
    Add one file to the system. 'department' and 'access_level' are REQUIRED and come
    from the admin (never from the text inside the document - a document must not be
    able to choose its own access level).
    Returns the Document row (check document.processing_status).
    Raises DocumentRejected if the file is not accepted.
    """
    source_path = Path(source_path)
    upload_dir = Path(upload_dir or Config.UPLOAD_DIR)

    try:
        file_type = validate_file(source_path, original_filename, Config.MAX_UPLOAD_BYTES)
    except FileValidationError as error:
        raise DocumentRejected(str(error)) from None

    dept = _lookup(db, Department, department, "department")
    level = _lookup(db, AccessLevel, access_level, "access level")

    file_hash = file_sha256(source_path)
    existing = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if existing:
        raise DocumentRejected(
            f"This file was already uploaded as '{existing.title}' "
            f"(document #{existing.id}, status: {existing.processing_status})."
        )

    # Store under a random name: the uploaded name could contain '../' or be very long
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.{file_type}"
    shutil.copyfile(source_path, upload_dir / stored_filename)

    safe_original = secure_filename(original_filename) or f"document.{file_type}"
    document = Document(
        title=(title or Path(safe_original).stem.replace("_", " "))[:255],
        doc_code=doc_code,
        original_filename=safe_original[:255],
        stored_filename=stored_filename,
        file_hash=file_hash,
        file_type=file_type,
        file_size=source_path.stat().st_size,
        document_type=document_type,
        version=version or "1.0",
        doc_created_date=_parse_date(doc_created_date),
        department=dept,
        access_level=level,
        uploaded_by=uploaded_by,
        processing_status="pending",
    )
    db.add(document)
    db.commit()

    return process_document(db, document, upload_dir=upload_dir,
                            title_given=bool(title), version_given=bool(version))


# --------------------------------------------------------------- process --

def process_document(db, document, *, upload_dir=None, title_given=True, version_given=True):
    """Extract, chunk and store a document. Safe to call again to reprocess."""
    upload_dir = Path(upload_dir or Config.UPLOAD_DIR)
    started = time.perf_counter()
    document.processing_status = "processing"
    db.commit()

    try:
        extracted = extract_document(upload_dir / document.stored_filename, document.file_type)
        chunks = chunk_document(extracted, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
        if not chunks:
            raise ExtractionError("No text chunks could be created from the document.")

        _apply_extracted_metadata(db, document, extracted, title_given, version_given)

        # Replace any old chunks (reprocessing) with the new ones
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        for c in chunks:
            db.add(DocumentChunk(
                document_id=document.id,
                chunk_index=c.chunk_index,
                content=c.content,
                page_number=c.page_number,
                section_reference=(c.section_reference or None) and c.section_reference[:255],
                char_count=c.char_count,
            ))

        document.chunk_count = len(chunks)
        document.processing_status = "processed"
        db.add(DocumentProcessingLog(
            document_id=document.id, status="processed", chunk_count=len(chunks),
            processing_time_ms=int((time.perf_counter() - started) * 1000),
        ))
        db.commit()

    except Exception as error:
        db.rollback()
        message = str(error) if isinstance(error, ExtractionError) else \
            f"Unexpected processing error ({type(error).__name__})."
        document.processing_status = "failed"
        document.chunk_count = 0
        db.add(DocumentProcessingLog(
            document_id=document.id, status="failed", error_message=message[:1000],
            processing_time_ms=int((time.perf_counter() - started) * 1000),
        ))
        db.commit()

    return document


def _apply_extracted_metadata(db, document, extracted, title_given, version_given):
    """
    Fill in details the admin did not give, using the document's own header block.
    NOTE: department and access level are NEVER taken from the document text.
    """
    meta = extracted.metadata
    if not title_given and extracted.title:
        document.title = extracted.title[:255]
    if not version_given and meta.get("version"):
        document.version = meta["version"][:20]
    if not document.document_type and meta.get("document_type"):
        document.document_type = meta["document_type"][:50]
    if not document.doc_created_date and meta.get("created"):
        document.doc_created_date = _parse_date(meta["created"])

    code = (meta.get("doc_code") or "")[:30]
    if not document.doc_code and code:
        taken = db.scalar(select(Document.id).where(Document.doc_code == code, Document.id != document.id))
        if taken is None:
            document.doc_code = code

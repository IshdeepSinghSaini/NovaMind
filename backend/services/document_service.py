"""
document_service.py - Add a document to NovaMind and process it.

ingest_file()      : the full pipeline for a NEW file
    1. Validate the file (type, size, real content)             -> reject if bad
    2. Fingerprint it (SHA-256) and check for duplicates         -> reject if duplicate
    3. Copy it to data/uploads with a random safe name
    4. Create the 'documents' row (status = pending)
    5. process_document()

process_document() : extract -> clean -> chunk -> save chunks -> embed -> ChromaDB
                     (also used to REPROCESS)
    - success: status = processed, chunk_count set, processing log written
    - failure: status = failed,  error message saved in the processing log,
               and any vectors of this document are removed from ChromaDB

Keeping PostgreSQL and ChromaDB in sync:
    PostgreSQL and ChromaDB are two separate databases, so one "transaction" cannot
    cover both. The order is: write chunks to PostgreSQL (not committed yet) ->
    write vectors to ChromaDB -> commit PostgreSQL. If anything fails, the PostgreSQL
    changes are rolled back AND this document's vectors are deleted from ChromaDB.
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
from rag.vector_store import get_vector_store
from services.chunking_service import chunk_document, embedding_text
from services.document_processor import ExtractionError, extract_document
from services.embedding_service import embed_texts
from utils.file_validation import FileValidationError, validate_file


class DocumentRejected(Exception):
    """
    The file was not accepted (bad type, duplicate, unknown department, ...).
    'code' tells the API which HTTP status to use:
    invalid (400), unsupported_type (415), too_large (413), duplicate (409).
    """

    def __init__(self, message, code="invalid"):
        super().__init__(message)
        self.code = code


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
        raise DocumentRejected(str(error), code=error.code) from None

    dept = _lookup(db, Department, department, "department")
    level = _lookup(db, AccessLevel, access_level, "access level")

    file_hash = file_sha256(source_path)
    existing = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if existing:
        raise DocumentRejected(
            f"This file was already uploaded as '{existing.title}' "
            f"(document #{existing.id}, status: {existing.processing_status}).",
            code="duplicate",
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
    try:
        db.commit()
    except Exception:
        db.rollback()
        (upload_dir / stored_filename).unlink(missing_ok=True)  # do not leave an orphan file
        raise

    return process_document(db, document, upload_dir=upload_dir,
                            title_given=bool(title), version_given=bool(version))


# --------------------------------------------------------------- process --

def process_document(db, document, *, upload_dir=None, title_given=True, version_given=True,
                     vector_store=None):
    """Extract, chunk, embed and store a document. Safe to call again to reprocess."""
    upload_dir = Path(upload_dir or Config.UPLOAD_DIR)
    store = vector_store or get_vector_store()
    started = time.perf_counter()
    document.processing_status = "processing"
    db.commit()

    try:
        if not (upload_dir / document.stored_filename).is_file():
            raise ExtractionError("The stored file is missing from the server.")
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
        db.flush()  # gives the new chunks their IDs (still not committed)

        index_document_vectors(db, document, store)

        document.chunk_count = len(chunks)
        document.processing_status = "processed"
        db.add(DocumentProcessingLog(
            document_id=document.id, status="processed", chunk_count=len(chunks),
            processing_time_ms=int((time.perf_counter() - started) * 1000),
        ))
        db.commit()

    except Exception as error:
        db.rollback()
        try:
            store.delete_document(document.id)  # never leave stale or half-written vectors
        except Exception:
            pass
        message = str(error) if isinstance(error, ExtractionError) else \
            f"Unexpected processing error ({type(error).__name__})."
        # A failed document must have no chunks (rollback may have restored old ones)
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        document.processing_status = "failed"
        document.chunk_count = 0
        db.add(DocumentProcessingLog(
            document_id=document.id, status="failed", error_message=message[:1000],
            processing_time_ms=int((time.perf_counter() - started) * 1000),
        ))
        db.commit()

    return document


def index_document_vectors(db, document, store=None):
    """
    (Re)create the ChromaDB vectors for all chunks of a document from PostgreSQL.
    Each chunk is embedded together with a small label ("Title > Section") to
    give the model context. Returns the number of vectors written.
    """
    store = store or get_vector_store()
    chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)
                        .order_by(DocumentChunk.chunk_index)).all()
    store.delete_document(document.id)  # remove old vectors first (reprocessing)
    if not chunks:
        return 0

    vectors = embed_texts([embedding_text(document.title, c.section_reference, c.content) for c in chunks])
    store.upsert_chunks([{
        "chunk_id": c.id,
        "embedding": vec,
        "content": c.content,
        "document_id": document.id,
        "chunk_index": c.chunk_index,
        "access_level": document.access_level.name,
        "department": document.department.name,
        "document_title": document.title,
        "doc_code": document.doc_code,
        "page_number": c.page_number,
        "section_reference": c.section_reference,
    } for c, vec in zip(chunks, vectors)])
    return len(chunks)


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


# ----------------------------------------------- manage existing documents --

def latest_processing_error(db, document):
    """The error message of the most recent processing attempt if it failed, else None."""
    log = db.scalar(select(DocumentProcessingLog)
                    .where(DocumentProcessingLog.document_id == document.id)
                    .order_by(DocumentProcessingLog.id.desc()).limit(1))
    return log.error_message if log is not None and log.status == "failed" else None


def update_document(db, document, changes, store=None):
    """
    Change title / version / document type / department / access level.
    'changes' must already be validated (see validate_document_update).
    Returns the list of fields that really changed.

    Vectors in ChromaDB are kept in line:
    - title changed        -> chunks are embedded again (the title is part of the embedded label)
    - department or access level changed -> only the metadata on the vectors is updated
    PostgreSQL is the source of truth: if ChromaDB fails, PostgreSQL is rolled back and the
    vectors are rebuilt from it, so the two never disagree for long.
    """
    store = store or get_vector_store()
    changed = []

    if "department" in changes and document.department.name != changes["department"]:
        document.department = _lookup(db, Department, changes["department"], "department")
        changed.append("department")
    if "access_level" in changes and document.access_level.name != changes["access_level"]:
        document.access_level = _lookup(db, AccessLevel, changes["access_level"], "access level")
        changed.append("access_level")
    for field in ("title", "version", "document_type"):
        if field in changes and getattr(document, field) != changes[field]:
            setattr(document, field, changes[field])
            changed.append(field)

    if not changed:
        return []

    try:
        db.flush()
        if document.processing_status == "processed":
            if "title" in changed:
                index_document_vectors(db, document, store)
            elif "department" in changed or "access_level" in changed:
                store.update_document_metadata(
                    document.id,
                    access_level=document.access_level.name,
                    department=document.department.name,
                )
        db.commit()
    except Exception:
        db.rollback()
        if document.processing_status == "processed":
            try:
                index_document_vectors(db, document, store)  # put ChromaDB back in line
            except Exception:
                pass
        raise
    return changed


def delete_document(db, document, store=None, upload_dir=None):
    """
    Delete a document completely: vectors, database rows (chunks and logs cascade) and file.
    Vectors go FIRST, so the document can never be found by a search again, even if a later
    step fails. Returns a small snapshot for the audit log (the row will be gone).
    """
    store = store or get_vector_store()
    upload_dir = Path(upload_dir or Config.UPLOAD_DIR)
    snapshot = {
        "document_id": document.id,
        "doc_code": document.doc_code,
        "title": document.title,
        "filename": document.original_filename,
        "department": document.department.name,
        "access_level": document.access_level.name,
        "chunks": document.chunk_count,
    }
    stored_filename = document.stored_filename

    store.delete_document(document.id)
    db.delete(document)
    db.commit()

    try:
        (upload_dir / stored_filename).unlink(missing_ok=True)
    except OSError:
        pass  # the database is already clean; a leftover file is harmless
    return snapshot


def replace_document_file(db, document, source_path, *, original_filename, version=None,
                          upload_dir=None, store=None):
    """
    Upload a NEW VERSION of an existing document: validate it, store it, and run the whole
    pipeline again (old chunks and vectors are replaced). Title, department and access level
    stay as the admin set them. Raises DocumentRejected if the file is not acceptable.
    """
    source_path = Path(source_path)
    upload_dir = Path(upload_dir or Config.UPLOAD_DIR)

    try:
        file_type = validate_file(source_path, original_filename, Config.MAX_UPLOAD_BYTES)
    except FileValidationError as error:
        raise DocumentRejected(str(error), code=error.code) from None

    file_hash = file_sha256(source_path)
    other = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if other is not None:
        if other.id == document.id:
            raise DocumentRejected("This file is identical to the current version of the document.",
                                   code="duplicate")
        raise DocumentRejected(
            f"This file was already uploaded as '{other.title}' (document #{other.id}).", code="duplicate"
        )

    upload_dir.mkdir(parents=True, exist_ok=True)
    new_stored = f"{uuid.uuid4().hex}.{file_type}"
    shutil.copyfile(source_path, upload_dir / new_stored)

    old_stored = document.stored_filename
    safe_original = secure_filename(original_filename) or f"document.{file_type}"
    document.stored_filename = new_stored
    document.original_filename = safe_original[:255]
    document.file_hash = file_hash
    document.file_type = file_type
    document.file_size = source_path.stat().st_size
    if version:
        document.version = version
    document.processing_status = "pending"
    try:
        db.commit()
    except Exception:
        db.rollback()
        (upload_dir / new_stored).unlink(missing_ok=True)
        raise

    process_document(db, document, upload_dir=upload_dir, title_given=True, version_given=True,
                     vector_store=store)

    try:
        (upload_dir / old_stored).unlink(missing_ok=True)  # the old version is no longer needed
    except OSError:
        pass
    return document

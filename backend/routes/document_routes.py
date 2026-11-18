"""
document_routes.py - Document management APIs.

    GET    /api/documents/options          departments + access levels (for forms)   any logged-in user
    GET    /api/documents                  list with filters and pages               any user (sees only permitted)
    GET    /api/documents/<id>             details                                   permitted users
    GET    /api/documents/<id>/file        view / download the original file         permitted users
    POST   /api/documents/upload           upload + process a new document           Admin
    PATCH  /api/documents/<id>             change title/version/type/department/level  Admin
    POST   /api/documents/<id>/reprocess   extract + chunk + embed again             Admin
    POST   /api/documents/<id>/replace     upload a new version of the file          Admin
    DELETE /api/documents/<id>             delete document, chunks, vectors, file    Admin
    GET    /api/documents/<id>/chunks      see the chunks of a document              Admin

Security rules used everywhere:
- Admin-only routes use @role_required("Admin") (checked in the backend on every request).
- Normal users only ever see documents allowed by permission_service. A document they may not
  see answers 404 "not found", exactly like a document that does not exist, so nobody can
  even find out which restricted documents exist. Such attempts are written to the audit log.
- The browser never learns the disk filename or the file hash.
"""

import math
import tempfile
from pathlib import Path

from flask import Blueprint, g, jsonify, request, send_from_directory
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from config import Config
from database import get_db
from extensions import limiter
from models import AccessLevel, Department, Document, DocumentChunk, DocumentProcessingLog
from rag.vector_store import get_vector_store
from services import audit_service as audit
from services import document_service as docs
from services.permission_service import can_view_document, is_admin, visible_document_filters
from utils.auth import login_required, role_required
from utils.validators import clean_version, validate_document_update, validate_upload_form

document_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

_REJECTION_STATUS = {"invalid": 400, "unsupported_type": 415, "too_large": 413, "duplicate": 409}
_MIME = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
UPLOAD_LIMIT = "30 per hour"


# ---------------------------------------------------------------- helpers --

def _error(message, status):
    return jsonify({"error": message}), status


def _not_found():
    return _error("Document not found.", 404)


def _load_visible(document_id):
    """The document if the current user may see it, otherwise None (never says why)."""
    db = get_db()
    document = db.get(Document, document_id)
    if document is None:
        return None
    if can_view_document(g.current_user, document):
        return document
    audit.log_action(db, audit.ACCESS_DENIED, user_id=g.current_user.id, resource_type="document",
                     resource_id=document_id, details={"reason": "no_permission"})
    return None


def _int_arg(name, default, minimum, maximum):
    raw = request.args.get(name)
    if raw is None:
        return default, None
    try:
        value = int(raw)
    except ValueError:
        return None, f"'{name}' must be a number."
    if not minimum <= value <= maximum:
        return None, f"'{name}' must be between {minimum} and {maximum}."
    return value, None


def _save_upload_to(folder):
    """Save the uploaded file into a temporary folder. Returns (path, original_name, error_response)."""
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return None, None, _error("Please choose a file to upload.", 400)
    incoming = Path(folder) / "incoming"
    upload.save(incoming)
    return incoming, upload.filename, None


def _admin_document_json(db, document):
    data = document.to_dict(admin=True)
    if document.processing_status == "failed":
        data["error"] = docs.latest_processing_error(db, document)
    return data


# ---------------------------------------------------------------- reading --

@document_bp.get("/options")
@login_required
def options():
    db = get_db()
    return jsonify({
        "departments": [d.name for d in db.scalars(select(Department).order_by(Department.id))],
        "access_levels": [{"name": a.name, "description": a.description}
                          for a in db.scalars(select(AccessLevel).order_by(AccessLevel.id))],
        "allowed_extensions": sorted(Config.ALLOWED_EXTENSIONS),
        "max_upload_mb": Config.MAX_UPLOAD_MB,
    }), 200


@document_bp.get("")
@login_required
def list_documents():
    db, user = get_db(), g.current_user
    page, error = _int_arg("page", 1, 1, 100000)
    if error:
        return _error(error, 400)
    page_size, error = _int_arg("page_size", 25, 1, 100)
    if error:
        return _error(error, 400)

    conditions = visible_document_filters(user)  # permission first, filters after
    department = request.args.get("department", "").strip()
    level = request.args.get("access_level", "").strip()
    status = request.args.get("status", "").strip()
    text = request.args.get("q", "").strip()[:100]

    if department:
        conditions.append(Document.department.has(Department.name == department))
    if level:
        conditions.append(Document.access_level.has(AccessLevel.name == level))
    if status:  # applied on top of the permission rules (normal users only ever see processed)
        conditions.append(Document.processing_status == status)
    if text:
        like = "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        conditions.append(or_(Document.title.ilike(like, escape="\\"),
                              Document.doc_code.ilike(like, escape="\\")))

    count_stmt = select(func.count()).select_from(Document)
    list_stmt = (select(Document)
                 .options(joinedload(Document.department), joinedload(Document.access_level),
                          joinedload(Document.uploader))
                 .order_by(Document.created_at.desc(), Document.id.desc())
                 .offset((page - 1) * page_size).limit(page_size))
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = db.scalar(count_stmt)
    documents = db.scalars(list_stmt).unique().all()
    admin = is_admin(user)
    return jsonify({
        "documents": [d.to_dict(admin=admin) for d in documents],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)),
    }), 200


@document_bp.get("/<int:document_id>")
@login_required
def get_document(document_id):
    document = _load_visible(document_id)
    if document is None:
        return _not_found()

    db = get_db()
    if not is_admin(g.current_user):
        return jsonify({"document": document.to_dict()}), 200

    logs = db.scalars(select(DocumentProcessingLog)
                      .where(DocumentProcessingLog.document_id == document.id)
                      .order_by(DocumentProcessingLog.id.desc()).limit(10)).all()
    data = _admin_document_json(db, document)
    data["vector_count"] = get_vector_store().count_for_document(document.id)
    data["processing_logs"] = [{
        "status": log.status,
        "error_message": log.error_message,
        "chunk_count": log.chunk_count,
        "processing_time_ms": log.processing_time_ms,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    } for log in logs]
    return jsonify({"document": data}), 200


@document_bp.get("/<int:document_id>/file")
@login_required
def document_file(document_id):
    """View or download the original file. PDF and TXT open in the browser; DOCX downloads."""
    document = _load_visible(document_id)
    if document is None:
        return _not_found()

    folder = Path(Config.UPLOAD_DIR)
    if not (folder / document.stored_filename).is_file():
        return _error("The file is no longer available on the server.", 404)

    audit.log_action(get_db(), audit.DOCUMENT_VIEWED, user_id=g.current_user.id,
                     resource_type="document", resource_id=document.id)

    inline = document.file_type in ("pdf", "txt") and request.args.get("download") != "1"
    response = send_from_directory(
        folder, document.stored_filename, mimetype=_MIME[document.file_type],
        as_attachment=not inline, download_name=document.original_filename,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"  # browser must not guess another type
    response.headers["Cache-Control"] = "private, no-store"
    return response


@document_bp.get("/<int:document_id>/chunks")
@role_required("Admin")
def document_chunks(document_id):
    db = get_db()
    document = db.get(Document, document_id)
    if document is None:
        return _not_found()
    chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id)
                        .order_by(DocumentChunk.chunk_index)).all()
    return jsonify({
        "document_id": document_id,
        "title": document.title,
        "chunks": [{
            "id": c.id, "chunk_index": c.chunk_index, "page_number": c.page_number,
            "section_reference": c.section_reference, "char_count": c.char_count, "content": c.content,
        } for c in chunks],
    }), 200


# --------------------------------------------------------------- changing --

@document_bp.post("/upload")
@limiter.limit(UPLOAD_LIMIT)
@role_required("Admin")
def upload_document():
    db, admin = get_db(), g.current_user

    # Cheap checks first, before reading the file
    values, error = validate_upload_form(request.form)
    if error:
        return _error(error, 400)
    if request.files.get("file") is None or not request.files["file"].filename:
        return _error("Please choose a file to upload.", 400)
    code = values.get("doc_code")
    if code and db.scalar(select(Document.id).where(Document.doc_code == code)):
        return _error(f"Document code '{code}' is already used.", 409)

    with tempfile.TemporaryDirectory() as folder:
        path, original_name, problem = _save_upload_to(folder)
        if problem:
            return problem
        try:
            document = docs.ingest_file(
                db, path, original_filename=original_name,
                department=values["department"], access_level=values["access_level"],
                uploaded_by=admin.id, title=values.get("title"), doc_code=code,
                version=values.get("version"), document_type=values.get("document_type"),
            )
        except docs.DocumentRejected as rejected:
            audit.log_action(db, audit.DOCUMENT_UPLOAD_REJECTED, user_id=admin.id, resource_type="document",
                             details={"filename": secure_filename(original_name)[:100],
                                      "reason": str(rejected)[:300]})
            return _error(str(rejected), _REJECTION_STATUS.get(rejected.code, 400))

    audit.log_action(db, audit.DOCUMENT_UPLOADED, user_id=admin.id, resource_type="document",
                     resource_id=document.id,
                     details={"title": document.title, "filename": document.original_filename,
                              "department": document.department.name,
                              "access_level": document.access_level.name,
                              "status": document.processing_status, "chunks": document.chunk_count})
    ok = document.processing_status == "processed"
    return jsonify({
        "message": "Document uploaded and processed." if ok
        else "Document uploaded, but processing failed. See the error below.",
        "document": _admin_document_json(db, document),
    }), 201


@document_bp.patch("/<int:document_id>")
@role_required("Admin")
def update_document(document_id):
    db = get_db()
    document = db.get(Document, document_id)
    if document is None:
        return _not_found()

    changes, error = validate_document_update(request.get_json(silent=True))
    if error:
        return _error(error, 400)

    before = {"title": document.title, "version": document.version,
              "document_type": document.document_type,
              "department": document.department.name, "access_level": document.access_level.name}
    try:
        changed = docs.update_document(db, document, changes)
    except docs.DocumentRejected as rejected:
        return _error(str(rejected), 400)

    if changed:
        after = {"title": document.title, "version": document.version,
                 "document_type": document.document_type,
                 "department": document.department.name, "access_level": document.access_level.name}
        audit.log_action(db, audit.DOCUMENT_UPDATED, user_id=g.current_user.id, resource_type="document",
                         resource_id=document.id,
                         details={"changes": {f: {"from": before[f], "to": after[f]} for f in changed}})
    return jsonify({
        "message": "Document updated." if changed else "No changes were needed.",
        "document": _admin_document_json(db, document),
    }), 200


@document_bp.post("/<int:document_id>/reprocess")
@limiter.limit(UPLOAD_LIMIT)
@role_required("Admin")
def reprocess_document(document_id):
    db = get_db()
    document = db.get(Document, document_id)
    if document is None:
        return _not_found()

    docs.process_document(db, document)
    audit.log_action(db, audit.DOCUMENT_REPROCESSED, user_id=g.current_user.id, resource_type="document",
                     resource_id=document.id,
                     details={"status": document.processing_status, "chunks": document.chunk_count})
    ok = document.processing_status == "processed"
    return jsonify({
        "message": "Document processed again." if ok else "Processing failed. See the error below.",
        "document": _admin_document_json(db, document),
    }), 200


@document_bp.post("/<int:document_id>/replace")
@limiter.limit(UPLOAD_LIMIT)
@role_required("Admin")
def replace_document(document_id):
    db = get_db()
    document = db.get(Document, document_id)
    if document is None:
        return _not_found()

    version, error = clean_version(request.form.get("version"))
    if error:
        return _error(error, 400)
    if request.files.get("file") is None or not request.files["file"].filename:
        return _error("Please choose a file to upload.", 400)

    old_version = document.version
    with tempfile.TemporaryDirectory() as folder:
        path, original_name, problem = _save_upload_to(folder)
        if problem:
            return problem
        try:
            docs.replace_document_file(db, document, path, original_filename=original_name, version=version)
        except docs.DocumentRejected as rejected:
            audit.log_action(db, audit.DOCUMENT_UPLOAD_REJECTED, user_id=g.current_user.id,
                             resource_type="document", resource_id=document_id,
                             details={"filename": secure_filename(original_name)[:100],
                                      "reason": str(rejected)[:300]})
            return _error(str(rejected), _REJECTION_STATUS.get(rejected.code, 400))

    audit.log_action(db, audit.DOCUMENT_REPLACED, user_id=g.current_user.id, resource_type="document",
                     resource_id=document.id,
                     details={"version_from": old_version, "version_to": document.version,
                              "status": document.processing_status, "chunks": document.chunk_count})
    ok = document.processing_status == "processed"
    return jsonify({
        "message": "New version uploaded and processed." if ok
        else "New version uploaded, but processing failed. See the error below.",
        "document": _admin_document_json(db, document),
    }), 200


@document_bp.delete("/<int:document_id>")
@role_required("Admin")
def delete_document(document_id):
    db = get_db()
    document = db.get(Document, document_id)
    if document is None:
        return _not_found()

    snapshot = docs.delete_document(db, document)
    audit.log_action(db, audit.DOCUMENT_DELETED, user_id=g.current_user.id, resource_type="document",
                     resource_id=snapshot["document_id"], details=snapshot)
    return jsonify({"message": "Document deleted.", "deleted": snapshot}), 200

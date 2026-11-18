"""
test_documents_api.py - Tests for the document management APIs
(upload, list, details, file download, update, reprocess, replace, delete).

Uses the 'api' fixture from conftest.py: temporary users, a temporary vector store and a
temporary upload folder. Real data is never touched.
"""

import csv
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from config import Config
from models import (
    AuditLog, Conversation, Document, DocumentChunk, DocumentProcessingLog, Message,
    MessageCitation, User,
)
from rag.vector_store import chunk_vector_id  # noqa: F401  (documents the ID format)
from services.embedding_service import embed_query

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "knowledge_base"
TEST_FILES = ROOT / "data" / "test_files"
INDEX = {r["doc_code"]: r for r in csv.DictReader(open(KB / "index.csv", encoding="utf-8"))}
URL = "/api/documents"


# ---------------------------------------------------------------- helpers --

def as_user(api, who):
    """A test browser that is logged in as this user (client.h = headers with the CSRF token)."""
    client = api.app.test_client()
    r = client.post("/api/auth/login", json={"email": f"{who}@pytest.local", "password": api.password})
    assert r.status_code == 200, r.get_json()
    client.h = {"X-CSRF-TOKEN": client.get_cookie("csrf_access_token").value}
    return client


def kb(code):
    return KB / INDEX[code]["relative_path"]


def upload(client, path, department=None, access_level=None, name=None, **extra):
    code = next((c for c, r in INDEX.items() if KB / r["relative_path"] == Path(path)), None)
    if department is None:   # only fill in a default when nothing was given ("" is a real value)
        department = INDEX[code]["department"] if code else "General"
    if access_level is None:
        access_level = INDEX[code]["access_level"] if code else "Employee"
    with open(path, "rb") as f:
        data = {"file": (f, name or Path(path).name), "department": department,
                "access_level": access_level, **extra}
        return client.post(f"{URL}/upload", data=data, headers=client.h, content_type="multipart/form-data")


def upload_ok(client, path, **kw):
    r = upload(client, path, **kw)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["document"]


def audit(api, action):
    return api.db.scalars(select(AuditLog).where(AuditLog.action == action)).all()


def titles(response):
    return sorted(d["title"] for d in response.get_json()["documents"])


# ------------------------------------------------------- who may do what --

MANAGE = [("post", "/upload"), ("patch", "/{id}"), ("delete", "/{id}"),
          ("post", "/{id}/reprocess"), ("post", "/{id}/replace"), ("get", "/{id}/chunks")]


@pytest.mark.parametrize("method, path", MANAGE)
@pytest.mark.parametrize("who", ["t_employee", "t_hr", "t_finance", "t_it"])
def test_only_admin_can_manage_documents(api, who, method, path):
    doc_id = upload_ok(as_user(api, "t_admin"), kb("IT-003"))["id"]
    user = as_user(api, who)
    r = getattr(user, method)(URL + path.format(id=doc_id), headers=user.h)
    assert r.status_code == 403
    assert api.db.get(Document, doc_id) is not None  # nothing was changed
    assert audit(api, "ACCESS_DENIED")


@pytest.mark.parametrize("method, path", MANAGE + [("get", ""), ("get", "/{id}"), ("get", "/{id}/file"),
                                                   ("get", "/options")])
def test_everything_needs_login(api, method, path):
    doc_id = upload_ok(as_user(api, "t_admin"), kb("IT-003"))["id"]
    r = getattr(api.app.test_client(), method)(URL + path.format(id=doc_id))
    assert r.status_code == 401


def test_upload_without_csrf_header_is_rejected(api):
    admin = as_user(api, "t_admin")
    with open(kb("IT-003"), "rb") as f:
        r = admin.post(f"{URL}/upload", content_type="multipart/form-data",
                       data={"file": (f, "a.txt"), "department": "IT", "access_level": "Employee"})
    assert r.status_code == 401
    assert api.db.query(Document).count() == 0


# ----------------------------------------------------------------- upload --

@pytest.mark.parametrize("code", ["HR-002", "HR-003", "IT-003"])  # pdf, docx, txt
def test_admin_can_upload_each_file_type(api, code):
    document = upload_ok(as_user(api, "t_admin"), kb(code))
    assert document["processing_status"] == "processed"
    assert document["chunk_count"] > 0
    assert document["title"] == INDEX[code]["title"]
    assert document["doc_code"] == code
    assert document["version"] == INDEX[code]["version"]
    assert document["uploaded_by"] == "t_admin"
    assert api.store.count_for_document(document["id"]) == document["chunk_count"]
    assert len(list(api.upload_dir.glob("*.*"))) == 1
    assert audit(api, "DOCUMENT_UPLOADED")


def test_api_never_exposes_disk_filename_or_hash(api):
    admin = as_user(api, "t_admin")
    upload_ok(admin, kb("HR-002"))
    for r in (admin.get(URL), admin.get(f"{URL}/{api.db.query(Document).first().id}")):
        text = r.get_data(as_text=True)
        assert "stored_filename" not in text and "file_hash" not in text
        assert api.db.query(Document).first().stored_filename not in text


def test_admin_values_override_what_the_document_says_about_itself(api):
    # The file says "Access Level: Employee" inside, but the admin chose HR
    document = upload_ok(as_user(api, "t_admin"), kb("HR-002"), access_level="HR",
                         title="My Own Title", version="9.9", document_type="Handbook")
    assert document["access_level"] == "HR"
    assert (document["title"], document["version"], document["document_type"]) == \
        ("My Own Title", "9.9", "Handbook")


@pytest.mark.parametrize("extra, message", [
    ({"department": ""}, "Department is required"),
    ({"access_level": ""}, "Access level is required"),
    ({"department": "Marketing"}, "Unknown department"),
    ({"access_level": "Secret"}, "Unknown access level"),
    ({"version": "x" * 30}, "Version"),
    ({"title": "t" * 300}, "too long"),
    ({"doc_code": "bad code!"}, "Document code"),
])
def test_bad_form_values_are_rejected(api, extra, message):
    r = upload(as_user(api, "t_admin"), kb("IT-003"), **extra)
    assert r.status_code == 400
    assert message in r.get_json()["error"]
    assert api.db.query(Document).count() == 0
    assert not list(api.upload_dir.iterdir())


def test_missing_file_is_rejected(api):
    admin = as_user(api, "t_admin")
    r = admin.post(f"{URL}/upload", data={"department": "IT", "access_level": "Employee"},
                   headers=admin.h, content_type="multipart/form-data")
    assert r.status_code == 400
    assert "choose a file" in r.get_json()["error"]


@pytest.mark.parametrize("name, status, message", [
    ("unsupported_format.csv", 415, "Unsupported file type"),
    ("empty_document.txt", 400, "empty"),
    ("fake_document.pdf", 400, "not a real PDF"),
    ("script_pretending.docx", 400, "not a real Word"),
])
def test_bad_files_are_rejected_with_clear_messages(api, name, status, message):
    admin = as_user(api, "t_admin")
    r = upload(admin, TEST_FILES / name, department="General", access_level="Employee")
    assert r.status_code == status
    assert message in r.get_json()["error"]
    assert api.db.query(Document).count() == 0
    assert not list(api.upload_dir.iterdir())
    assert audit(api, "DOCUMENT_UPLOAD_REJECTED")


def test_file_larger_than_the_limit_is_rejected(api, monkeypatch):
    monkeypatch.setattr(Config, "MAX_UPLOAD_BYTES", 1000)
    r = upload(as_user(api, "t_admin"), kb("HR-002"))
    assert r.status_code == 413 and "too large" in r.get_json()["error"]


def test_request_larger_than_flask_limit_is_cut_off_early(api):
    api.app.config["MAX_CONTENT_LENGTH"] = 1000
    r = upload(as_user(api, "t_admin"), kb("HR-002"))
    assert r.status_code == 413
    assert "too large" in r.get_json()["error"]


def test_duplicate_upload_is_rejected_even_with_another_name(api):
    admin = as_user(api, "t_admin")
    upload_ok(admin, kb("HR-002"))
    r = upload(admin, TEST_FILES / "Leave_Policy_COPY.pdf", department="HR", access_level="Employee")
    assert r.status_code == 409
    assert "already uploaded" in r.get_json()["error"]
    assert api.db.query(Document).count() == 1
    assert len(list(api.upload_dir.iterdir())) == 1


def test_document_code_must_be_unique(api):
    admin = as_user(api, "t_admin")
    upload_ok(admin, kb("HR-002"), doc_code="CUSTOM-1")
    r = upload(admin, kb("HR-003"), doc_code="CUSTOM-1")
    assert r.status_code == 409
    assert api.db.query(Document).count() == 1


def test_file_without_text_is_saved_as_failed_with_the_reason(api):
    r = upload(as_user(api, "t_admin"), TEST_FILES / "whitespace_only.txt",
               department="General", access_level="Employee")
    assert r.status_code == 201
    body = r.get_json()
    assert body["document"]["processing_status"] == "failed"
    assert "No readable text" in body["document"]["error"]
    assert "failed" in body["message"]
    assert api.store.count() == 0


def test_dangerous_file_name_cannot_escape_the_upload_folder(api):
    document = upload_ok(as_user(api, "t_admin"), kb("IT-003"), name="../../evil name.txt")
    assert "/" not in document["filename"] and ".." not in document["filename"]
    assert [p.parent for p in api.upload_dir.glob("*.txt")] == [api.upload_dir]


# ------------------------------------------------------ list and details --

@pytest.fixture
def library(api):
    """Four documents: a restricted HR one, an open HR one, a public one and a failed one."""
    admin = as_user(api, "t_admin")
    ids = {
        "salary": upload_ok(admin, kb("HR-007"))["id"],            # HR only
        "leave": upload_ok(admin, kb("HR-002"))["id"],             # Employee
        "company": upload_ok(admin, kb("GEN-001"))["id"],          # Public
    }
    failed = upload(admin, TEST_FILES / "whitespace_only.txt", department="General", access_level="Public")
    ids["failed"] = failed.get_json()["document"]["id"]
    return ids


def test_each_role_lists_only_what_it_may_see(api, library):
    expect = {
        "t_admin": {"Salary Bands and Compensation Guidelines", "Annual Leave Policy", "Company Overview",
                    "whitespace only"},
        "t_employee": {"Annual Leave Policy", "Company Overview"},
        "t_hr": {"Salary Bands and Compensation Guidelines", "Annual Leave Policy", "Company Overview"},
        "t_finance": {"Annual Leave Policy", "Company Overview"},
        "t_it": {"Annual Leave Policy", "Company Overview"},
    }
    for who, wanted in expect.items():
        r = as_user(api, who).get(URL)
        assert r.status_code == 200
        assert set(titles(r)) == wanted, who


def test_normal_users_cannot_list_failed_documents_with_a_filter(api, library):
    r = as_user(api, "t_employee").get(f"{URL}?status=failed")
    assert r.get_json()["documents"] == []
    r = as_user(api, "t_admin").get(f"{URL}?status=failed")
    assert len(r.get_json()["documents"]) == 1


def test_list_filters_and_paging(api, library):
    admin = as_user(api, "t_admin")
    page1 = admin.get(f"{URL}?page_size=3").get_json()
    assert (page1["total"], page1["total_pages"], len(page1["documents"])) == (4, 2, 3)
    assert len(admin.get(f"{URL}?page_size=3&page=2").get_json()["documents"]) == 1
    assert titles(admin.get(f"{URL}?department=HR")) == ["Annual Leave Policy",
                                                         "Salary Bands and Compensation Guidelines"]
    assert titles(admin.get(f"{URL}?access_level=Public")) == ["Company Overview", "whitespace only"]
    assert titles(admin.get(f"{URL}?q=leave")) == ["Annual Leave Policy"]
    assert titles(admin.get(f"{URL}?q=HR-007")) == ["Salary Bands and Compensation Guidelines"]


def test_search_text_wildcards_do_not_match_everything(api, library):
    admin = as_user(api, "t_admin")
    assert admin.get(f"{URL}?q=%25").get_json()["total"] == 0  # '%'
    assert admin.get(f"{URL}?q=_").get_json()["total"] == 0    # '_'


@pytest.mark.parametrize("query", ["page=abc", "page=0", "page_size=1000", "page_size=0"])
def test_bad_paging_values_are_rejected(api, query):
    assert as_user(api, "t_employee").get(f"{URL}?{query}").status_code == 400


def test_restricted_document_looks_like_it_does_not_exist(api, library):
    employee = as_user(api, "t_employee")
    hidden = employee.get(f"{URL}/{library['salary']}")
    missing = employee.get(f"{URL}/999999999")
    assert hidden.status_code == missing.status_code == 404
    assert hidden.get_json() == missing.get_json()          # same answer: no hint that it exists
    denied = audit(api, "ACCESS_DENIED")
    assert any(a.resource_id == str(library["salary"]) for a in denied)  # but it is logged


def test_failed_document_is_invisible_to_normal_users(api, library):
    assert as_user(api, "t_employee").get(f"{URL}/{library['failed']}").status_code == 404
    assert as_user(api, "t_admin").get(f"{URL}/{library['failed']}").status_code == 200


def test_allowed_role_can_open_restricted_document_details(api, library):
    assert as_user(api, "t_hr").get(f"{URL}/{library['salary']}").status_code == 200
    assert as_user(api, "t_finance").get(f"{URL}/{library['salary']}").status_code == 404


def test_admin_details_include_logs_and_vector_count(api, library):
    data = as_user(api, "t_admin").get(f"{URL}/{library['leave']}").get_json()["document"]
    assert data["vector_count"] == data["chunk_count"] > 0
    assert data["processing_logs"][0]["status"] == "processed"
    assert data["is_active"] is True


def test_normal_user_details_have_no_admin_fields(api, library):
    data = as_user(api, "t_employee").get(f"{URL}/{library['leave']}").get_json()["document"]
    for admin_only in ("processing_logs", "vector_count", "uploaded_by", "is_active"):
        assert admin_only not in data


def test_options_list_departments_and_levels(api):
    data = as_user(api, "t_employee").get(f"{URL}/options").get_json()
    assert data["departments"] == ["HR", "IT", "Finance", "Product", "General"]
    assert [a["name"] for a in data["access_levels"]] == ["Public", "Employee", "HR", "Finance", "IT"]
    assert data["allowed_extensions"] == ["docx", "pdf", "txt"]


def test_admin_can_read_chunks(api, library):
    data = as_user(api, "t_admin").get(f"{URL}/{library['leave']}/chunks").get_json()
    assert len(data["chunks"]) == api.db.get(Document, library["leave"]).chunk_count
    assert any("24 days of paid annual leave" in c["content"] for c in data["chunks"])


# --------------------------------------------------------------- the file --

def test_permitted_user_can_view_the_original_pdf(api, library):
    r = as_user(api, "t_employee").get(f"{URL}/{library['leave']}/file")
    assert r.status_code == 200
    assert r.mimetype == "application/pdf"
    assert r.data.startswith(b"%PDF-")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "inline" in r.headers["Content-Disposition"]
    assert audit(api, "DOCUMENT_VIEWED")


def test_download_option_and_docx_are_attachments(api):
    admin = as_user(api, "t_admin")
    pdf_id = upload_ok(admin, kb("HR-002"))["id"]
    docx_id = upload_ok(admin, kb("HR-003"))["id"]
    assert "attachment" in admin.get(f"{URL}/{pdf_id}/file?download=1").headers["Content-Disposition"]
    assert "attachment" in admin.get(f"{URL}/{docx_id}/file").headers["Content-Disposition"]


def test_restricted_file_is_never_sent_to_unauthorised_users(api, library):
    for who in ("t_employee", "t_finance", "t_it"):
        r = as_user(api, who).get(f"{URL}/{library['salary']}/file")
        assert r.status_code == 404
        assert not r.data.startswith(b"%PDF")
    assert as_user(api, "t_hr").get(f"{URL}/{library['salary']}/file").status_code == 200


def test_missing_file_on_disk_gives_a_clean_error(api, library):
    for p in api.upload_dir.iterdir():
        p.unlink()
    r = as_user(api, "t_employee").get(f"{URL}/{library['leave']}/file")
    assert r.status_code == 404 and "no longer available" in r.get_json()["error"]


# ----------------------------------------------------------------- update --

def patch(client, doc_id, body):
    return client.patch(f"{URL}/{doc_id}", json=body, headers=client.h)


def test_changing_access_level_immediately_changes_who_can_find_it(api):
    admin, employee = as_user(api, "t_admin"), as_user(api, "t_employee")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]                  # Employee level
    question = embed_query("How many paid leaves do I get in a year?")
    employee_levels = ["Public", "Employee"]
    assert any(h["document_id"] == doc_id for h in api.store.query(question, employee_levels, 10))
    assert employee.get(f"{URL}/{doc_id}").status_code == 200

    r = patch(admin, doc_id, {"access_level": "HR"})                # now HR only
    assert r.status_code == 200 and r.get_json()["document"]["access_level"] == "HR"

    assert not any(h["document_id"] == doc_id for h in api.store.query(question, employee_levels, 10))
    assert employee.get(f"{URL}/{doc_id}").status_code == 404
    assert employee.get(f"{URL}/{doc_id}/file").status_code == 404
    assert titles(employee.get(URL)) == []
    stored = api.store.collection.get(where={"document_id": doc_id}, include=["metadatas"])
    assert {m["access_level"] for m in stored["metadatas"]} == {"HR"}
    assert as_user(api, "t_hr").get(f"{URL}/{doc_id}").status_code == 200

    change = audit(api, "DOCUMENT_UPDATED")[0].details["changes"]["access_level"]
    assert change == {"from": "Employee", "to": "HR"}

    patch(admin, doc_id, {"access_level": "Employee"})              # and back again
    assert any(h["document_id"] == doc_id for h in api.store.query(question, employee_levels, 10))


def test_changing_department_updates_vectors(api):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]
    assert patch(admin, doc_id, {"department": "Finance"}).status_code == 200
    stored = api.store.collection.get(where={"document_id": doc_id}, include=["metadatas"])
    assert {m["department"] for m in stored["metadatas"]} == {"Finance"}


def test_changing_title_embeds_the_chunks_again(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-002"))
    r = patch(admin, document["id"], {"title": "  Paid   Time Off  Policy "})
    assert r.get_json()["document"]["title"] == "Paid Time Off Policy"   # spaces tidied
    stored = api.store.collection.get(where={"document_id": document["id"]}, include=["metadatas"])
    assert {m["document_title"] for m in stored["metadatas"]} == {"Paid Time Off Policy"}
    assert len(stored["ids"]) == document["chunk_count"]


def test_changing_version_and_type_does_not_touch_vectors(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-002"))
    r = patch(admin, document["id"], {"version": "3.0", "document_type": ""})
    data = r.get_json()["document"]
    assert (data["version"], data["document_type"]) == ("3.0", None)
    assert api.store.count_for_document(document["id"]) == document["chunk_count"]


def test_update_with_same_values_changes_nothing(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-002"))
    r = patch(admin, document["id"], {"title": document["title"]})
    assert r.status_code == 200 and "No changes" in r.get_json()["message"]
    assert not audit(api, "DOCUMENT_UPDATED")


@pytest.mark.parametrize("body, message", [
    ({"title": ""}, "Title is required"),
    ({"title": 5}, "must be text"),
    ({"department": "Marketing"}, "Unknown department"),
    ({"access_level": "Secret"}, "Unknown access level"),
    ({"version": "x" * 30}, "Version"),
    ({"version": ""}, "Version is required"),
    ({}, "No changes"),
    ({"processing_status": "processed"}, "cannot be changed"),
    ({"file_hash": "abc", "access_level": "HR"}, "cannot be changed"),
    ({"uploaded_by": 1}, "cannot be changed"),
    ({"is_active": False}, "cannot be changed"),
    ({"id": 5}, "cannot be changed"),
])
def test_bad_updates_are_rejected_and_nothing_changes(api, body, message):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-002"))
    r = patch(admin, document["id"], body)
    assert r.status_code == 400 and message in r.get_json()["error"]
    after = api.db.get(Document, document["id"])
    api.db.refresh(after)
    assert (after.title, after.access_level.name, after.processing_status) == \
        (document["title"], "Employee", "processed")


def test_update_body_must_be_json(api):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]
    r = admin.patch(f"{URL}/{doc_id}", data="hello", content_type="text/plain", headers=admin.h)
    assert r.status_code == 400


def test_update_of_unknown_document_is_404(api):
    admin = as_user(api, "t_admin")
    assert patch(admin, 999999, {"title": "x"}).status_code == 404


def test_vector_store_failure_rolls_the_change_back(api, monkeypatch):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]

    def broken(*_a, **_k):
        raise RuntimeError("ChromaDB is down")

    monkeypatch.setattr(api.store, "update_document_metadata", broken)
    admin.application.config["PROPAGATE_EXCEPTIONS"] = False
    r = patch(admin, doc_id, {"access_level": "HR"})
    assert r.status_code == 500
    after = api.db.get(Document, doc_id)
    api.db.refresh(after)
    assert after.access_level.name == "Employee"       # PostgreSQL unchanged
    stored = api.store.collection.get(where={"document_id": doc_id}, include=["metadatas"])
    assert {m["access_level"] for m in stored["metadatas"]} == {"Employee"}  # vectors still match


# ------------------------------------------------------------- reprocess --

def test_reprocess_uses_the_current_chunk_settings(api, monkeypatch):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-002"))
    monkeypatch.setattr(Config, "CHUNK_SIZE", 200)
    monkeypatch.setattr(Config, "CHUNK_OVERLAP", 40)

    r = admin.post(f"{URL}/{document['id']}/reprocess", headers=admin.h)
    assert r.status_code == 200
    new = r.get_json()["document"]
    assert new["processing_status"] == "processed"
    assert new["chunk_count"] > document["chunk_count"]
    assert api.store.count_for_document(document["id"]) == new["chunk_count"]
    assert api.store.count() == new["chunk_count"]                      # no old vectors left
    assert api.db.query(DocumentChunk).filter_by(document_id=document["id"]).count() == new["chunk_count"]
    assert api.db.query(DocumentProcessingLog).filter_by(document_id=document["id"]).count() == 2
    assert audit(api, "DOCUMENT_REPROCESSED")


def test_reprocess_fails_cleanly_when_the_stored_file_is_missing(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("IT-003"))
    for p in api.upload_dir.iterdir():
        p.unlink()
    r = admin.post(f"{URL}/{document['id']}/reprocess", headers=admin.h)
    assert r.status_code == 200
    failed = r.get_json()["document"]
    assert failed["processing_status"] == "failed"
    assert "missing" in failed["error"]
    assert api.store.count_for_document(document["id"]) == 0
    assert api.db.query(DocumentChunk).filter_by(document_id=document["id"]).count() == 0
    # a failed document disappears from normal users' lists
    assert as_user(api, "t_employee").get(f"{URL}/{document['id']}").status_code == 404


def test_reprocess_of_unknown_document_is_404(api):
    admin = as_user(api, "t_admin")
    assert admin.post(f"{URL}/999999/reprocess", headers=admin.h).status_code == 404


# --------------------------------------------------------------- replace --

def replace(client, doc_id, path, name=None, **extra):
    with open(path, "rb") as f:
        return client.post(f"{URL}/{doc_id}/replace", headers=client.h, content_type="multipart/form-data",
                           data={"file": (f, name or Path(path).name), **extra})


def test_replace_with_a_new_version_updates_everything(api, tmp_path_factory):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-006"))                          # attendance policy (txt)
    old_file = api.db.get(Document, document["id"]).stored_filename
    assert any("3 late marks" in c.content for c in api.db.query(DocumentChunk).filter_by(document_id=document["id"]))

    new_text = kb("HR-006").read_text(encoding="utf-8").replace("3 late marks", "4 late marks")
    new_file = tmp_path_factory.mktemp("newversion") / "HR-006_Attendance_Policy_v2.txt"
    new_file.write_text(new_text, encoding="utf-8")

    r = replace(admin, document["id"], new_file, version="2.0")
    assert r.status_code == 200, r.get_json()
    data = r.get_json()["document"]
    assert data["version"] == "2.0" and data["processing_status"] == "processed"
    assert data["title"] == document["title"]                          # admin's title is kept
    assert data["access_level"] == document["access_level"]            # and access level

    api.db.expire_all()
    row = api.db.get(Document, document["id"])
    assert row.stored_filename != old_file
    assert not (api.upload_dir / old_file).exists()                    # old version removed
    assert (api.upload_dir / row.stored_filename).exists()
    contents = " ".join(c.content for c in api.db.query(DocumentChunk).filter_by(document_id=row.id))
    assert "4 late marks" in contents and "3 late marks" not in contents
    assert api.store.count_for_document(row.id) == row.chunk_count
    stored = api.store.collection.get(where={"document_id": row.id}, include=["documents"])
    assert any("4 late marks" in t for t in stored["documents"])
    assert not any("3 late marks" in t for t in stored["documents"])
    assert audit(api, "DOCUMENT_REPLACED")[0].details["version_to"] == "2.0"


def test_replace_with_the_same_file_is_rejected(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-006"))
    r = replace(admin, document["id"], kb("HR-006"))
    assert r.status_code == 409 and "identical" in r.get_json()["error"]


def test_replace_with_a_file_that_belongs_to_another_document_is_rejected(api):
    admin = as_user(api, "t_admin")
    first = upload_ok(admin, kb("HR-006"))
    upload_ok(admin, kb("IT-003"))
    r = replace(admin, first["id"], kb("IT-003"))
    assert r.status_code == 409 and "already uploaded" in r.get_json()["error"]


def test_replace_with_an_invalid_file_keeps_the_old_version(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-006"))
    before = api.db.get(Document, document["id"]).stored_filename
    r = replace(admin, document["id"], TEST_FILES / "fake_document.pdf")
    assert r.status_code == 400
    api.db.expire_all()
    row = api.db.get(Document, document["id"])
    assert row.stored_filename == before and (api.upload_dir / before).exists()
    assert row.processing_status == "processed"
    assert api.store.count_for_document(row.id) == row.chunk_count


def test_replace_needs_a_file_and_a_valid_version(api):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-006"))["id"]
    assert admin.post(f"{URL}/{doc_id}/replace", headers=admin.h, data={},
                      content_type="multipart/form-data").status_code == 400
    assert replace(admin, doc_id, kb("IT-003"), version="no way!!").status_code == 400


# ----------------------------------------------------------------- delete --

def test_delete_removes_everything(api):
    admin = as_user(api, "t_admin")
    document = upload_ok(admin, kb("HR-002"))
    doc_id = document["id"]
    stored = api.db.get(Document, doc_id).stored_filename
    assert (api.upload_dir / stored).exists()

    r = admin.delete(f"{URL}/{doc_id}", headers=admin.h)
    assert r.status_code == 200
    api.db.expire_all()
    assert api.db.get(Document, doc_id) is None
    assert api.db.query(DocumentChunk).filter_by(document_id=doc_id).count() == 0
    assert api.db.query(DocumentProcessingLog).filter_by(document_id=doc_id).count() == 0
    assert api.store.count_for_document(doc_id) == 0
    assert not (api.upload_dir / stored).exists()
    assert admin.get(f"{URL}/{doc_id}").status_code == 404

    entry = audit(api, "DOCUMENT_DELETED")[0]
    assert entry.details["title"] == "Annual Leave Policy" and entry.resource_id == str(doc_id)
    assert admin.delete(f"{URL}/{doc_id}", headers=admin.h).status_code == 404


def test_delete_only_removes_that_document(api):
    admin = as_user(api, "t_admin")
    keep = upload_ok(admin, kb("HR-003"))
    gone = upload_ok(admin, kb("HR-002"))
    admin.delete(f"{URL}/{gone['id']}", headers=admin.h)
    assert api.store.count() == keep["chunk_count"]
    assert api.store.count_for_document(keep["id"]) == keep["chunk_count"]
    assert admin.get(f"{URL}/{keep['id']}").status_code == 200


def test_deleted_document_can_no_longer_be_found_by_search(api):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]
    question = embed_query("How many paid leaves do I get in a year?")
    assert any(h["document_id"] == doc_id for h in api.store.query(question, ["Employee"], 10))
    admin.delete(f"{URL}/{doc_id}", headers=admin.h)
    assert api.store.query(question, ["Employee"], 10) == []


def test_old_chat_citations_survive_deleting_the_document(api):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]
    chunk = api.db.query(DocumentChunk).filter_by(document_id=doc_id).first()
    user = api.db.scalar(select(User).where(User.username == "t_employee"))

    conversation = Conversation(user_id=user.id, title="Leave question")
    api.db.add(conversation)
    api.db.flush()
    message = Message(conversation_id=conversation.id, sender="assistant", content="You get 24 days.")
    api.db.add(message)
    api.db.flush()
    citation = MessageCitation(message_id=message.id, document_id=doc_id, chunk_id=chunk.id, rank=1,
                               document_title="Annual Leave Policy", excerpt="24 days of paid annual leave")
    api.db.add(citation)
    api.db.commit()

    assert admin.delete(f"{URL}/{doc_id}", headers=admin.h).status_code == 200
    api.db.expire_all()
    kept = api.db.get(MessageCitation, citation.id)
    assert kept is not None
    assert kept.document_id is None and kept.chunk_id is None           # link removed
    assert kept.document_title == "Annual Leave Policy"                 # text snapshot kept


def test_audit_details_never_contain_secrets(api):
    admin = as_user(api, "t_admin")
    doc_id = upload_ok(admin, kb("HR-002"))["id"]
    patch(admin, doc_id, {"access_level": "HR"})
    admin.delete(f"{URL}/{doc_id}", headers=admin.h)
    text = json.dumps([a.details for a in api.db.scalars(select(AuditLog)) if a.details])
    assert api.password not in text and "scrypt" not in text and "stored_filename" not in text

"""
test_database.py - Checks the real PostgreSQL tables, RBAC rules, and test users.
Run scripts/initialize_database.py and scripts/create_sample_users.py first.
"""

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from database import engine
from models import Document, Role, User

EXPECTED_TABLES = {
    "roles", "access_levels", "role_access_levels", "users",
    "departments", "documents", "document_chunks", "document_processing_logs",
    "conversations", "messages", "message_citations",
    "query_logs", "audit_logs",
}

EXPECTED_RBAC = {
    "Admin": {"Public", "Employee", "HR", "Finance", "IT"},
    "Employee": {"Public", "Employee"},
    "HR": {"Public", "Employee", "HR"},
    "Finance": {"Public", "Employee", "Finance"},
    "IT": {"Public", "Employee", "IT"},
}


def test_all_tables_exist():
    assert EXPECTED_TABLES <= set(inspect(engine).get_table_names())


def test_rbac_rules_are_correct(db_session):
    for role_name, expected_levels in EXPECTED_RBAC.items():
        role = db_session.scalar(select(Role).where(Role.name == role_name))
        assert role is not None, f"Role {role_name} missing"
        assert {level.name for level in role.access_levels} == expected_levels


def test_employee_cannot_see_restricted_levels(db_session):
    role = db_session.scalar(select(Role).where(Role.name == "Employee"))
    levels = {level.name for level in role.access_levels}
    assert "HR" not in levels
    assert "Finance" not in levels
    assert "IT" not in levels


def test_five_sample_users_with_correct_roles(db_session):
    expected = {
        "admin@technova.test": "Admin",
        "employee@technova.test": "Employee",
        "hr@technova.test": "HR",
        "finance@technova.test": "Finance",
        "it@technova.test": "IT",
    }
    for email, role_name in expected.items():
        user = db_session.scalar(select(User).where(User.email == email))
        assert user is not None, f"{email} missing"
        assert user.role.name == role_name
        assert user.is_active is True


def test_passwords_are_stored_as_hashes(db_session):
    for user in db_session.scalars(select(User)):
        assert user.password_hash.startswith("scrypt:")


def test_to_dict_never_exposes_password_hash(db_session):
    user = db_session.scalar(select(User).where(User.email == "admin@technova.test"))
    data = user.to_dict()
    assert "password_hash" not in data
    assert data["role"] == "Admin"


def test_duplicate_email_is_rejected(db_session):
    role = db_session.scalar(select(Role).where(Role.name == "Employee"))
    db_session.add(User(
        username="someone_else", email="employee@technova.test",
        full_name="Duplicate", password_hash="x", role=role,
    ))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_invalid_processing_status_is_rejected(db_session):
    """The database itself refuses unknown status values (CHECK constraint)."""
    from models import AccessLevel, Department
    doc = Document(
        title="Bad", original_filename="a.txt", stored_filename="x-test.txt",
        file_hash="0" * 64, file_type="txt", file_size=1,
        department=db_session.scalar(select(Department).where(Department.name == "HR")),
        access_level=db_session.scalar(select(AccessLevel).where(AccessLevel.name == "HR")),
        processing_status="banana",
    )
    db_session.add(doc)
    with pytest.raises(IntegrityError):
        db_session.flush()

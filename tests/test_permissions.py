"""
test_permissions.py - The RBAC rules: which role may see which document.

These tests are the safety net for the most important rule of the project:
a user must never see a document they are not allowed to see.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy import select

from models import Role
from services.permission_service import (
    allowed_access_levels, can_view_document, is_admin, visible_document_filters,
)

ROLES = ["Admin", "Employee", "HR", "Finance", "IT"]
LEVELS = ["Public", "Employee", "HR", "Finance", "IT"]

# The table from the project plan: role -> access levels it may read
EXPECTED = {
    "Admin": {"Public", "Employee", "HR", "Finance", "IT"},
    "Employee": {"Public", "Employee"},
    "HR": {"Public", "Employee", "HR"},
    "Finance": {"Public", "Employee", "Finance"},
    "IT": {"Public", "Employee", "IT"},
}


def user_with_role(db, role_name, active=True):
    return SimpleNamespace(role=db.scalar(select(Role).where(Role.name == role_name)), is_active=active)


def document(level, status="processed", active=True):
    return SimpleNamespace(is_active=active, processing_status=status, access_level=SimpleNamespace(name=level))


@pytest.mark.parametrize("role", ROLES)
def test_allowed_levels_follow_the_rbac_table(db_session, role):
    assert set(allowed_access_levels(user_with_role(db_session, role))) == EXPECTED[role]


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("role", ROLES)
def test_every_role_and_level_combination(db_session, role, level):
    """25 combinations: can this role view a processed document with this access level?"""
    allowed = can_view_document(user_with_role(db_session, role), document(level))
    assert allowed is (level in EXPECTED[role])


@pytest.mark.parametrize("role", ["Employee", "HR", "Finance", "IT"])
@pytest.mark.parametrize("status", ["pending", "processing", "failed"])
def test_normal_users_never_see_unprocessed_documents(db_session, role, status):
    assert can_view_document(user_with_role(db_session, role), document("Public", status=status)) is False


@pytest.mark.parametrize("role", ["Employee", "HR", "Finance", "IT"])
def test_normal_users_never_see_inactive_documents(db_session, role):
    assert can_view_document(user_with_role(db_session, role), document("Public", active=False)) is False


def test_admin_can_see_everything_to_manage_it(db_session):
    admin = user_with_role(db_session, "Admin")
    assert is_admin(admin)
    assert can_view_document(admin, document("HR", status="failed", active=False)) is True


def test_inactive_user_can_see_nothing(db_session):
    for role in ROLES:
        user = user_with_role(db_session, role, active=False)
        assert allowed_access_levels(user) == []
        assert can_view_document(user, document("Public")) is False
        assert not is_admin(user)


def test_missing_user_or_document_is_denied():
    assert can_view_document(None, document("Public")) is False
    assert allowed_access_levels(None) == []


def test_filters_fail_closed_for_missing_or_inactive_user(db_session):
    assert len(visible_document_filters(None)) == 1
    assert len(visible_document_filters(user_with_role(db_session, "Employee", active=False))) == 1


def test_admin_has_no_extra_filters_but_others_do(db_session):
    assert visible_document_filters(user_with_role(db_session, "Admin")) == []
    assert len(visible_document_filters(user_with_role(db_session, "Employee"))) == 3

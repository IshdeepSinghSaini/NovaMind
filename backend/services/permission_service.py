"""
permission_service.py - The ONE place that decides "who may see which document".

Rules (from the RBAC tables in the database, not hard-coded per role):
- A role can see the access levels linked to it in role_access_levels.
    Employee -> Public, Employee          HR -> Public, Employee, HR      ... and so on
- A normal user can see a document only if ALL of these are true:
    1. the document's access level is one of the user's allowed levels
    2. the document is processed (successfully ready)
    3. the document is active
- Admin can see every document (also failed or inactive ones) to manage them.
- Inactive users can see nothing.

Both the document APIs (Phase 7) and the AI search (Phase 8) use these functions, so
the rules can never drift apart.
"""

from sqlalchemy import false

from models import AccessLevel, Document

ADMIN_ROLE = "Admin"


def is_admin(user) -> bool:
    return user is not None and user.is_active and user.role.name == ADMIN_ROLE


def allowed_access_levels(user):
    """Names of the access levels this user may read, e.g. ['Employee', 'Public']."""
    if user is None or not user.is_active:
        return []
    return sorted(level.name for level in user.role.access_levels)


def can_view_document(user, document) -> bool:
    """Single-document check (used for details and file download)."""
    if user is None or document is None or not user.is_active:
        return False
    if is_admin(user):
        return True
    return (
        bool(document.is_active)
        and document.processing_status == "processed"
        and document.access_level.name in allowed_access_levels(user)
    )


def visible_document_filters(user):
    """
    SQL conditions for list queries: only documents this user may see.
    Returns a list of conditions to add with .where(...). Fails closed: no user or
    no allowed levels -> a condition that matches nothing.
    """
    if user is None or not user.is_active:
        return [false()]
    if is_admin(user):
        return []
    allowed = allowed_access_levels(user)
    if not allowed:
        return [false()]
    return [
        Document.is_active.is_(True),
        Document.processing_status == "processed",
        Document.access_level.has(AccessLevel.name.in_(allowed)),
    ]

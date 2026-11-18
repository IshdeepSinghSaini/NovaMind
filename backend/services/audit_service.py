"""
audit_service.py - Writes important actions into the audit_logs table.

Usage:
    log_action(db, "LOGIN_SUCCESS", user_id=5, resource_type="user", resource_id=5)

Rules:
- Never put passwords, tokens, or API keys in "details".
- If writing the audit log fails, we print a warning but do not crash the request.
"""

from flask import has_request_context, request

from models import AuditLog

# All action names in one place (avoids typos like "LOGIN_SUCESS")
LOGIN_SUCCESS = "LOGIN_SUCCESS"
LOGIN_FAILED = "LOGIN_FAILED"
LOGIN_BLOCKED_INACTIVE = "LOGIN_BLOCKED_INACTIVE"
LOGOUT = "LOGOUT"
ACCESS_DENIED = "ACCESS_DENIED"
RATE_LIMITED = "RATE_LIMITED"
DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
DOCUMENT_UPLOAD_REJECTED = "DOCUMENT_UPLOAD_REJECTED"
DOCUMENT_UPDATED = "DOCUMENT_UPDATED"
DOCUMENT_REPROCESSED = "DOCUMENT_REPROCESSED"
DOCUMENT_REPLACED = "DOCUMENT_REPLACED"
DOCUMENT_DELETED = "DOCUMENT_DELETED"
DOCUMENT_VIEWED = "DOCUMENT_VIEWED"


def _client_ip():
    return request.remote_addr if has_request_context() else None


def log_action(db, action, user_id=None, resource_type=None, resource_id=None, details=None):
    """Save one audit entry and commit it."""
    try:
        db.add(AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
            ip_address=_client_ip(),
        ))
        db.commit()
    except Exception as error:  # logging must never break the main action
        db.rollback()
        print(f"[audit] WARNING: could not write audit log {action}: {type(error).__name__}")

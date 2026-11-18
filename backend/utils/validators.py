"""
validators.py - Check user input before using it.

Never trust what comes from the browser: it can be empty, too long, or the wrong type.
"""

import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_EMAIL_LENGTH = 255
MAX_PASSWORD_LENGTH = 128  # stops someone sending a 10 MB "password" to slow the server


def validate_login_input(data):
    """
    Check the login form data.
    Returns (email, password, None) if OK, or (None, None, "error message") if not.
    """
    if not isinstance(data, dict):
        return None, None, "Request body must be JSON."

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return None, None, "Email and password are required."

    email = email.strip().lower()
    if not email or not password:
        return None, None, "Email and password are required."
    if len(email) > MAX_EMAIL_LENGTH or not EMAIL_PATTERN.match(email):
        return None, None, "Please enter a valid email address."
    if len(password) > MAX_PASSWORD_LENGTH:
        return None, None, "Password is too long."

    return email, password, None


# ------------------------------------------------------------- documents --

VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,19}$")
DOC_CODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,29}$")
EDITABLE_DOCUMENT_FIELDS = {"title", "version", "document_type", "department", "access_level"}


def _text(value, label, max_len, required=False):
    """Clean one text field. Returns (clean_value_or_None, error_or_None)."""
    if value is None:
        return (None, f"{label} is required.") if required else (None, None)
    if not isinstance(value, str):
        return None, f"{label} must be text."
    value = " ".join(value.replace("\x00", "").split())  # no NUL bytes, tidy spaces
    if not value:
        return (None, f"{label} is required.") if required else (None, None)
    if len(value) > max_len:
        return None, f"{label} is too long (maximum {max_len} characters)."
    return value, None


def clean_version(value):
    """Returns (version_or_None, error_or_None). Blank means 'not given'."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, None
    if not isinstance(value, str) or not VERSION_PATTERN.match(value.strip()):
        return None, "Version may use letters, numbers, dots, dashes and underscores (maximum 20 characters)."
    return value.strip(), None


def validate_upload_form(form):
    """
    Check the upload form fields. Returns (values, None) or (None, "error message").
    'values' only contains the fields that were given.
    """
    values = {}
    for field, label, max_len, required in [
        ("department", "Department", 50, True),
        ("access_level", "Access level", 50, True),
        ("title", "Title", 255, False),
        ("document_type", "Document type", 50, False),
    ]:
        value, error = _text(form.get(field), label, max_len, required)
        if error:
            return None, error
        if value is not None:
            values[field] = value

    version, error = clean_version(form.get("version"))
    if error:
        return None, error
    if version:
        values["version"] = version

    code = (form.get("doc_code") or "").strip()
    if code:
        if not DOC_CODE_PATTERN.match(code):
            return None, "Document code may use letters, numbers, dashes and underscores (maximum 30 characters)."
        values["doc_code"] = code
    return values, None


def validate_document_update(data):
    """
    Check a PATCH body. Only a fixed list of fields may be changed (so nobody can set
    processing_status, file_hash, uploaded_by ... through the API).
    Returns (changes, None) or (None, "error message").
    """
    if not isinstance(data, dict):
        return None, "Request body must be JSON."
    unknown = sorted(set(data) - EDITABLE_DOCUMENT_FIELDS)
    if unknown:
        return None, "These fields cannot be changed: " + ", ".join(unknown) + "."
    if not data:
        return None, "No changes were given."

    changes = {}
    for field, label, max_len in [("title", "Title", 255), ("department", "Department", 50),
                                  ("access_level", "Access level", 50)]:
        if field in data:
            value, error = _text(data[field], label, max_len, required=True)
            if error:
                return None, error
            changes[field] = value
    if "version" in data:
        value, error = clean_version(data["version"])
        if error or value is None:
            return None, error or "Version is required."
        changes["version"] = value
    if "document_type" in data:
        value, error = _text(data["document_type"], "Document type", 50, required=False)
        if error:
            return None, error
        changes["document_type"] = value  # None clears it
    return changes, None

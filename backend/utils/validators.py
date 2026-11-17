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

"""
auth.py - "Guards" that protect API routes.

    @login_required              -> must be logged in (valid token cookie) and active
    @role_required("Admin")      -> must be logged in AND have one of these roles

How it works on EVERY protected request:
1. Read the token from the cookie and check its signature + expiry (flask-jwt-extended).
   For POST/PUT/PATCH/DELETE it also checks the CSRF header.
2. Load the user FRESH from the database (we never trust the role written in the token):
   - deleted or deactivated users are blocked immediately, even with an old token
   - role changes take effect immediately
3. Put the user in g.current_user so the route can use it.
"""

from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from database import get_db
from models import User
from services.audit_service import ACCESS_DENIED, log_action


def _load_current_user():
    """Check the token and return the active user, or None."""
    verify_jwt_in_request()  # raises an error (-> 401) if token missing/invalid/expired
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None

    user = get_db().get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = _load_current_user()
        if user is None:
            return jsonify({"error": "Your session is not valid. Please log in again."}), 401
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _load_current_user()
            if user is None:
                return jsonify({"error": "Your session is not valid. Please log in again."}), 401

            if user.role.name not in allowed_roles:
                # Record the attempt: someone tried to use something they are not allowed to
                log_action(
                    get_db(), ACCESS_DENIED, user_id=user.id, resource_type="endpoint",
                    details={"endpoint": view.__name__, "role": user.role.name,
                             "required": list(allowed_roles)},
                )
                return jsonify({"error": "You do not have permission to do this."}), 403

            g.current_user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator

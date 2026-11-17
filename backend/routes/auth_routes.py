"""
auth_routes.py - Login, logout, and "who am I?".

    POST /api/auth/login   {email, password} -> sets the login cookie
    POST /api/auth/logout                     -> removes the login cookie
    GET  /api/auth/me                         -> the logged-in user's details
"""

import secrets
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, set_access_cookies, unset_jwt_cookies,
    verify_jwt_in_request,
)
from sqlalchemy import select

from database import get_db
from extensions import limiter
from models import User
from services import audit_service as audit
from utils.auth import login_required
from utils.security import hash_password, verify_password
from utils.validators import validate_login_input

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# A real scrypt hash of a random value (made once when the app starts). Used when the
# email does not exist, so a wrong email takes the same time as a wrong password
# (attackers can't time the reply to discover which emails are registered).
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
GENERIC_LOGIN_ERROR = "Invalid email or password."


@auth_bp.post("/login")
# Only FAILED attempts count toward the limit (deduct_when). Otherwise many colleagues
# logging in from the same office IP would block each other.
@limiter.limit(
    lambda: current_app.config["LOGIN_RATE_LIMIT"],
    deduct_when=lambda response: response.status_code != 200,
)
def login():
    email, password, error = validate_login_input(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    db = get_db()
    user = db.scalar(select(User).where(User.email == email))

    # 1. Unknown email -> same message and same work as a wrong password
    if user is None:
        verify_password(_DUMMY_HASH, password)
        audit.log_action(db, audit.LOGIN_FAILED, details={"reason": "unknown_email", "email": email})
        return jsonify({"error": GENERIC_LOGIN_ERROR}), 401

    # 2. Wrong password
    if not verify_password(user.password_hash, password):
        audit.log_action(db, audit.LOGIN_FAILED, user_id=user.id, resource_type="user",
                         resource_id=user.id, details={"reason": "wrong_password"})
        return jsonify({"error": GENERIC_LOGIN_ERROR}), 401

    # 3. Correct password but the account is switched off
    if not user.is_active:
        audit.log_action(db, audit.LOGIN_BLOCKED_INACTIVE, user_id=user.id,
                         resource_type="user", resource_id=user.id)
        return jsonify({"error": "This account is deactivated. Please contact the administrator."}), 403

    # 4. Success: create the token (only the user id inside) and put it in a cookie
    user.last_login_at = datetime.now(timezone.utc)
    audit.log_action(db, audit.LOGIN_SUCCESS, user_id=user.id, resource_type="user", resource_id=user.id)

    response = jsonify({"message": "Login successful.", "user": user.to_dict()})
    set_access_cookies(response, create_access_token(identity=str(user.id)))
    return response, 200


@auth_bp.post("/logout")
def logout():
    """Always removes the cookie, even if the token already expired."""
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        user_id = int(identity) if identity else None
    except Exception:
        pass  # expired / broken token: still log the person out

    if user_id is not None:
        audit.log_action(get_db(), audit.LOGOUT, user_id=user_id, resource_type="user", resource_id=user_id)

    response = jsonify({"message": "Logged out."})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.get("/me")
@login_required
def me():
    user = g.current_user
    data = user.to_dict()
    data["access_levels"] = sorted(level.name for level in user.role.access_levels)
    return jsonify({"user": data}), 200

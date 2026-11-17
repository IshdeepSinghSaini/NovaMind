"""
user_routes.py - User management (Admin only).

    GET /api/users -> list all users

More actions (create user, change role, activate/deactivate) come in Phase 13.
"""

from flask import Blueprint, jsonify
from sqlalchemy import select

from database import get_db
from models import User
from utils.auth import role_required

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.get("")
@role_required("Admin")
def list_users():
    users = get_db().scalars(select(User).order_by(User.id)).all()
    return jsonify({"users": [u.to_dict() for u in users], "total": len(users)}), 200

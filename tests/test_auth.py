"""
test_auth.py - Tests for login, logout, "who am I", role protection and rate limiting.

Every test uses its own temporary users inside a database transaction that is
rolled back at the end, so the real data is never changed.
"""

import secrets

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app import create_app
from database import engine
from extensions import limiter
from models import AuditLog, Role, User
from utils.auth import login_required
from utils.security import hash_password

PASSWORD = "Test-" + secrets.token_urlsafe(10)  # random for every test run


# ----------------------------------------------------------------- fixtures --

@pytest.fixture
def ctx():
    """App + test client + DB session, all inside one rolled-back transaction."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint",
                           expire_on_commit=False)

    app = create_app({"TESTING": True, "SESSION_FACTORY": Session})

    # A small extra POST route, only for testing CSRF protection
    @app.post("/api/test/protected-post")
    @login_required
    def protected_post():
        return {"ok": True}

    limiter.reset()
    db = Session()

    roles = {r.name: r for r in db.scalars(select(Role))}
    pw_hash = hash_password(PASSWORD)
    for name, role, active in [
        ("t_admin", "Admin", True),
        ("t_employee", "Employee", True),
        ("t_inactive", "Employee", False),
    ]:
        db.add(User(username=name, email=f"{name}@pytest.local", full_name=name,
                    password_hash=pw_hash, role=roles[role], is_active=active))
    db.commit()

    yield {"app": app, "client": app.test_client(), "db": db}

    db.close()
    transaction.rollback()
    connection.close()


def login(client, who, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": f"{who}@pytest.local", "password": password})


def audit_actions(db, action):
    return db.scalars(select(AuditLog).where(AuditLog.action == action)).all()


# ------------------------------------------------------------------- login --

def test_login_success_sets_secure_cookie(ctx):
    r = login(ctx["client"], "t_admin")
    assert r.status_code == 200
    assert r.get_json()["user"]["role"] == "Admin"

    cookie_header = " ".join(r.headers.getlist("Set-Cookie"))
    assert "access_token_cookie=" in cookie_header
    assert "HttpOnly" in cookie_header          # JavaScript cannot read the token
    assert "csrf_access_token=" in cookie_header

    assert audit_actions(ctx["db"], "LOGIN_SUCCESS")


def test_login_response_never_contains_password_hash(ctx):
    r = login(ctx["client"], "t_admin")
    assert "password_hash" not in r.get_data(as_text=True)
    assert "scrypt" not in r.get_data(as_text=True)


def test_wrong_password_is_rejected_with_generic_message(ctx):
    r = login(ctx["client"], "t_admin", password="Wrong-password-123")
    assert r.status_code == 401
    assert r.get_json()["error"] == "Invalid email or password."
    assert audit_actions(ctx["db"], "LOGIN_FAILED")


def test_unknown_email_gives_same_message_as_wrong_password(ctx):
    r = login(ctx["client"], "nobody")
    assert r.status_code == 401
    assert r.get_json()["error"] == "Invalid email or password."


@pytest.mark.parametrize("body", [
    {},
    {"email": "t_admin@pytest.local"},
    {"email": "not-an-email", "password": "x"},
    {"email": 123, "password": ["x"]},
    {"email": "a@b.co", "password": "x" * 500},
])
def test_invalid_login_input_returns_400(ctx, body):
    r = ctx["client"].post("/api/auth/login", json=body)
    assert r.status_code == 400


def test_non_json_body_returns_400(ctx):
    r = ctx["client"].post("/api/auth/login", data="hello", content_type="text/plain")
    assert r.status_code == 400


def test_inactive_user_cannot_log_in(ctx):
    r = login(ctx["client"], "t_inactive")
    assert r.status_code == 403
    assert audit_actions(ctx["db"], "LOGIN_BLOCKED_INACTIVE")


def test_email_is_case_insensitive(ctx):
    r = ctx["client"].post("/api/auth/login",
                           json={"email": "  T_ADMIN@PYTEST.LOCAL ", "password": PASSWORD})
    assert r.status_code == 200


# ---------------------------------------------------------------------- me --

def test_me_requires_login(ctx):
    assert ctx["client"].get("/api/auth/me").status_code == 401


def test_me_returns_user_and_access_levels(ctx):
    login(ctx["client"], "t_employee")
    r = ctx["client"].get("/api/auth/me")
    assert r.status_code == 200
    user = r.get_json()["user"]
    assert user["role"] == "Employee"
    assert user["access_levels"] == ["Employee", "Public"]


def test_tampered_token_is_rejected(ctx):
    client = ctx["client"]
    client.set_cookie("access_token_cookie", "this.is.fake", domain="localhost")
    assert client.get("/api/auth/me").status_code == 401


# --------------------------------------------------------- role protection --

def test_employee_cannot_list_users(ctx):
    login(ctx["client"], "t_employee")
    r = ctx["client"].get("/api/users")
    assert r.status_code == 403
    assert audit_actions(ctx["db"], "ACCESS_DENIED")


def test_admin_can_list_users(ctx):
    login(ctx["client"], "t_admin")
    r = ctx["client"].get("/api/users")
    assert r.status_code == 200
    assert "password_hash" not in r.get_data(as_text=True)


def test_not_logged_in_cannot_list_users(ctx):
    assert ctx["client"].get("/api/users").status_code == 401


def test_deactivated_user_is_blocked_even_with_old_token(ctx):
    client, db = ctx["client"], ctx["db"]
    login(client, "t_employee")
    assert client.get("/api/auth/me").status_code == 200

    user = db.scalar(select(User).where(User.username == "t_employee"))
    user.is_active = False
    db.commit()

    assert client.get("/api/auth/me").status_code == 401


def test_role_change_takes_effect_immediately(ctx):
    client, db = ctx["client"], ctx["db"]
    login(client, "t_employee")
    assert client.get("/api/users").status_code == 403

    user = db.scalar(select(User).where(User.username == "t_employee"))
    user.role = db.scalar(select(Role).where(Role.name == "Admin"))
    db.commit()

    assert client.get("/api/users").status_code == 200


# ------------------------------------------------------------------- CSRF --

def test_post_without_csrf_header_is_rejected(ctx):
    client = ctx["client"]
    login(client, "t_admin")
    assert client.post("/api/test/protected-post").status_code == 401


def test_post_with_csrf_header_is_allowed(ctx):
    client = ctx["client"]
    login(client, "t_admin")
    csrf = client.get_cookie("csrf_access_token").value
    r = client.post("/api/test/protected-post", headers={"X-CSRF-TOKEN": csrf})
    assert r.status_code == 200


# ----------------------------------------------------------------- logout --

def test_logout_clears_the_session(ctx):
    client = ctx["client"]
    login(client, "t_admin")
    assert client.get("/api/auth/me").status_code == 200

    csrf = client.get_cookie("csrf_access_token").value
    r = client.post("/api/auth/logout", headers={"X-CSRF-TOKEN": csrf})
    assert r.status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert audit_actions(ctx["db"], "LOGOUT")


def test_logout_works_even_when_not_logged_in(ctx):
    assert ctx["client"].post("/api/auth/logout").status_code == 200


# ---------------------------------------------------------- rate limiting --

def test_too_many_login_attempts_are_blocked(ctx):
    client = ctx["client"]
    codes = [login(client, "t_admin", password="Wrong-password-123").status_code for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429
    # Even the CORRECT password is blocked while the limit is active
    assert login(client, "t_admin").status_code == 429
    assert audit_actions(ctx["db"], "RATE_LIMITED")


def test_successful_logins_do_not_use_up_the_limit(ctx):
    """Many people in one office share an IP; correct logins must not block each other."""
    client = ctx["client"]
    for _ in range(8):
        assert login(client, "t_admin").status_code == 200
    # Failed attempts still get their full 5 tries
    assert login(client, "t_admin", password="Wrong-password-123").status_code == 401

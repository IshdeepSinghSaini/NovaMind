"""
conftest.py - Shared setup for all tests (pytest loads this automatically).
"""

import sys
from pathlib import Path

import pytest

# Let tests import code from the "backend" folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import SessionLocal, engine  # noqa: E402


@pytest.fixture(scope="session")
def temp_vector_store(tmp_path_factory):
    """One temporary ChromaDB for the whole test run (the real one is never touched)."""
    from rag.vector_store import VectorStore

    return VectorStore(path=tmp_path_factory.mktemp("chroma"), collection_name="test_chunks")


@pytest.fixture(autouse=True)
def _use_temp_vector_store(temp_vector_store):
    """Every test uses the temporary vector store, starting empty."""
    from rag import vector_store as vs

    previous = vs._default_store
    temp_vector_store.reset()
    vs.set_vector_store(temp_vector_store)
    yield temp_vector_store
    vs.set_vector_store(previous)


@pytest.fixture
def db_session():
    """
    A database session whose changes are ALWAYS undone after the test.
    So tests can add/change rows without messing up the real data.

    Each test also STARTS with no documents (deleted inside the transaction, then
    rolled back at the end). Otherwise the real knowledge base would make uploads
    of the same sample files fail as "duplicates".
    """
    from sqlalchemy import delete

    from models import Document

    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    try:
        session.execute(delete(Document))
        session.flush()
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def api(tmp_path, monkeypatch, _use_temp_vector_store):
    """
    A complete test setup for API tests:
    - the Flask app and a test client
    - a database session whose changes are all undone after the test (and no documents at the start)
    - a temporary vector store and a temporary upload folder (the real ones are never touched)
    - 5 temporary users (t_admin, t_employee, t_hr, t_finance, t_it) with a random password
    """
    import secrets
    from types import SimpleNamespace

    from sqlalchemy import delete, select
    from sqlalchemy.orm import sessionmaker

    from app import create_app
    from config import Config
    from extensions import limiter
    from models import Document, Role, User
    from utils.security import hash_password

    monkeypatch.setattr(Config, "UPLOAD_DIR", tmp_path)

    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint",
                           expire_on_commit=False)
    app = create_app({"TESTING": True, "SESSION_FACTORY": Session})
    limiter.reset()

    db = Session()
    db.execute(delete(Document))
    password = "Test-" + secrets.token_urlsafe(10)
    pw_hash = hash_password(password)
    roles = {r.name: r for r in db.scalars(select(Role))}
    for who, role in [("t_admin", "Admin"), ("t_employee", "Employee"), ("t_hr", "HR"),
                      ("t_finance", "Finance"), ("t_it", "IT")]:
        db.add(User(username=who, email=f"{who}@pytest.local", full_name=who,
                    password_hash=pw_hash, role=roles[role]))
    db.commit()

    yield SimpleNamespace(app=app, db=db, password=password, upload_dir=tmp_path,
                          store=_use_temp_vector_store)

    db.close()
    transaction.rollback()
    connection.close()

"""
conftest.py - Shared setup for all tests (pytest loads this automatically).
"""

import sys
from pathlib import Path

import pytest

# Let tests import code from the "backend" folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import SessionLocal, engine  # noqa: E402


@pytest.fixture
def db_session():
    """
    A database session whose changes are ALWAYS undone after the test.
    So tests can add/change rows without messing up the real data.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

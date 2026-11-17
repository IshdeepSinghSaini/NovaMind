"""
database.py - The connection between Python and PostgreSQL.

- engine        : the "phone line" to the database
- SessionLocal  : opens a short conversation (session) with the database
- Base          : parent class for all our tables (used from Phase 2)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import Config

# pool_pre_ping=True: check the connection is still alive before using it
engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """All database tables (models) will inherit from this class."""
    pass


def get_db():
    """
    Give the current web request its own database session.
    The same session is reused during one request and closed at the end (close_db).
    Tests can swap the session maker via app.config["SESSION_FACTORY"].
    """
    from flask import current_app, g

    if "db" not in g:
        factory = current_app.config.get("SESSION_FACTORY") or SessionLocal
        g.db = factory()
    return g.db


def close_db(_error=None):
    """Called automatically by Flask after every request."""
    from flask import g

    db = g.pop("db", None)
    if db is not None:
        db.close()


def check_connection():
    """
    Try a tiny query on the database.
    Returns (True, version_text) if it works, or (False, error_text) if not.
    """
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
        return True, version
    except Exception as error:
        # Only return the error type + message, never the password
        return False, f"{type(error).__name__}: {str(error).splitlines()[0]}"

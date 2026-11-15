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

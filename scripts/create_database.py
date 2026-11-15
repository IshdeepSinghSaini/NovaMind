"""
create_database.py - Creates the NovaMind database (novamind_db) if it does not exist yet.

Run from the project root folder:
    venv\\Scripts\\python.exe scripts\\create_database.py

How it works:
1. Connects to PostgreSQL's built-in "postgres" database (it always exists).
2. Checks if "novamind_db" is already there.
3. If not, creates it. Safe to run many times.
"""

import sys
from pathlib import Path

# Let this script use the code inside the "backend" folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import create_engine, text  # noqa: E402

from config import Config  # noqa: E402


def main():
    db_name = Config.DB_NAME

    # Same login details, but connect to the built-in "postgres" database
    admin_url = Config.DATABASE_URL.set(database="postgres")

    # CREATE DATABASE cannot run inside a transaction, so use AUTOCOMMIT
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()

            if exists:
                print(f"Database '{db_name}' already exists. Nothing to do.")
            else:
                # Database names cannot be passed as parameters, so we quote it safely
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Database '{db_name}' created successfully.")
    except Exception as error:
        print(f"Could not create database: {type(error).__name__}: {str(error).splitlines()[0]}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

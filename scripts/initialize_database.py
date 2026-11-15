"""
initialize_database.py - Creates all NovaMind tables and fills the fixed "lookup" data.

Run from the project root folder:
    venv\\Scripts\\python.exe scripts\\initialize_database.py
    venv\\Scripts\\python.exe scripts\\initialize_database.py --reset   (DELETES all data first!)

What it does:
1. Creates every table defined in backend/models (skips tables that already exist).
2. Adds roles, access levels, departments, and the RBAC rules (which role sees what).
Safe to run many times: existing rows are not duplicated.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import inspect, select  # noqa: E402

import models  # noqa: E402,F401  (loads every table definition)
from database import Base, SessionLocal, engine  # noqa: E402
from models import AccessLevel, Department, Role  # noqa: E402

ROLES = {
    "Admin": "Full access: manage documents, users, and view all data",
    "Employee": "Standard employee: public and general employee documents",
    "HR": "Human Resources: employee documents plus HR-only documents",
    "Finance": "Finance team: employee documents plus Finance-only documents",
    "IT": "IT team: employee documents plus IT-only documents",
}

ACCESS_LEVELS = {
    "Public": "Anyone in the company can see it",
    "Employee": "All logged-in employees",
    "HR": "HR team only",
    "Finance": "Finance team only",
    "IT": "IT team only",
}

DEPARTMENTS = ["HR", "IT", "Finance", "Product", "General"]

# THE RBAC RULES: role -> access levels it can see
ROLE_ACCESS = {
    "Admin": ["Public", "Employee", "HR", "Finance", "IT"],
    "Employee": ["Public", "Employee"],
    "HR": ["Public", "Employee", "HR"],
    "Finance": ["Public", "Employee", "Finance"],
    "IT": ["Public", "Employee", "IT"],
}


def get_or_create(session, model, name, **extra):
    """Return the row with this name, creating it if it does not exist yet."""
    row = session.scalar(select(model).where(model.name == name))
    if row is None:
        row = model(name=name, **extra)
        session.add(row)
        session.flush()  # gives the row its id now
    return row


def seed(session):
    levels = {n: get_or_create(session, AccessLevel, n, description=d) for n, d in ACCESS_LEVELS.items()}
    roles = {n: get_or_create(session, Role, n, description=d) for n, d in ROLES.items()}
    for name in DEPARTMENTS:
        get_or_create(session, Department, name)

    for role_name, level_names in ROLE_ACCESS.items():
        role = roles[role_name]
        for level_name in level_names:
            if levels[level_name] not in role.access_levels:
                role.access_levels.append(levels[level_name])


def main():
    parser = argparse.ArgumentParser(description="Create NovaMind tables and seed lookup data.")
    parser.add_argument("--reset", action="store_true", help="DROP all tables first (deletes all data)")
    args = parser.parse_args()

    if args.reset:
        print("WARNING: --reset given. Dropping ALL NovaMind tables and data...")
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)
    tables = sorted(inspect(engine).get_table_names())
    print(f"Tables ready ({len(tables)}): {', '.join(tables)}")

    with SessionLocal() as session:
        seed(session)
        session.commit()

        print("\nRBAC rules (role -> can see):")
        for role in session.scalars(select(Role).order_by(Role.id)):
            names = ", ".join(sorted(level.name for level in role.access_levels))
            print(f"  {role.name:<9} -> {names}")

    print("\nDatabase initialized successfully.")


if __name__ == "__main__":
    main()

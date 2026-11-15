"""
create_sample_users.py - Creates the 5 test accounts (one per role).

Run from the project root folder:
    venv\\Scripts\\python.exe scripts\\create_sample_users.py

Password handling (development only):
- All 5 test users share ONE test password, read from SEED_USER_PASSWORD in .env.
- If it is missing, a strong random password is generated and SAVED into .env.
- The password is never printed on screen. Open .env to see it.
- Only its hash is stored in the database.
Safe to run many times: existing users are not duplicated.
"""

import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from database import SessionLocal  # noqa: E402
from models import Role, User  # noqa: E402
from utils.security import hash_password  # noqa: E402

ENV_FILE = ROOT / ".env"

SAMPLE_USERS = [
    # (username, email, full name, role)
    ("admin", "admin@technova.test", "TechNova Admin", "Admin"),
    ("employee", "employee@technova.test", "TechNova Employee", "Employee"),
    ("hr", "hr@technova.test", "TechNova HR", "HR"),
    ("finance", "finance@technova.test", "TechNova Finance", "Finance"),
    ("it", "it@technova.test", "TechNova IT", "IT"),
]


def get_seed_password() -> str:
    """Read the test password from .env, or create one and save it there."""
    password = os.getenv("SEED_USER_PASSWORD", "").strip()
    if password:
        return password

    password = "Nova-" + secrets.token_urlsafe(12)  # random, strong, typeable
    with open(ENV_FILE, "a", encoding="utf-8") as f:
        f.write(
            "\n# ---- Test user password (development only, created by create_sample_users.py) ----\n"
            f"SEED_USER_PASSWORD={password}\n"
        )
    print("A new test password was generated and saved in .env as SEED_USER_PASSWORD.")
    return password


def main():
    password_hash = hash_password(get_seed_password())  # hash once, reuse for all 5

    with SessionLocal() as session:
        roles = {r.name: r for r in session.scalars(select(Role))}
        if not roles:
            print("No roles found. Run scripts\\initialize_database.py first.")
            sys.exit(1)

        for username, email, full_name, role_name in SAMPLE_USERS:
            if session.scalar(select(User).where(User.email == email)):
                print(f"  exists   {email:<26} ({role_name})")
                continue
            session.add(User(
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                role=roles[role_name],
            ))
            print(f"  created  {email:<26} ({role_name})")

        session.commit()

    print("\nDone. Login password for all test users: see SEED_USER_PASSWORD in your .env file.")


if __name__ == "__main__":
    main()

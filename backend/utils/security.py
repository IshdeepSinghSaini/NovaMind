"""
security.py - Password hashing helpers.

We NEVER store real passwords. We store a "hash": a one-way scrambled version.
- hash_password("abc")        -> "scrypt:32768:8:1$<salt>$<hash>"
- verify_password(hash, "abc") -> True / False

scrypt is a slow-on-purpose algorithm, so guessing millions of passwords is very
expensive for an attacker. A random "salt" is added, so two users with the same
password still get different hashes.
"""

from werkzeug.security import check_password_hash, generate_password_hash

MIN_PASSWORD_LENGTH = 8


def hash_password(plain_password: str) -> str:
    """Turn a plain password into a safe hash for the database."""
    if not plain_password or len(plain_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    return generate_password_hash(plain_password, method="scrypt")


def verify_password(password_hash: str, plain_password: str) -> bool:
    """Check if a typed password matches the stored hash."""
    if not password_hash or not plain_password:
        return False
    return check_password_hash(password_hash, plain_password)

"""
test_security.py - Tests for password hashing (no database needed).
"""

import pytest

from utils.security import hash_password, verify_password


def test_hash_is_not_the_password():
    hashed = hash_password("CorrectHorse123")
    assert hashed != "CorrectHorse123"
    assert hashed.startswith("scrypt:")


def test_correct_password_matches():
    hashed = hash_password("CorrectHorse123")
    assert verify_password(hashed, "CorrectHorse123") is True


def test_wrong_password_does_not_match():
    hashed = hash_password("CorrectHorse123")
    assert verify_password(hashed, "WrongHorse123") is False


def test_same_password_gives_different_hashes():
    # Because of the random "salt"
    assert hash_password("SamePassword1") != hash_password("SamePassword1")


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_empty_inputs_never_match():
    assert verify_password("", "anything") is False
    assert verify_password(hash_password("CorrectHorse123"), "") is False

"""Simple password hashing with hashlib (sha256 + salt).

Avoids the passlib/bcrypt version incompatibility for this demo project.
In production, replace with bcrypt or argon2.
"""

import hashlib
import os


def hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256."""
    salt = os.urandom(32).hex()
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a salted SHA-256 hash."""
    try:
        salt, h = hashed.split("$", 1)
        expected = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return h == expected
    except Exception:
        return False

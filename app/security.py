"""Password, JWT middleware, and output-encoding helpers."""

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from flask_jwt_extended import verify_jwt_in_request
from markupsafe import escape


# Argon2id settings provide a sensible baseline for an educational API. The
# library creates a unique random salt for every password automatically.
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65_536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

# Used only to make unknown-user login attempts perform a password hash check,
# reducing the timing difference that could otherwise reveal valid usernames.
_dummy_hash = _password_hasher.hash("not-a-real-user-password")

F = TypeVar("F", bound=Callable[..., Any])


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_dummy_password(password: str) -> None:
    """Perform comparable work when a username does not exist."""
    verify_password(_dummy_hash, password)


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def escape_text(value: str) -> str:
    """HTML-escape untrusted text before it leaves the API."""
    return str(escape(value))


def auth_required(view: F) -> F:
    """Reusable authentication middleware for protected endpoints."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        verify_jwt_in_request()
        return view(*args, **kwargs)

    return cast(F, wrapped)


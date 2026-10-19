"""Small, explicit validation helpers for JSON request bodies."""

import re
from typing import Any

from flask import request


_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")


def require_json_object() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    return payload


def require_string(
    payload: dict[str, Any],
    field: str,
    *,
    minimum: int = 1,
    maximum: int,
    strip: bool = True,
) -> str:
    value = payload.get(field)
    if not isinstance(value, str):
        raise ValueError(f"'{field}' must be a string.")

    clean_value = value.strip() if strip else value
    if not minimum <= len(clean_value) <= maximum:
        raise ValueError(
            f"'{field}' must contain between {minimum} and {maximum} characters."
        )
    return clean_value


def validate_username(username: str) -> str:
    clean_username = username.strip()
    if not _USERNAME_RE.fullmatch(clean_username):
        raise ValueError(
            "Username must be 3-64 characters and contain only letters, "
            "digits, dots, underscores, or hyphens."
        )
    return clean_username


def validate_new_password(password: str) -> None:
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must contain between 12 and 128 characters.")


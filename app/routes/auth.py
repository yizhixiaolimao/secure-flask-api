"""Authentication endpoints."""

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import create_access_token
from sqlalchemy import select

from app.extensions import db, limiter
from app.models import User
from app.security import (
    escape_text,
    password_needs_rehash,
    verify_dummy_password,
)
from app.validation import require_json_object, require_string, validate_username


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
BEARER_SCHEME = "Bearer"


@auth_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    """Authenticate a user and issue a short-lived JWT access token."""
    try:
        payload = require_json_object()
        username = validate_username(
            require_string(payload, "login", maximum=64)
        )
        password = require_string(
            payload, "password", maximum=256, strip=False
        )
    except ValueError as exc:
        return jsonify(
            {"error": {"code": "validation_error", "message": str(exc)}}
        ), 400

    # SQLAlchemy binds username as a query parameter; it is never interpolated
    # into the SQL string.
    user = db.session.scalar(select(User).where(User.username == username))

    if user is None:
        verify_dummy_password(password)
        return _invalid_credentials()

    if not user.is_active or not user.check_password(password):
        return _invalid_credentials()

    if password_needs_rehash(user.password_hash):
        user.set_password(password)
        db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        fresh=True,
        additional_claims={"username": user.username},
    )
    expires = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    response = jsonify(
        {
            "access_token": access_token,
            "token_type": BEARER_SCHEME,
            "expires_in": int(expires.total_seconds()),
            "user": {"id": user.id, "username": escape_text(user.username)},
        }
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response, 200


def _invalid_credentials():
    # One generic response prevents username enumeration.
    return jsonify(
        {
            "error": {
                "code": "invalid_credentials",
                "message": "Invalid login or password.",
            }
        }
    ), 401


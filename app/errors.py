"""Consistent JSON error responses and JWT callback handlers."""

from typing import Any

from flask import Flask, jsonify

from app.extensions import db, jwt


def json_error(message: str, status: int, code: str):
    return jsonify({"error": {"code": code, "message": message}}), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(_error: Any):
        return json_error("The request is invalid.", 400, "bad_request")

    @app.errorhandler(404)
    def not_found(_error: Any):
        return json_error("The requested resource was not found.", 404, "not_found")

    @app.errorhandler(405)
    def method_not_allowed(_error: Any):
        return json_error("HTTP method not allowed.", 405, "method_not_allowed")

    @app.errorhandler(413)
    def payload_too_large(_error: Any):
        return json_error("Request body is too large.", 413, "payload_too_large")

    @app.errorhandler(429)
    def rate_limited(_error: Any):
        return json_error(
            "Too many requests. Please try again later.",
            429,
            "rate_limit_exceeded",
        )

    @app.errorhandler(500)
    def internal_error(_error: Any):
        db.session.rollback()
        return json_error(
            "An internal error occurred.", 500, "internal_server_error"
        )

    @jwt.unauthorized_loader
    def missing_token(_reason: str):
        return json_error(
            "A valid Bearer token is required.", 401, "authorization_required"
        )

    @jwt.invalid_token_loader
    def invalid_token(_reason: str):
        return json_error("The access token is invalid.", 401, "invalid_token")

    @jwt.expired_token_loader
    def expired_token(_header: dict[str, Any], _payload: dict[str, Any]):
        return json_error("The access token has expired.", 401, "token_expired")

    @jwt.revoked_token_loader
    def revoked_token(_header: dict[str, Any], _payload: dict[str, Any]):
        return json_error("The access token was revoked.", 401, "token_revoked")

    @jwt.needs_fresh_token_loader
    def fresh_token_required(_header: dict[str, Any], _payload: dict[str, Any]):
        return json_error("A fresh access token is required.", 401, "fresh_token_required")


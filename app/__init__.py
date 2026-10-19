"""Application factory for the secure Flask API."""

from pathlib import Path

import click
from flask import Flask, jsonify, request

from app.errors import register_error_handlers
from app.extensions import db, jwt, limiter


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""
    from app.config import Config

    app = Flask(__name__, instance_relative_config=True, static_folder=None)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    _validate_security_config(app)

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    # Import models before db.create_all() can be called by a CLI command.
    from app import models  # noqa: F401
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    register_error_handlers(app)
    _register_cli_commands(app)
    _register_security_headers(app)

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        """Unauthenticated liveness endpoint for local checks/monitoring."""
        return {"status": "ok"}, 200

    return app


def _validate_security_config(app: Flask) -> None:
    """Fail fast when a real environment uses a weak JWT signing key."""
    if app.config.get("TESTING"):
        return

    jwt_secret = app.config.get("JWT_SECRET_KEY", "")
    if not isinstance(jwt_secret, str) or len(jwt_secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a random value of at least 32 characters. "
            "See .env.example."
        )


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        # The service returns JSON only, so scripts, frames, and embedded content
        # are never needed.
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        # HSTS is useful only when the request actually arrived over HTTPS.
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


def _register_cli_commands(app: Flask) -> None:
    from sqlalchemy import select

    from app.models import User
    from app.validation import validate_new_password, validate_username

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create the SQLite tables without deleting existing data."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-user")
    @click.option("--username", prompt=True, help="3-64 letters, digits, . _ or -")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="At least 12 characters",
    )
    def create_user_command(username: str, password: str) -> None:
        """Create a user while keeping the password out of shell history."""
        try:
            clean_username = validate_username(username)
            validate_new_password(password)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

        existing = db.session.scalar(
            select(User).where(User.username == clean_username)
        )
        if existing:
            raise click.ClickException("That username already exists.")

        user = User(username=clean_username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"User '{clean_username}' created.")


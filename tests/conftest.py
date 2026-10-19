"""Shared pytest fixtures."""

import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.sqlite"
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "JWT_SECRET_KEY": "test-only-secret-key-that-is-long-enough-123456",
            "RATELIMIT_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()
        user = User(username="alice")
        user.set_password("CorrectHorseBatteryStaple!42")
        db.session.add(user)
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def access_token(client) -> str:
    response = client.post(
        "/auth/login",
        json={
            "login": "alice",
            "password": "CorrectHorseBatteryStaple!42",
        },
    )
    return response.get_json()["access_token"]


@pytest.fixture()
def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


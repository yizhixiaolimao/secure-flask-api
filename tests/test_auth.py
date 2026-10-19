"""Authentication behavior tests."""

from sqlalchemy import select

from app.extensions import db
from app.models import User


def test_login_returns_short_lived_token(client):
    response = client.post(
        "/auth/login",
        json={
            "login": "alice",
            "password": "CorrectHorseBatteryStaple!42",
        },
    )

    body = response.get_json()
    assert response.status_code == 200
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 900
    assert body["access_token"]
    assert "password" not in str(body).lower()
    assert response.headers["Cache-Control"] == "no-store"


def test_wrong_password_uses_generic_error(client):
    response = client.post(
        "/auth/login",
        json={"login": "alice", "password": "totally-wrong-password"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"


def test_unknown_user_uses_same_generic_error(client):
    response = client.post(
        "/auth/login",
        json={"login": "nobody", "password": "totally-wrong-password"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"


def test_sql_injection_string_cannot_bypass_login(client, app):
    response = client.post(
        "/auth/login",
        json={"login": "alice' OR '1'='1", "password": "anything"},
    )

    assert response.status_code in {400, 401}
    with app.app_context():
        assert db.session.scalar(select(User).where(User.username == "alice"))


def test_password_is_an_argon2_hash(app):
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "alice"))
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert "CorrectHorseBatteryStaple!42" not in user.password_hash


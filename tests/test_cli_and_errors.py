"""CLI commands and generic HTTP error tests."""

from sqlalchemy import select

from app.extensions import db
from app.models import User


def test_create_user_cli(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["create-user", "--username", "bob"],
        input="AnotherStrongPassword!42\nAnotherStrongPassword!42\n",
    )

    assert result.exit_code == 0
    assert "User 'bob' created." in result.output
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "bob"))
        assert user is not None
        assert user.check_password("AnotherStrongPassword!42")


def test_create_user_cli_rejects_duplicate(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["create-user", "--username", "alice"],
        input="AnotherStrongPassword!42\nAnotherStrongPassword!42\n",
    )

    assert result.exit_code != 0
    assert "already exists" in result.output


def test_init_db_cli_is_idempotent(app):
    result = app.test_cli_runner().invoke(args=["init-db"])

    assert result.exit_code == 0
    assert "Database tables created." in result.output


def test_generic_not_found_and_method_errors(client):
    not_found = client.get("/does-not-exist")
    wrong_method = client.post("/health")

    assert not_found.status_code == 404
    assert not_found.get_json()["error"]["code"] == "not_found"
    assert wrong_method.status_code == 405
    assert wrong_method.get_json()["error"]["code"] == "method_not_allowed"


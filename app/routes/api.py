"""Protected application endpoints."""

from flask import Blueprint, jsonify, url_for
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import select

from app.extensions import db
from app.models import Post, User
from app.security import auth_required, escape_text
from app.validation import require_json_object, require_string


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/data")
@auth_required
def get_data():
    """Return the newest posts to an authenticated user."""
    posts = db.session.scalars(
        select(Post).order_by(Post.created_at.desc(), Post.id.desc()).limit(100)
    ).all()

    data = [_serialize_post(post) for post in posts]
    return jsonify({"count": len(data), "data": data}), 200


@api_bp.post("/posts")
@auth_required
def create_post():
    """Create a post owned by the authenticated user."""
    try:
        payload = require_json_object()
        title = require_string(payload, "title", maximum=120)
        content = require_string(payload, "content", maximum=2_000)
    except ValueError as exc:
        return jsonify(
            {"error": {"code": "validation_error", "message": str(exc)}}
        ), 400

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify(
            {"error": {"code": "invalid_token", "message": "Invalid token identity."}}
        ), 401

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        return jsonify(
            {
                "error": {
                    "code": "account_unavailable",
                    "message": "The account is unavailable.",
                }
            }
        ), 403

    # Only explicitly allowed fields are assigned. Unknown JSON properties are
    # ignored, preventing mass-assignment of author_id or other model fields.
    post = Post(title=title, content=content, author_id=user.id)
    db.session.add(post)
    db.session.commit()

    response = jsonify({"data": _serialize_post(post)})
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_data") + f"#post-{post.id}"
    return response


def _serialize_post(post: Post) -> dict:
    """Apply contextual output encoding to all stored user-controlled text."""
    return {
        "id": post.id,
        "title": escape_text(post.title),
        "content": escape_text(post.content),
        "author": escape_text(post.author.username),
        "created_at": post.created_at.isoformat(),
    }


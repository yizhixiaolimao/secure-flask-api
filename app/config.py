"""Configuration loaded from environment variables."""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Default configuration for development and deployment."""

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///secure_api.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))
    )
    JWT_ALGORITHM = "HS256"
    JWT_TOKEN_LOCATION = ["headers"]

    # Keep request bodies small because this API accepts only short JSON fields.
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "16384"))

    # memory:// is appropriate for one-process teaching/demo use. Production
    # deployments should point this at Redis so limits are shared by all workers.
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True


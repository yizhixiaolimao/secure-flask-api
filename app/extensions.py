"""Flask extension instances shared across modules."""

from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


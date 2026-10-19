"""WSGI entry point used by Flask and production WSGI servers."""

from app import create_app

app = create_app()


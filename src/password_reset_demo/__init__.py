"""Flask application scaffold; routes and state are added in later tasks."""

from flask import Flask


def create_app() -> Flask:
    """Create an independent Flask app with package-relative Jinja templates."""
    return Flask(__name__)

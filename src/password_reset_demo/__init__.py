"""Local synthetic Flask app; user-facing routes are added in later tasks."""

import os
import secrets

from flask import Flask

from password_reset_demo.csrf import csrf_token
from password_reset_demo.state import Clock, create_store


def create_app(*, clock: Clock | None = None) -> Flask:
    """Create an independent app with signed sessions and private in-memory state."""
    secret = os.environ.get("PASSWORD_RESET_SESSION_SECRET")
    if not secret:
        raise RuntimeError("PASSWORD_RESET_SESSION_SECRET must be configured")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret
    app.extensions["reset_store"] = create_store(clock)
    app.extensions["csrf_app_id"] = secrets.token_urlsafe(16)
    app.context_processor(lambda: {"csrf_token": csrf_token})
    return app

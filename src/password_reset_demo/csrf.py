"""Session-bound CSRF state, independent of account identity or lookup."""

import secrets

from flask import current_app, session

_SESSION_KEY = "_csrf_token"
_APP_KEY = "_csrf_app_id"


def csrf_token() -> str:
    """Return a random token that does not depend on the selected account."""
    token = session.get(_SESSION_KEY)
    if (
        session.get(_APP_KEY) != current_app.extensions["csrf_app_id"]
        or not isinstance(token, str)
        or not token
    ):
        token = secrets.token_urlsafe(32)
        session[_SESSION_KEY] = token
        session[_APP_KEY] = current_app.extensions["csrf_app_id"]
    return token


def valid_csrf_token(submitted: str | None) -> bool:
    """Only accept a token already issued for this signed client session."""
    expected = session.get(_SESSION_KEY)
    return (
        session.get(_APP_KEY) == current_app.extensions["csrf_app_id"]
        and isinstance(expected, str)
        and isinstance(submitted, str)
        and secrets.compare_digest(expected, submitted)
    )

"""Local synthetic Flask app and server-rendered demonstration pages."""

import os
import secrets

from flask import (
    Flask,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from password_reset_demo import recovery
from password_reset_demo.csrf import csrf_token, valid_csrf_token
from password_reset_demo.logging_policy import install_token_log_redaction
from password_reset_demo.state import Clock, create_store, normalize_email, token_digest


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
    install_token_log_redaction(app.logger)

    @app.get("/")
    def sign_in():
        return render_template("sign_in.html")

    @app.post("/sign-in")
    def submit_sign_in():
        if not valid_csrf_token(request.form.get("csrf_token")):
            abort(400)

        email = request.form.get("email", "")
        password = request.form.get("password", "")
        email_error = "Enter an email address." if not email.strip() else None
        password_error = "Enter a password." if not password else None
        if email_error or password_error:
            session.pop("account_id", None)
            session.pop("session_version", None)
            return render_template(
                "sign_in.html", email_error=email_error, password_error=password_error
            ), 400

        store = app.extensions["reset_store"]
        with store.lock:
            key = normalize_email(email)
            account = store.accounts.get(key)
            if account is not None and check_password_hash(
                account.password_hash, password
            ):
                # Discard any prior identity and rotate CSRF state on a new sign-in.
                session.clear()
                session["account_id"] = key
                session["session_version"] = account.session_version
                return redirect(url_for("demo"), code=303)

        session.pop("account_id", None)
        session.pop("session_version", None)
        return render_template(
            "sign_in.html", password_error="Invalid email address or password."
        ), 401

    @app.get("/demo")
    def demo():
        store = app.extensions["reset_store"]
        account_id = session.get("account_id")
        version = session.get("session_version")
        with store.lock:
            account = (
                store.accounts.get(account_id) if isinstance(account_id, str) else None
            )
            if (
                account is not None
                and type(version) is int
                and version == account.session_version
            ):
                email = account.email
            else:
                email = None
        if email is None:
            if "account_id" in session or "session_version" in session:
                session.clear()
            return redirect(url_for("sign_in"), code=303)

        response = make_response(render_template("demo.html", email=email))
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/forgot-password")
    def forgot_password():
        return render_template("forgot_password.html")

    @app.post("/forgot-password")
    def submit_forgot_password():
        if not valid_csrf_token(request.form.get("csrf_token")):
            abort(400)

        address = request.form.get("email", "")
        if not recovery.valid_address_syntax(address):
            email_error = (
                "Enter an email address."
                if not address.strip()
                else "Enter a valid email address."
            )
            return render_template("forgot_password.html", email_error=email_error), 400

        # The private service owns lookup and throttling. Neither its result
        # nor account state affects the response or signed session.
        recovery._issue_reset_request(
            app.extensions["reset_store"], normalize_email(address)
        )
        return redirect(url_for("reset_requested"), code=303)

    @app.get("/reset-requested")
    def reset_requested():
        return render_template("reset_requested.html")

    @app.get("/reset/<token>")
    def reset_link(token: str):
        store = app.extensions["reset_store"]
        with store.lock:
            record = store.reset_records.get(token_digest(token))
            usable = (
                record is not None
                and record.consumed_at is None
                and store.now() < record.expires_at
            )
        if usable:
            return render_template("reset_password.html")
        return render_template("reset_unavailable.html")

    @app.after_request
    def protect_token_pages(response):
        # Include method errors too: they still have a bearer token in the URL.
        if request.path.startswith("/reset/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    return app

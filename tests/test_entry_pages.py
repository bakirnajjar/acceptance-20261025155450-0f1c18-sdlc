"""TASK-002 DOM coverage: page presentation and recovery entry only."""

import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path

import pytest
from flask import Flask, render_template

from password_reset_demo import create_app


class Page(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.tokens: list[tuple[str, dict[str, str | None] | str]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tokens.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        if text := data.strip():
            self.tokens.append(("text", text))

    def element(self, tag: str, **attributes: str) -> dict[str, str | None]:
        for node_tag, attrs in self.tokens:
            if (
                node_tag == tag
                and isinstance(attrs, dict)
                and all(attrs.get(key) == value for key, value in attributes.items())
            ):
                return attrs
        raise AssertionError(f"Missing {tag} with {attributes}")

    def index(self, tag: str, **attributes: str) -> int:
        for index, (node_tag, attrs) in enumerate(self.tokens):
            if (
                node_tag == tag
                and isinstance(attrs, dict)
                and all(attrs.get(key) == value for key, value in attributes.items())
            ):
                return index
        raise AssertionError(f"Missing {tag} with {attributes}")


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "entry-page-test-key")
    return create_app()


def test_tc_001_sign_in_card_labels_empty_fields_and_examples(app) -> None:
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    page = Page(response.get_data(as_text=True))
    assert page.element("html")["lang"] == "en"
    assert (
        sum(
            tag == "section"
            and isinstance(attrs, dict)
            and attrs.get("class") == "card"
            for tag, attrs in page.tokens
        )
        == 1
    )
    assert page.element("section", **{"class": "card"})["aria-labelledby"] == (
        "sign-in-heading"
    )
    assert page.element("h1", id="sign-in-heading")
    assert ("text", "Sign in") in page.tokens
    assert page.element("form")["method"] == "post"
    assert page.element("form")["action"] == "/sign-in"
    assert page.element("input", name="csrf_token")["value"]

    assert page.element("label", **{"for": "sign-in-email"})
    assert page.element("label", **{"for": "sign-in-password"})
    assert ("text", "Email address") in page.tokens
    assert ("text", "Password") in page.tokens
    email = page.element("input", id="sign-in-email")
    password = page.element("input", id="sign-in-password")
    assert (email["type"], email["placeholder"]) == ("email", "name@example.com")
    assert (password["type"], password["placeholder"]) == ("password", "********")
    assert email.get("value", "") == password.get("value", "") == ""
    assert (
        page.index("h1", id="sign-in-heading")
        < page.index("label", **{"for": "sign-in-email"})
        < page.index("input", id="sign-in-email")
    )
    assert page.index("label", **{"for": "sign-in-password"}) < page.index(
        "input", id="sign-in-password"
    )

    stylesheet = page.element("link", rel="stylesheet")["href"]
    assert stylesheet == "/static/styles.css"
    css_response = app.test_client().get(stylesheet)
    assert css_response.status_code == 200
    css = css_response.get_data(as_text=True)
    assert "background: #fff;" in css
    assert "justify-content: center;" in css
    assert "align-items: center;" in css
    assert ".card {" in css and "border: 1px solid" in css
    assert "font-weight: 700;" in css


def test_tc_002_sign_in_visual_and_dom_order(app) -> None:
    page = Page(app.test_client().get("/").get_data(as_text=True))
    assert (
        page.index("input", id="sign-in-email")
        < page.index("input", id="sign-in-password")
        < page.index("a", **{"class": "recovery-link"})
        < page.index("button", **{"class": "primary-button"})
        < page.tokens.index(("text", "No account? Contact your administrator."))
    )
    assert ("text", "Forgot password?") in page.tokens
    assert page.element("a", **{"class": "recovery-link"})["href"] == (
        "/forgot-password"
    )
    assert page.element("button", **{"class": "primary-button"})["type"] == "submit"
    css = (
        Path(__file__).parents[1] / "src/password_reset_demo/static/styles.css"
    ).read_text()
    assert "text-decoration: underline;" in css
    assert "a { color: #135ba1;" in css
    assert "background: #212a36;" in css
    assert ".primary-button {" in css and "width: 100%;" in css
    assert ".support-text {" in css and "color: #596577;" in css
    assert ":focus-visible" in css


def test_tc_003_recovery_link_opens_csrf_ready_accessible_request_form(app) -> None:
    client = app.test_client()
    sign_in = Page(client.get("/").get_data(as_text=True))
    entry = sign_in.element("a", **{"class": "recovery-link"})["href"]
    assert entry == "/forgot-password"
    response = client.get(entry)
    assert response.status_code == 200
    page = Page(response.get_data(as_text=True))

    assert page.element("section", **{"class": "card"})["aria-labelledby"] == (
        "reset-heading"
    )
    assert ("text", "Enter your email address to request a password reset.") in (
        page.tokens
    )
    assert page.element("form")["method"] == "post"
    assert page.element("form")["action"] == entry
    csrf = page.element("input", name="csrf_token")
    assert csrf["type"] == "hidden" and csrf["value"]
    with client.session_transaction() as session:
        assert session["_csrf_token"] == csrf["value"]
    assert page.element("label", **{"for": "reset-email"})
    assert page.element("input", id="reset-email")["type"] == "email"
    assert page.element("input", id="reset-email").get("value", "") == ""
    assert (
        page.index("input", id="reset-email")
        < page.index("button", **{"class": "primary-button"})
        < page.index("a", **{"class": "return-link"})
    )
    assert page.element("a", **{"class": "return-link"})["href"] == "/"
    assert ("text", "Request password reset") in page.tokens
    assert all(
        "tabindex" not in attrs
        for tag, attrs in page.tokens
        if tag in {"input", "button", "a"} and isinstance(attrs, dict)
    )
    return_path = page.element("a", **{"class": "return-link"})["href"]
    assert client.get(return_path).status_code == 200


def test_tc_014_python_312_flask_renders_request_pages(app) -> None:
    """The local Python 3.12 client receives HTML from the Flask/Jinja routes."""
    assert sys.version_info[:2] == (3, 12)
    metadata = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert metadata["project"]["requires-python"] == ">=3.12"
    assert any(dep.startswith("flask==") for dep in metadata["project"]["dependencies"])
    assert isinstance(app, Flask)
    client = app.test_client()
    for path, heading in (
        ("/", "sign-in-heading"),
        ("/forgot-password", "reset-heading"),
        ("/reset-requested", "requested-heading"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.mimetype == "text/html"
        assert Page(response.get_data(as_text=True)).element("h1", id=heading)
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
    assert (
        client.post(
            "/forgot-password",
            data={"email": "owner@example.test", "csrf_token": csrf},
        ).status_code
        == 303
    )
    url = app.extensions["reset_store"].owner_link_outbox[-1].url
    for path, heading, has_form in (
        (url, "new-password-heading", True),
        ("/reset/unknown-opaque-token", "unavailable-heading", False),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.mimetype == "text/html"
        page = Page(response.get_data(as_text=True))
        assert page.element("h1", id=heading)
        assert any(tag == "form" for tag, _ in page.tokens) is has_form


@pytest.mark.parametrize(
    ("template", "field_id", "error_id"),
    [
        ("sign_in.html", "sign-in-email", "sign-in-email-error"),
        ("sign_in.html", "sign-in-password", "sign-in-password-error"),
        ("forgot_password.html", "reset-email", "reset-email-error"),
    ],
)
def test_entry_forms_associate_future_field_errors(
    app, template, field_id, error_id
) -> None:
    with app.test_request_context("/"):
        error = {"email_error": "Check the address."}
        if field_id == "sign-in-password":
            error = {"password_error": "Check the password."}
        page = Page(render_template(template, **error))
    field = page.element("input", id=field_id)
    assert field["aria-invalid"] == "true"
    assert field["aria-describedby"] == error_id
    assert field["autofocus"] is None
    assert page.element("p", id=error_id)["role"] == "alert"
    assert ("text", next(iter(error.values()))) in page.tokens


def test_entry_form_multiple_errors_focus_first_field_and_escape_copy(app) -> None:
    with app.test_request_context("/"):
        html = render_template(
            "sign_in.html",
            email_error="<check address>",
            password_error="Check password.",
        )
    page = Page(html)
    assert page.element("input", id="sign-in-email")["autofocus"] is None
    assert "autofocus" not in page.element("input", id="sign-in-password")
    assert "&lt;check address&gt;" in html
    assert "<check address>" not in html


def test_tc_024_dom_only_labels_focus_hints_field_errors_and_outcomes(app) -> None:
    """Static DOM contracts only; keyboard, reader and contrast need manual review."""
    client = app.test_client()
    for path, field_id, label, button in (
        ("/", "sign-in-email", "Email address", "Sign in"),
        ("/forgot-password", "reset-email", "Email address", "Request password reset"),
    ):
        page = Page(client.get(path).get_data(as_text=True))
        assert page.element("label", **{"for": field_id})
        assert ("text", label) in page.tokens
        assert ("text", button) in page.tokens
        assert page.index("input", id=field_id) < page.index("button", type="submit")
        assert all(
            "tabindex" not in attrs
            for tag, attrs in page.tokens
            if tag in {"input", "button", "a"} and isinstance(attrs, dict)
        )
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]

    invalid_sign_in = client.post(
        "/sign-in",
        data={"csrf_token": csrf, "email": "", "password": ""},
    )
    sign_in_page = Page(invalid_sign_in.get_data(as_text=True))
    assert invalid_sign_in.status_code == 400
    assert sign_in_page.element("input", id="sign-in-email")["autofocus"] is None
    assert "autofocus" not in sign_in_page.element("input", id="sign-in-password")
    for field, error in (
        ("sign-in-email", "sign-in-email-error"),
        ("sign-in-password", "sign-in-password-error"),
    ):
        assert sign_in_page.element("label", **{"for": field})
        assert sign_in_page.element("input", id=field)["aria-describedby"] == error
        assert sign_in_page.element("input", id=field)["aria-invalid"] == "true"
        assert sign_in_page.element("p", id=error)["role"] == "alert"

    invalid_request = client.post(
        "/forgot-password",
        data={"csrf_token": csrf, "email": "not-an-address"},
    )
    request_page = Page(invalid_request.get_data(as_text=True))
    assert invalid_request.status_code == 400
    assert request_page.element("label", **{"for": "reset-email"})
    assert request_page.element("input", id="reset-email")["autofocus"] is None
    assert request_page.element("input", id="reset-email")["aria-describedby"] == (
        "reset-email-error"
    )
    assert request_page.element("p", id="reset-email-error")["role"] == "alert"

    requested = client.post(
        "/forgot-password",
        data={"csrf_token": csrf, "email": "owner@example.test"},
    )
    assert requested.status_code == 303
    assert requested.headers["Location"] == "/reset-requested"
    requested_page = Page(
        client.get(requested.headers["Location"]).get_data(as_text=True)
    )
    assert requested_page.element("h1", id="requested-heading")["tabindex"] == "-1"
    assert requested_page.element("p", role="status")
    assert requested_page.element("a", href="/")

    store = app.extensions["reset_store"]
    reset_url = store.owner_link_outbox[-1].url
    form_page = Page(client.get(reset_url).get_data(as_text=True))
    assert form_page.element("label", **{"for": "new-password"})
    assert ("text", "New password") in form_page.tokens
    assert ("text", "Reset password") in form_page.tokens
    assert form_page.index("input", id="new-password") < form_page.index(
        "button", type="submit"
    )
    invalid_password = client.post(
        reset_url, data={"csrf_token": csrf, "password": "  "}
    )
    assert invalid_password.status_code == 400
    password_page = Page(invalid_password.get_data(as_text=True))
    assert password_page.element("input", id="new-password")["autofocus"] is None
    assert password_page.element("input", id="new-password")["aria-invalid"] == "true"
    assert password_page.element("input", id="new-password")["aria-describedby"] == (
        "new-password-error"
    )
    assert password_page.element("p", id="new-password-error")["role"] == "alert"
    assert password_page.element("label", **{"for": "new-password"})

    completed = client.post(reset_url, data={"csrf_token": csrf, "password": "test"})
    assert (completed.status_code, completed.headers["Location"]) == (
        303,
        "/reset-complete",
    )
    complete_page = Page(client.get("/reset-complete").get_data(as_text=True))
    assert complete_page.element("h1", id="complete-heading")["tabindex"] == "-1"
    assert complete_page.element("p", role="status")
    assert complete_page.element("a", href="/")
    unavailable_page = Page(client.get(reset_url).get_data(as_text=True))
    assert unavailable_page.element("h1", id="unavailable-heading")["tabindex"] == "-1"
    assert unavailable_page.element("p", role="alert")
    assert unavailable_page.element("a", href="/forgot-password")
    assert not any(tag == "form" for tag, _ in unavailable_page.tokens)
    css = client.get("/static/styles.css").get_data(as_text=True)
    assert ":focus-visible" in css and "outline:" in css


def test_recovery_post_requires_csrf(app) -> None:
    client = app.test_client()
    assert client.post("/sign-in").status_code == 400
    assert client.post("/forgot-password").status_code == 400

"""TASK-002 DOM coverage: page presentation and recovery entry only."""

from html.parser import HTMLParser
from pathlib import Path

import pytest
from flask import render_template

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
    page = Page(response.get_data(as_text=True))
    assert page.element("html")["lang"] == "en"
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


def test_recovery_post_handler_remains_for_later_task(app) -> None:
    client = app.test_client()
    assert client.post("/sign-in").status_code == 400
    assert client.post("/forgot-password").status_code == 405

"""TASK-004: neutral request surface, syntax feedback and CSRF boundary."""

from datetime import UTC, datetime
from html.parser import HTMLParser

import pytest

from password_reset_demo import create_app, recovery
from password_reset_demo.state import normalize_email

T0 = datetime(2026, 1, 1, 12, tzinfo=UTC)


class FormPage(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.text: list[str] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.text.append(data.strip())

    def element(self, tag: str, **attributes: str) -> dict[str, str | None]:
        for node_tag, attrs in self.elements:
            if node_tag == tag and all(
                attrs.get(key) == value for key, value in attributes.items()
            ):
                return attrs
        raise AssertionError(f"Missing {tag} with {attributes}")


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "request-test-key")
    return create_app(clock=lambda: T0)


def ready_client(app):
    client = app.test_client()
    entry = client.get("/forgot-password")
    assert entry.status_code == 200
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
        assert csrf and session.get("account_id") is None
    return client, csrf


@pytest.mark.parametrize("private_count", [0, 4, 5])
def test_tc_004_valid_request_surface_independent_of_owner_and_throttle(
    app, monkeypatch: pytest.MonkeyPatch, private_count: int
) -> None:
    store = app.extensions["reset_store"]
    owner, absent = "owner@example.test", "absent@example.test"
    for address in (owner, absent):
        store.request_times[normalize_email(address)] = [T0] * private_count

    calls = []

    def private_handoff(store_arg, key):
        assert store_arg is store
        calls.append(key)
        # Simulate TASK-005 distinguishing an eligible owner, a missing
        # address and a throttled key. The public handler ignores the result.
        return key in store_arg.accounts and len(store_arg.request_times[key]) < 5

    monkeypatch.setattr(recovery, "_issue_reset_request", private_handoff)
    results = []
    for address in (" OWNER@EXAMPLE.TEST ", " Absent@Example.Test "):
        client, csrf = ready_client(app)
        response = client.post(
            "/forgot-password", data={"email": address, "csrf_token": csrf}
        )
        destination = client.get(response.headers["Location"])
        assert response.status_code == 303
        assert response.headers["Location"] == "/reset-requested"
        assert destination.status_code == 200
        assert destination.mimetype == "text/html"
        page = FormPage(destination.get_data(as_text=True))
        assert page.element("h1", id="requested-heading")["tabindex"] == "-1"
        assert page.element("p", role="status")
        assert page.element("a", href="/")
        assert any("If an account exists" in text for text in page.text)
        for public in (response, destination):
            surface = str(public.headers) + public.get_data(as_text=True)
            assert address.strip() not in surface
            assert (
                owner not in surface and absent not in surface and csrf not in surface
            )
        results.append(
            (
                response.status_code,
                response.headers["Location"],
                list(response.headers.items()),
                response.data,
                destination.status_code,
                list(destination.headers.items()),
                destination.data,
            )
        )

    assert results[0] == results[1]  # Includes Set-Cookie and all public headers.
    assert calls == [owner, absent]
    assert store.owner_link_outbox == []
    assert store.reset_records == {}
    assert store.request_times == {
        owner: [T0] * private_count,
        absent: [T0] * private_count,
    }


@pytest.mark.parametrize(
    ("address", "message"),
    [
        ("", "Enter an email address."),
        ("   ", "Enter an email address."),
        ("not-an-address", "Enter a valid email address."),
        ("owner@example..test", "Enter a valid email address."),
        ("bad@@example.test", "Enter a valid email address."),
        ("owner @example.test", "Enter a valid email address."),
        ("a" * 65 + "@example.test", "Enter a valid email address."),
    ],
)
def test_tc_020_invalid_address_has_associated_error_before_lookup(
    app, monkeypatch: pytest.MonkeyPatch, address: str, message: str
) -> None:
    def forbidden(*_args):
        raise AssertionError("Invalid request reached account lookup or issuance")

    monkeypatch.setattr(recovery, "_issue_reset_request", forbidden)
    store = app.extensions["reset_store"]
    store.accounts = type("NoLookup", (dict,), {"get": forbidden})(store.accounts)
    client, csrf = ready_client(app)
    response = client.post(
        "/forgot-password", data={"email": address, "csrf_token": csrf}
    )
    assert response.status_code == 400
    page = FormPage(response.get_data(as_text=True))
    assert page.element("input", id="reset-email")["aria-invalid"] == "true"
    assert (
        page.element("input", id="reset-email")["aria-describedby"]
        == "reset-email-error"
    )
    assert page.element("input", id="reset-email")["autofocus"] is None
    assert page.element("p", id="reset-email-error")["role"] == "alert"
    assert message in page.text
    if address.strip():
        assert address.strip() not in response.get_data(as_text=True)
    assert store.request_times == {}
    assert store.owner_link_outbox == []


def test_csrf_state_and_rejection_do_not_consult_accounts(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*_args):
        raise AssertionError("CSRF rejection reached private issuance")

    monkeypatch.setattr(recovery, "_issue_reset_request", forbidden)
    store = app.extensions["reset_store"]
    store.accounts = type("NoLookup", (dict,), {"get": forbidden})(store.accounts)
    first, token = ready_client(app)
    second, other_token = ready_client(app)
    assert token != other_token
    for client, supplied in (
        (first, None),
        (first, "incorrect"),
        (second, token),
    ):
        response = client.post(
            "/forgot-password",
            data={
                "email": "owner@example.test",
                **({"csrf_token": supplied} if supplied is not None else {}),
            },
        )
        assert response.status_code == 400
        assert response.headers.get("Location") is None
        assert b"owner@example.test" not in response.data
    assert store.request_times == {}
    assert store.owner_link_outbox == []
    assert store.reset_records == {}


def test_account_like_invalid_addresses_receive_identical_feedback(app) -> None:
    responses = []
    for address in ("owner@example..test", "absent@example..test"):
        client, csrf = ready_client(app)
        response = client.post(
            "/forgot-password", data={"email": address, "csrf_token": csrf}
        )
        responses.append((response, response.data.replace(csrf.encode(), b"<csrf>")))
    assert all(response.status_code == 400 for response, _body in responses)
    assert responses[0][1] == responses[1][1]
    assert list(responses[0][0].headers.items()) == list(
        responses[1][0].headers.items()
    )

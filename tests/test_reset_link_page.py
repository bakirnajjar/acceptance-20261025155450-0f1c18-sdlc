"""TASK-006: GET visibility, expiry and token-page disclosure boundaries."""

import logging
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest

from password_reset_demo import create_app
from password_reset_demo.state import token_digest

T0 = datetime(2026, 1, 1, 12, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.value = T0

    def __call__(self) -> datetime:
        return self.value


class Page(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.nodes: list[tuple[str, dict[str, str | None]]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.nodes.append((tag, dict(attrs)))

    def element(self, tag: str, **attributes: str) -> dict[str, str | None]:
        for node_tag, attrs in self.nodes:
            if node_tag == tag and all(
                attrs.get(key) == value for key, value in attributes.items()
            ):
                return attrs
        raise AssertionError(f"Missing {tag} with {attributes}")


@pytest.fixture
def setup(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "reset-page-test-key")
    clock = FakeClock()
    app = create_app(clock=clock)
    client = app.test_client()
    client.get("/forgot-password")
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
    issued = client.post(
        "/forgot-password",
        data={"email": "owner@example.test", "csrf_token": csrf},
    )
    assert issued.status_code == 303
    store = app.extensions["reset_store"]
    assert len(store.owner_link_outbox) == 1
    url = store.owner_link_outbox[0].url
    token = url.removeprefix("/reset/")
    record = store.reset_records[token_digest(token)]
    return app, clock, client, store, url, token, record


def assert_token_page(response, token: str) -> Page:
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert token.encode() not in response.data
    assert token not in str(response.headers)
    page = Page(response.get_data(as_text=True))
    for tag, attributes in page.nodes:
        for attr in ("src", "href"):
            if tag in ("script", "img", "link") and attr in attributes:
                url = attributes[attr]
                assert url is not None
                assert not urlsplit(url).netloc
                assert url.startswith("/")
    assert page.element("link", rel="stylesheet")["href"] == "/static/styles.css"
    return page


def test_tc_014_025_usable_get_is_labeled_csrf_ready_and_non_consuming(setup) -> None:
    _app, clock, client, store, url, token, record = setup
    before = (record.consumed_at, store.accounts[record.owner_key].password_hash)
    for instant in (T0, T0 + timedelta(minutes=29, seconds=59, microseconds=999999)):
        clock.value = instant
        page = assert_token_page(client.get(url), token)
        form = page.element("form")
        assert form["method"] == "post"
        assert form["action"] == ""  # The current URL; no bearer token in HTML.
        csrf_field = page.element("input", name="csrf_token")
        assert csrf_field["type"] == "hidden" and csrf_field["value"]
        with client.session_transaction() as session:
            assert csrf_field["value"] == session["_csrf_token"]
        assert page.element("label", **{"for": "new-password"})
        password = page.element("input", id="new-password")
        assert (password["name"], password["type"]) == ("password", "password")
        assert password["autocomplete"] == "new-password"
        assert password.get("value", "") == ""
        assert page.element("button", type="submit")
        assert page.element("a", href="/forgot-password")
        assert record.consumed_at is None
        assert (record.consumed_at, store.accounts[record.owner_key].password_hash) == (
            before
        )
        assert store.owner_notice_sink == []

    # A valid GET does not authorize a later POST at the expiry boundary.
    # A previously valid GET cannot authorize a reset at expiry.
    clock.value = T0 + timedelta(minutes=30)
    response = client.post(
        url, data={"password": "new-password", "csrf_token": csrf_field["value"]}
    )
    assert response.status_code == 400
    assert b"Reset link unavailable" in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert token.encode() not in response.data
    assert record.consumed_at is None
    assert store.accounts[record.owner_key].password_hash == before[1]


@pytest.mark.parametrize("kind", ["unknown", "used", "exact_expiry", "after_expiry"])
def test_tc_025_unusable_links_are_recoverable_without_password_form(
    setup, kind: str
) -> None:
    _app, clock, client, store, url, token, record = setup
    if kind == "unknown":
        url, token = "/reset/unknown-opaque-token", "unknown-opaque-token"
    elif kind == "used":
        record.consumed_at = T0
    elif kind == "exact_expiry":
        clock.value = T0 + timedelta(minutes=30)
    else:
        clock.value = T0 + timedelta(minutes=30, microseconds=1)

    before = store.accounts[record.owner_key].password_hash
    for _ in range(2):
        page = assert_token_page(client.get(url), token)
        assert page.element("h1", id="unavailable-heading")["tabindex"] == "-1"
        assert page.element("p", role="alert")
        assert page.element("a", href="/forgot-password")
        assert not any(tag == "form" for tag, _attrs in page.nodes)
        assert not any(tag == "input" for tag, _attrs in page.nodes)
    assert store.accounts[record.owner_key].password_hash == before
    assert record.consumed_at == (T0 if kind == "used" else None)
    assert store.owner_notice_sink == []


@pytest.mark.parametrize("kind", ["unknown", "used", "exact_expiry", "after_expiry"])
def test_tc_025_unusable_get_and_post_protect_public_surface_and_state(
    setup, kind: str
) -> None:
    _app, clock, client, store, url, token, record = setup
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
    if kind == "unknown":
        url, token = "/reset/unknown-opaque-token", "unknown-opaque-token"
    elif kind == "used":
        assert (
            client.post(
                url,
                data={"csrf_token": csrf, "password": "test"},
            ).status_code
            == 303
        )
    elif kind == "exact_expiry":
        clock.value = record.expires_at
    else:
        clock.value = record.expires_at + timedelta(microseconds=1)

    before = {
        key: (account.password_hash, account.session_version)
        for key, account in store.accounts.items()
    }
    consumed = record.consumed_at
    notices = store.owner_notice_sink[:]
    for response in (
        client.get(url),
        client.post(
            url, data={"csrf_token": csrf, "password": "fake-later-replacement"}
        ),
    ):
        assert response.status_code == (
            200 if response.request.method == "GET" else 400
        )
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        surface = str(response.headers) + response.get_data(as_text=True)
        assert token not in surface
        assert "/reset-complete" not in surface
        assert "Password reset complete" not in surface
        page = Page(response.get_data(as_text=True))
        assert page.element("p", role="alert")
        assert page.element("a", href="/forgot-password")
        assert not any(tag in {"form", "input"} for tag, _ in page.nodes)
        assert page.element("link", rel="stylesheet")["href"] == "/static/styles.css"
        for tag, attributes in page.nodes:
            if tag in {"script", "img", "link"}:
                for attr in ("src", "href"):
                    if attributes.get(attr):
                        asset = attributes[attr]
                        assert asset is not None
                        assert asset.startswith("/") and not urlsplit(asset).netloc
    with client.session_transaction() as session:
        assert token not in str(dict(session))
    assert {
        key: (account.password_hash, account.session_version)
        for key, account in store.accounts.items()
    } == before
    assert record.consumed_at == consumed
    assert store.owner_notice_sink == notices


def test_tc_025_eligible_private_link_never_enters_public_request_or_confirmation(
    setup,
) -> None:
    _app, _clock, client, store, first_url, first_token, _record = setup
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
    response = client.post(
        "/forgot-password",
        data={"email": "owner@example.test", "csrf_token": csrf},
    )
    assert (response.status_code, response.headers["Location"]) == (
        303,
        "/reset-requested",
    )
    second_url = store.owner_link_outbox[-1].url
    assert second_url != first_url
    second_token = second_url.removeprefix("/reset/")
    confirmation = client.get("/reset-requested")
    assert confirmation.status_code == 200
    assert Page(confirmation.get_data(as_text=True)).element("p", role="status")
    for public in (response, confirmation, client.get("/")):
        surface = str(public.headers) + public.get_data(as_text=True)
        assert first_token not in surface
        assert second_token not in surface
        assert first_url not in surface
        assert second_url not in surface
        assert "owner@example.test" not in surface
    with client.session_transaction() as session:
        assert first_token not in str(dict(session))
        assert second_token not in str(dict(session))
    assert store.owner_notice_sink == []
    assert len(store.owner_link_outbox) == 2


def test_tc_025_token_path_is_redacted_in_ordinary_logs(setup, caplog) -> None:
    app, _clock, _client, _store, url, token, _record = setup
    with caplog.at_level(logging.INFO, logger="werkzeug"):
        logging.getLogger("werkzeug").info('"%s %s HTTP/1.1" 200 -', "GET", url)
    with caplog.at_level(logging.ERROR, logger=app.logger.name):
        app.logger.error("Exception on %s [GET]", url)
    assert token not in caplog.text
    assert caplog.text.count("/reset/[redacted]") == 2

"""TASK-007/008: one-use password commits and owner-session revocation."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from threading import Barrier

import pytest
from werkzeug.security import check_password_hash

from password_reset_demo import create_app
from password_reset_demo.state import OwnerNotice, ResetRecord, token_digest

T0 = datetime(2026, 1, 1, 12, tzinfo=UTC)
OWNER = "owner@example.test"
PEER = "peer@example.test"


class Clock:
    def __init__(self) -> None:
        self.value = T0

    def __call__(self) -> datetime:
        return self.value


class Page(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))

    def element(self, tag: str, **expected: str) -> dict[str, str | None]:
        for actual_tag, attrs in self.elements:
            if actual_tag == tag and all(
                attrs.get(k) == v for k, v in expected.items()
            ):
                return attrs
        raise AssertionError(f"Missing {tag} with {expected}")


@pytest.fixture
def reset_setup(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "commit-test-key")
    clock = Clock()
    app = create_app(clock=clock)
    requester = app.test_client()
    requester.get("/forgot-password")
    with requester.session_transaction() as session:
        csrf = session["_csrf_token"]
    assert (
        requester.post(
            "/forgot-password", data={"email": OWNER, "csrf_token": csrf}
        ).status_code
        == 303
    )
    store = app.extensions["reset_store"]
    url = store.owner_link_outbox[-1].url
    record = store.reset_records[token_digest(url.removeprefix("/reset/"))]
    return app, clock, store, url, record


def form_client(app, url):
    client = app.test_client()
    response = client.get(url)
    assert response.status_code == 200
    page = Page(response.get_data(as_text=True))
    csrf = page.element("input", name="csrf_token")["value"]
    assert isinstance(csrf, str)
    return client, csrf


def submit(client, url, csrf, password):
    return client.post(url, data={"csrf_token": csrf, "password": password})


def test_tc_007_valid_commit_changes_only_owner_hash_and_old_sign_in_fails(
    reset_setup,
) -> None:
    app, _clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    old_owner = store.accounts[OWNER].password_hash
    old_peer = store.accounts[PEER].password_hash
    response = submit(client, url, csrf, "  new password  ")
    assert (response.status_code, response.headers["Location"]) == (
        303,
        "/reset-complete",
    )
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert url.removeprefix("/reset/").encode() not in response.data
    complete = client.get("/reset-complete")
    page = Page(complete.get_data(as_text=True))
    assert page.element("h1", id="complete-heading")["tabindex"] == "-1"
    assert page.element("p", role="status")
    assert page.element("a", href="/")
    assert b"Password reset complete" in complete.data
    assert store.accounts[OWNER].password_hash != old_owner
    assert not check_password_hash(
        store.accounts[OWNER].password_hash, "demo-owner-password"
    )
    assert check_password_hash(store.accounts[OWNER].password_hash, "  new password  ")
    assert store.accounts[PEER].password_hash == old_peer
    assert record.consumed_at == T0
    assert store.accounts[OWNER].session_version == 1
    assert store.owner_notice_sink == [OwnerNotice(OWNER, T0)]

    for password, expected in (("demo-owner-password", 401), ("  new password  ", 303)):
        signed_in = app.test_client()
        signed_in.get("/")
        with signed_in.session_transaction() as session:
            sign_in_csrf = session["_csrf_token"]
        result = signed_in.post(
            "/sign-in",
            data={"csrf_token": sign_in_csrf, "email": OWNER, "password": password},
        )
        assert result.status_code == expected
        assert signed_in.get("/demo").status_code == (200 if expected == 303 else 303)


def test_tc_008_replay_get_and_post_cannot_change_hash(reset_setup) -> None:
    app, _clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    assert submit(client, url, csrf, "first-new-password").status_code == 303
    committed_hash = store.accounts[OWNER].password_hash
    consumed_at = record.consumed_at
    committed_notices = store.owner_notice_sink[:]
    assert committed_notices == [OwnerNotice(OWNER, T0)]
    page = Page(client.get(url).get_data(as_text=True))
    assert page.element("a", href="/forgot-password")
    assert not any(tag == "form" for tag, _ in page.elements)
    response = submit(client, url, csrf, "second-new-password")
    assert response.status_code == 400
    assert b"Reset link unavailable" in response.data
    assert b"Password reset complete" not in response.data
    assert (store.accounts[OWNER].password_hash, record.consumed_at) == (
        committed_hash,
        consumed_at,
    )
    assert check_password_hash(committed_hash, "first-new-password")
    assert not check_password_hash(committed_hash, "second-new-password")
    assert store.accounts[OWNER].session_version == 1
    assert store.owner_notice_sink == committed_notices


def test_tc_008_unknown_token_post_is_not_a_success(reset_setup) -> None:
    app, _clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    original = store.accounts[OWNER].password_hash
    response = submit(client, "/reset/unknown-opaque-token", csrf, "new-password")
    assert response.status_code == 400
    assert b"Reset link unavailable" in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert (store.accounts[OWNER].password_hash, record.consumed_at) == (original, None)


def test_tc_009_last_microsecond_before_expiry_commits(reset_setup) -> None:
    app, clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    clock.value = record.expires_at - timedelta(microseconds=1)
    assert submit(client, url, csrf, "boundary-password").status_code == 303
    assert record.consumed_at == clock.value
    assert store.accounts[OWNER].session_version == 1
    assert check_password_hash(store.accounts[OWNER].password_hash, "boundary-password")
    assert not check_password_hash(
        store.accounts[OWNER].password_hash, "demo-owner-password"
    )


@pytest.mark.parametrize("offset", [timedelta(0), timedelta(microseconds=1)])
def test_tc_010_expired_post_does_not_commit(reset_setup, offset) -> None:
    app, clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    original = store.accounts[OWNER].password_hash
    clock.value = record.expires_at + offset
    page = Page(client.get(url).get_data(as_text=True))
    assert page.element("a", href="/forgot-password")
    assert not any(tag == "form" for tag, _ in page.elements)
    response = submit(client, url, csrf, "boundary-password")
    assert response.status_code == 400
    assert b"Reset link unavailable" in response.data
    assert (store.accounts[OWNER].password_hash, record.consumed_at) == (original, None)
    assert store.accounts[OWNER].session_version == 0
    assert store.owner_notice_sink == []


def test_tc_010_valid_get_then_expired_post_rechecks_under_lock(reset_setup) -> None:
    app, clock, store, url, record = reset_setup
    clock.value = T0 + timedelta(minutes=29)
    client, csrf = form_client(app, url)
    original = store.accounts[OWNER].password_hash
    clock.value = record.expires_at
    response = submit(client, url, csrf, "too-late-password")
    assert response.status_code == 400
    assert b"Reset link unavailable" in response.data
    assert (store.accounts[OWNER].password_hash, record.consumed_at) == (original, None)


@pytest.mark.parametrize(
    ("password", "error"),
    [
        ("", "Enter a new password with a non-space character."),
        ("  \t", "Enter a new password with a non-space character."),
        ("x" * 1025, "Use a password of 1024 characters or fewer."),
    ],
)
def test_tc_020_password_feedback_preserves_link(reset_setup, password, error) -> None:
    app, _clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    original = store.accounts[OWNER].password_hash
    response = submit(client, url, csrf, password)
    assert response.status_code == 400
    page = Page(response.get_data(as_text=True))
    password_field = page.element("input", id="new-password")
    assert password_field["aria-invalid"] == "true"
    assert password_field["aria-describedby"] == "new-password-error"
    assert password_field["autofocus"] is None
    assert page.element("p", id="new-password-error")["role"] == "alert"
    assert error.encode() in response.data
    assert (store.accounts[OWNER].password_hash, record.consumed_at) == (original, None)
    assert store.accounts[OWNER].session_version == 0
    assert store.owner_notice_sink == []


def test_tc_020_csrf_rejection_and_1024_character_bound(reset_setup) -> None:
    app, _clock, store, url, record = reset_setup
    client, csrf = form_client(app, url)
    other, other_csrf = form_client(app, url)
    original = store.accounts[OWNER].password_hash
    for supplied in (None, "incorrect", other_csrf):
        data = {"password": "new-password"}
        if supplied is not None:
            data["csrf_token"] = supplied
        response = client.post(url, data=data)
        assert response.status_code == 400
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert (store.accounts[OWNER].password_hash, record.consumed_at) == (
            original,
            None,
        )
    assert csrf != other_csrf
    assert submit(other, url, other_csrf, "x" * 1024).status_code == 303
    assert check_password_hash(store.accounts[OWNER].password_hash, "x" * 1024)
    assert store.owner_notice_sink == [OwnerNotice(OWNER, T0)]


def test_tc_022_concurrent_redemption_has_exactly_one_winner(reset_setup) -> None:
    app, clock, store, url, record = reset_setup
    clock.value = T0 + timedelta(minutes=1)
    first, first_csrf = form_client(app, url)
    second, second_csrf = form_client(app, url)
    barrier = Barrier(3)

    def redeem(client, csrf, password):
        barrier.wait()
        return submit(client, url, csrf, password)

    with ThreadPoolExecutor(max_workers=2) as executor:
        one = executor.submit(redeem, first, first_csrf, "first-password")
        two = executor.submit(redeem, second, second_csrf, "second-password")
        barrier.wait()
        responses = [one.result(), two.result()]
    assert sorted(response.status_code for response in responses) == [303, 400]
    assert (
        sum(
            response.headers.get("Location") == "/reset-complete"
            for response in responses
        )
        == 1
    )
    assert record.consumed_at == clock.value
    final_hash = store.accounts[OWNER].password_hash
    for response, password in zip(
        responses, ("first-password", "second-password"), strict=True
    ):
        assert check_password_hash(final_hash, password) == (
            response.status_code == 303
        )
    assert store.accounts[OWNER].session_version == 1
    assert store.owner_notice_sink == [OwnerNotice(OWNER, clock.value)]


def test_in_process_mutation_failure_restores_hash_and_token(
    reset_setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, _clock, store, url, record = reset_setup
    app.testing = False  # Flask renders an error response rather than propagating it.
    client, csrf = form_client(app, url)
    original = store.accounts[OWNER].password_hash
    original_setattr = ResetRecord.__setattr__
    failed = False

    def fail_after_consumption(self, name, value):
        nonlocal failed
        original_setattr(self, name, value)
        if self is record and name == "consumed_at" and not failed:
            failed = True
            raise RuntimeError("simulated in-process failure")

    monkeypatch.setattr(ResetRecord, "__setattr__", fail_after_consumption)
    response = submit(client, url, csrf, "new-password")
    assert response.status_code == 500
    assert failed
    assert (store.accounts[OWNER].password_hash, record.consumed_at) == (original, None)
    assert store.accounts[OWNER].session_version == 0
    assert store.owner_notice_sink == []
    assert submit(client, url, csrf, "new-password").status_code == 303
    assert check_password_hash(store.accounts[OWNER].password_hash, "new-password")
    assert store.accounts[OWNER].session_version == 1
    assert store.owner_notice_sink == [OwnerNotice(OWNER, T0)]

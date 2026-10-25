"""TC-011: reset commits revoke only the owner's previously signed sessions."""

from datetime import UTC, datetime, timedelta

import pytest
from werkzeug.security import check_password_hash

from password_reset_demo import create_app
from password_reset_demo.state import Account, OwnerNotice, token_digest

OWNER = "owner@example.test"
PEER = "peer@example.test"


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 1, 1, 12, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.value


@pytest.fixture
def app_clock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "session-revocation-test-key")
    clock = Clock()
    return create_app(clock=clock), clock


def csrf_for(client, path: str) -> str:
    assert client.get(path).status_code == 200
    with client.session_transaction() as session:
        return session["_csrf_token"]


def sign_in(client, email: str, password: str) -> None:
    csrf = csrf_for(client, "/")
    response = client.post(
        "/sign-in",
        data={"csrf_token": csrf, "email": email, "password": password},
    )
    assert (response.status_code, response.headers["Location"]) == (303, "/demo")
    assert client.get("/demo").status_code == 200


def issue_link(app) -> str:
    requester = app.test_client()
    csrf = csrf_for(requester, "/forgot-password")
    assert (
        requester.post(
            "/forgot-password", data={"email": OWNER, "csrf_token": csrf}
        ).status_code
        == 303
    )
    return app.extensions["reset_store"].owner_link_outbox[-1].url


def submit(client, url: str, csrf: str, password: str):
    return client.post(url, data={"csrf_token": csrf, "password": password})


def assert_cleared_on_next_access(client) -> None:
    response = client.get("/demo")
    assert (response.status_code, response.headers["Location"]) == (303, "/")
    assert client.get_cookie("session") is None
    with client.session_transaction() as session:
        assert "account_id" not in session
        assert "session_version" not in session


def test_tc_011_success_revokes_independent_owner_clients_and_copied_cookie(
    app_clock,
) -> None:
    app, _clock = app_clock
    store = app.extensions["reset_store"]
    owner1, owner2, resetter, peer = (app.test_client() for _ in range(4))
    for client in (owner1, owner2, resetter):
        sign_in(client, OWNER, "demo-owner-password")
    sign_in(peer, PEER, "demo-peer-password")
    signed_cookie = owner1.get_cookie("session")
    assert signed_cookie is not None
    original_hash = store.accounts[OWNER].password_hash
    peer_hash = store.accounts[PEER].password_hash

    url = issue_link(app)
    csrf = csrf_for(resetter, url)
    response = submit(resetter, url, csrf, "new-owner-password")
    assert (response.status_code, response.headers["Location"]) == (
        303,
        "/reset-complete",
    )
    assert store.accounts[OWNER].session_version == 1
    assert store.accounts[PEER].session_version == 0
    assert store.accounts[OWNER].password_hash != original_hash
    assert check_password_hash(
        store.accounts[OWNER].password_hash, "new-owner-password"
    )
    assert store.accounts[PEER].password_hash == peer_hash
    assert store.reset_records[token_digest(url.removeprefix("/reset/"))].consumed_at
    assert store.owner_notice_sink == [OwnerNotice(OWNER, store.now())]

    copied = app.test_client()
    copied.set_cookie(
        "session",
        signed_cookie.value,
        domain=signed_cookie.domain,
        path=signed_cookie.path,
    )
    assert copied.get_cookie("session").value == signed_cookie.value
    for client in (owner1, owner2, resetter, copied):
        assert_cleared_on_next_access(client)
    assert peer.get("/demo").status_code == 200
    with peer.session_transaction() as session:
        assert session["account_id"] == PEER
        assert session["session_version"] == 0


def test_tc_011_invalid_expired_and_replayed_resets_leave_new_session_intact(
    app_clock,
) -> None:
    app, clock = app_clock
    store = app.extensions["reset_store"]
    url = issue_link(app)
    resetter = app.test_client()
    csrf = csrf_for(resetter, url)
    assert submit(resetter, url, csrf, "new-owner-password").status_code == 303

    current = app.test_client()
    sign_in(current, OWNER, "new-owner-password")
    next_url = issue_link(app)
    next_csrf = csrf_for(resetter, next_url)
    next_record = store.reset_records[token_digest(next_url.removeprefix("/reset/"))]
    original_hash = store.accounts[OWNER].password_hash
    committed_notices = store.owner_notice_sink[:]
    assert committed_notices == [OwnerNotice(OWNER, clock.value)]

    def assert_no_revocation(response) -> None:
        assert response.status_code == 400
        assert store.accounts[OWNER].session_version == 1
        assert store.owner_notice_sink == committed_notices
        assert current.get("/demo").status_code == 200

    assert_no_revocation(submit(resetter, url, csrf, "replayed-password"))
    assert_no_revocation(
        resetter.post(
            next_url,
            data={"csrf_token": "invalid", "password": "test"},
        )
    )
    assert_no_revocation(submit(resetter, next_url, next_csrf, "   "))
    assert_no_revocation(
        submit(resetter, "/reset/unknown-token", next_csrf, "unknown-password")
    )
    clock.value = next_record.expires_at
    assert_no_revocation(submit(resetter, next_url, next_csrf, "expired-password"))
    assert next_record.consumed_at is None
    assert store.accounts[OWNER].password_hash == original_hash
    assert store.accounts[OWNER].session_version == 1
    assert store.accounts[PEER].session_version == 0


def test_version_mutation_failure_rolls_back_hash_token_and_revocation(
    app_clock, monkeypatch: pytest.MonkeyPatch
) -> None:
    app, clock = app_clock
    app.testing = False  # Return HTTP 500 for the injected in-process error.
    store = app.extensions["reset_store"]
    owner1, owner2, peer = (app.test_client() for _ in range(3))
    for client in (owner1, owner2):
        sign_in(client, OWNER, "demo-owner-password")
    sign_in(peer, PEER, "demo-peer-password")
    url = issue_link(app)
    resetter = app.test_client()
    csrf = csrf_for(resetter, url)
    record = store.reset_records[token_digest(url.removeprefix("/reset/"))]
    account = store.accounts[OWNER]
    original_hash = account.password_hash
    original_setattr = Account.__setattr__
    failed = False

    def fail_after_version_change(self, name, value):
        nonlocal failed
        original_setattr(self, name, value)
        if self is account and name == "session_version" and not failed:
            failed = True
            raise RuntimeError("simulated in-process version failure")

    monkeypatch.setattr(Account, "__setattr__", fail_after_version_change)
    assert submit(resetter, url, csrf, "new-owner-password").status_code == 500
    assert failed
    assert account.password_hash == original_hash
    assert account.session_version == 0
    assert record.consumed_at is None
    assert store.owner_notice_sink == []
    for client in (owner1, owner2, peer):
        assert client.get("/demo").status_code == 200

    clock.value += timedelta(minutes=1)
    assert submit(resetter, url, csrf, "new-owner-password").status_code == 303
    assert account.session_version == 1
    assert record.consumed_at == clock.value
    assert store.owner_notice_sink == [OwnerNotice(OWNER, clock.value)]
    for client in (owner1, owner2):
        assert_cleared_on_next_access(client)
    assert peer.get("/demo").status_code == 200

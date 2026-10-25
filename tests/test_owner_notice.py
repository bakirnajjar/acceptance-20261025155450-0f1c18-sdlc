"""TASK-009: one process-local owner notice per committed reset."""

import logging
from datetime import UTC, datetime, timedelta

import pytest
from werkzeug.security import check_password_hash

from password_reset_demo import create_app
from password_reset_demo.state import OwnerNotice, token_digest

OWNER = "owner@example.test"
PEER = "peer@example.test"
T0 = datetime(2026, 1, 1, 12, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.value = T0

    def __call__(self) -> datetime:
        return self.value


@pytest.fixture
def app_clock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "fake-local-notice-key")
    clock = Clock()
    return create_app(clock=clock), clock


def csrf_for(client, path: str) -> str:
    assert client.get(path).status_code == 200
    with client.session_transaction() as session:
        return session["_csrf_token"]


def issue_link(app) -> str:
    requester = app.test_client()
    csrf = csrf_for(requester, "/forgot-password")
    response = requester.post(
        "/forgot-password", data={"email": OWNER, "csrf_token": csrf}
    )
    assert (response.status_code, response.headers["Location"]) == (
        303,
        "/reset-requested",
    )
    return app.extensions["reset_store"].owner_link_outbox[-1].url


def sign_in(client, email: str, password: str) -> None:
    csrf = csrf_for(client, "/")
    response = client.post(
        "/sign-in",
        data={"csrf_token": csrf, "email": email, "password": password},
    )
    assert (response.status_code, response.headers["Location"]) == (303, "/demo")
    assert client.get("/demo").status_code == 200


def submit(client, url: str, csrf: str, password: str):
    return client.post(url, data={"csrf_token": csrf, "password": password})


def test_tc_012_tc_013_two_fresh_successes_append_one_owner_notice_each(
    app_clock,
) -> None:
    app, clock = app_clock
    store = app.extensions["reset_store"]
    peer_hash = store.accounts[PEER].password_hash
    resetter = app.test_client()
    assert store.owner_notice_sink == []
    assert store.owner_link_outbox == []

    first_url = issue_link(app)
    first_csrf = csrf_for(resetter, first_url)
    assert (
        submit(resetter, first_url, first_csrf, "fake-new-password-one").status_code
        == 303
    )
    first_hash = store.accounts[OWNER].password_hash
    assert check_password_hash(first_hash, "fake-new-password-one")
    assert store.owner_notice_sink == [OwnerNotice(OWNER, T0)]
    assert store.owner_notice_sink is not store.owner_link_outbox
    assert len(store.owner_link_outbox) == 1

    clock.value += timedelta(minutes=1)
    second_url = issue_link(app)
    assert second_url != first_url
    second_csrf = csrf_for(resetter, second_url)
    assert (
        submit(resetter, second_url, second_csrf, "fake-new-password-two").status_code
        == 303
    )
    assert store.accounts[OWNER].password_hash != first_hash
    assert check_password_hash(
        store.accounts[OWNER].password_hash, "fake-new-password-two"
    )
    assert store.owner_notice_sink == [
        OwnerNotice(OWNER, T0),
        OwnerNotice(OWNER, clock.value),
    ]
    assert len(store.owner_link_outbox) == 2
    assert store.accounts[OWNER].session_version == 2
    assert store.accounts[PEER].password_hash == peer_hash
    assert store.accounts[PEER].session_version == 0

    for url, csrf in ((first_url, first_csrf), (second_url, second_csrf)):
        assert submit(resetter, url, csrf, "fake-replay-password").status_code == 400
    assert store.owner_notice_sink == [
        OwnerNotice(OWNER, T0),
        OwnerNotice(OWNER, clock.value),
    ]
    assert not check_password_hash(
        store.accounts[OWNER].password_hash, "fake-replay-password"
    )


class FailingSink(list[OwnerNotice]):
    def __init__(self, notices: list[OwnerNotice], *, append_first: bool) -> None:
        super().__init__(notices)
        self.append_first = append_first

    def append(self, notice: OwnerNotice) -> None:
        if self.append_first:
            super().append(notice)
        raise RuntimeError("fake in-process sink failure")


@pytest.mark.parametrize(
    ("append_first", "prior_success"),
    [(False, False), (True, True)],
)
def test_tc_023_sink_failure_rolls_back_all_effects_and_keeps_sessions(
    app_clock, append_first: bool, prior_success: bool, caplog
) -> None:
    app, clock = app_clock
    app.testing = False  # Injected in-process error returns an HTTP 500.
    store = app.extensions["reset_store"]
    resetter = app.test_client()
    password = "demo-owner-password"
    if prior_success:
        prior_url = issue_link(app)
        prior_csrf = csrf_for(resetter, prior_url)
        assert (
            submit(resetter, prior_url, prior_csrf, "fake-prior-password").status_code
            == 303
        )
        password = "fake-prior-password"
        clock.value += timedelta(minutes=1)

    first, second, peer = (app.test_client() for _ in range(3))
    for client in (first, second):
        sign_in(client, OWNER, password)
    sign_in(peer, PEER, "demo-peer-password")
    url = issue_link(app)
    csrf = csrf_for(resetter, url)
    record = store.reset_records[token_digest(url.removeprefix("/reset/"))]
    owner_hash = store.accounts[OWNER].password_hash
    owner_version = store.accounts[OWNER].session_version
    peer_hash = store.accounts[PEER].password_hash
    peer_version = store.accounts[PEER].session_version
    notices = store.owner_notice_sink[:]
    sink = FailingSink(notices, append_first=append_first)
    store.owner_notice_sink = sink

    with caplog.at_level(logging.ERROR, logger=app.logger.name):
        response = submit(resetter, url, csrf, "fake-retry-password")
    assert response.status_code == 500
    assert response.headers.get("Location") != "/reset-complete"
    # TC-025: Inspect a real Flask exception record, not just a fabricated log line.
    assert url.removeprefix("/reset/") not in caplog.text
    assert "/reset/[redacted]" in caplog.text
    assert store.accounts[OWNER].password_hash == owner_hash
    assert record.consumed_at is None
    assert store.accounts[OWNER].session_version == owner_version
    assert (
        store.accounts[PEER].password_hash,
        store.accounts[PEER].session_version,
    ) == (
        peer_hash,
        peer_version,
    )
    assert store.owner_notice_sink is sink
    assert sink == notices  # Even append-then-throw leaves no orphan notice.
    for client in (first, second, peer):
        assert client.get("/demo").status_code == 200

    store.owner_notice_sink = list(notices)
    assert submit(resetter, url, csrf, "fake-retry-password").status_code == 303
    assert check_password_hash(
        store.accounts[OWNER].password_hash, "fake-retry-password"
    )
    assert record.consumed_at == clock.value
    assert store.accounts[OWNER].session_version == owner_version + 1
    assert store.owner_notice_sink == [*notices, OwnerNotice(OWNER, clock.value)]
    for client in (first, second):
        assert client.get("/demo").status_code == 303
    assert peer.get("/demo").status_code == 200

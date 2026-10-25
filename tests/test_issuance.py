"""TASK-005: locked rolling-window accounting and private link issuance."""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest

from password_reset_demo import create_app
from password_reset_demo.state import token_digest

T0 = datetime(2026, 1, 1, 12, tzinfo=UTC)
OWNER = "owner@example.test"
ABSENT = "absent@example.test"


class FakeClock:
    def __init__(self) -> None:
        self.value = T0

    def __call__(self) -> datetime:
        return self.value


@pytest.fixture
def setup(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "issuance-test-key")
    clock = FakeClock()
    return create_app(clock=clock), clock


def ready_client(app):
    client = app.test_client()
    assert client.get("/forgot-password").status_code == 200
    with client.session_transaction() as session:
        csrf = session["_csrf_token"]
    return client, csrf


def request_link(client, csrf: str, address: str):
    return client.post("/forgot-password", data={"email": address, "csrf_token": csrf})


def public_surface(client, response):
    assert response.status_code == 303
    assert response.headers["Location"] == "/reset-requested"
    destination = client.get(response.headers["Location"])
    assert destination.status_code == 200
    return (
        response.status_code,
        tuple(response.headers.items()),
        response.data,
        destination.status_code,
        tuple(destination.headers.items()),
        destination.data,
    )


def assert_private_link(store, link, issued_at: datetime) -> str:
    assert link.owner_key == OWNER
    assert re.fullmatch(r"/reset/[A-Za-z0-9_-]{43}", link.url)
    token = link.url.removeprefix("/reset/")
    digest = token_digest(token)
    assert token not in store.reset_records
    record = store.reset_records[digest]
    assert record.owner_key == OWNER
    assert record.issued_at == issued_at
    assert record.expires_at == issued_at + timedelta(minutes=30)
    assert record.consumed_at is None
    assert token not in repr(record)
    return token


def test_tc_005_006_first_fifth_sixth_and_exact_hour_boundary(setup) -> None:
    app, clock = setup
    store = app.extensions["reset_store"]
    client, csrf = ready_client(app)
    surfaces = []
    for index in range(5):
        address = " OWNER@Example.Test " if index % 2 == 0 else OWNER
        response = request_link(client, csrf, address)
        surfaces.append(public_surface(client, response))
        assert len(store.owner_link_outbox) == index + 1
        assert len(store.reset_records) == index + 1

    assert store.request_times == {OWNER: [T0] * 5}
    tokens = [assert_private_link(store, link, T0) for link in store.owner_link_outbox]
    assert len(set(tokens)) == 5
    assert len(store.owner_notice_sink) == 0
    for instant in (
        T0 + timedelta(seconds=3599),
        T0 + timedelta(hours=1, microseconds=-1),
    ):
        clock.value = instant
        surfaces.append(public_surface(client, request_link(client, csrf, OWNER)))
        assert len(store.owner_link_outbox) == len(store.reset_records) == 5
        assert store.request_times[OWNER] == [T0] * 5

    clock.value = T0 + timedelta(seconds=3600)
    surfaces.append(
        public_surface(client, request_link(client, csrf, " Owner@EXAMPLE.TEST "))
    )
    assert store.request_times == {OWNER: [clock.value]}
    assert len(store.owner_link_outbox) == len(store.reset_records) == 6
    boundary_token = assert_private_link(
        store, store.owner_link_outbox[-1], clock.value
    )
    assert boundary_token not in tokens
    assert all(surface == surfaces[0] for surface in surfaces)
    for token in (*tokens, boundary_token):
        assert all(
            token.encode() not in part
            for surface in surfaces
            for part in (
                str(surface[1]).encode(),
                surface[2],
                str(surface[4]).encode(),
                surface[5],
            )
        )


@pytest.mark.parametrize("initial_count", [0, 4, 5])
@pytest.mark.parametrize("owner_first", [True, False])
def test_tc_004_019_matched_owner_absent_parity_and_private_counts(
    setup, initial_count: int, owner_first: bool
) -> None:
    first_app, clock = setup
    second_app = create_app(clock=clock)
    pairs = [(OWNER, first_app), (ABSENT, second_app)]
    if not owner_first:
        pairs.reverse()

    surfaces = {}
    for key, app in pairs:
        store = app.extensions["reset_store"]
        store.request_times[key] = [T0] * initial_count
        client, csrf = ready_client(app)
        clock.value = T0 + (
            timedelta(seconds=3599) if initial_count == 5 else timedelta(0)
        )
        address = f" {key.split('@')[0].upper()}@Example.Test "
        response = request_link(client, csrf, address)
        surfaces[key] = public_surface(client, response)
        assert store.request_times == {
            key: [T0] * initial_count + ([] if initial_count == 5 else [clock.value])
        }
        assert len(store.owner_link_outbox) == (key == OWNER and initial_count < 5)
        assert len(store.reset_records) == len(store.owner_link_outbox)
        if store.owner_link_outbox:
            assert_private_link(store, store.owner_link_outbox[0], clock.value)
        assert store.owner_notice_sink == []

    assert surfaces[OWNER] == surfaces[ABSENT]
    assert OWNER.encode() not in surfaces[OWNER][2]
    assert ABSENT.encode() not in surfaces[ABSENT][2]


def test_absent_key_has_same_fifth_sixth_and_hour_boundary_accounting(setup) -> None:
    app, clock = setup
    store = app.extensions["reset_store"]
    client, csrf = ready_client(app)
    surfaces = []
    for _ in range(5):
        surfaces.append(public_surface(client, request_link(client, csrf, ABSENT)))
    assert store.request_times == {ABSENT: [T0] * 5}
    clock.value = T0 + timedelta(seconds=3599)
    surfaces.append(
        public_surface(client, request_link(client, csrf, " ABSENT@Example.Test "))
    )
    assert store.request_times[ABSENT] == [T0] * 5
    clock.value = T0 + timedelta(seconds=3600)
    surfaces.append(public_surface(client, request_link(client, csrf, ABSENT)))
    assert store.request_times == {ABSENT: [clock.value]}
    assert store.owner_link_outbox == []
    assert store.reset_records == {}
    assert all(surface == surfaces[0] for surface in surfaces)


def test_tc_021_two_simultaneous_clients_compete_for_fifth_slot(setup) -> None:
    app, clock = setup
    store = app.extensions["reset_store"]
    initial_client, initial_csrf = ready_client(app)
    for _ in range(4):
        assert request_link(initial_client, initial_csrf, OWNER).status_code == 303
    assert len(store.owner_link_outbox) == len(store.reset_records) == 4
    first_four = {link.url for link in store.owner_link_outbox}
    clock.value = T0 + timedelta(seconds=1)
    clients = [ready_client(app), ready_client(app)]
    barrier = Barrier(2)

    def submit(client_and_csrf, address):
        client, csrf = client_and_csrf
        barrier.wait(timeout=10)
        return public_surface(client, request_link(client, csrf, address))

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(submit, clients[0], OWNER)
        second = executor.submit(submit, clients[1], " OWNER@Example.Test ")
        surfaces = [first.result(timeout=10), second.result(timeout=10)]

    assert surfaces[0] == surfaces[1]
    assert store.request_times == {OWNER: [T0] * 4 + [clock.value]}
    assert len(store.owner_link_outbox) == len(store.reset_records) == 5
    assert len(first_four | {link.url for link in store.owner_link_outbox}) == 5
    assert_private_link(store, store.owner_link_outbox[-1], clock.value)
    assert store.owner_notice_sink == []

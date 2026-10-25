"""TASK-003: signed synthetic sign-in and version-guard prerequisites for TC-011."""

import pytest

from password_reset_demo import create_app
from password_reset_demo.state import normalize_email


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "sign-in-test-key")
    return create_app()


def sign_in(client, email: str, password: str, *, csrf_token: str | None = None):
    if csrf_token is None:
        client.get("/")
        with client.session_transaction() as session:
            csrf_token = session["_csrf_token"]
    return client.post(
        "/sign-in",
        data={"email": email, "password": password, "csrf_token": csrf_token},
    )


def test_tc_011_two_owner_clients_revoked_by_version_not_unrelated_account(app) -> None:
    owner_a, owner_b, peer = (app.test_client() for _ in range(3))
    owner_key = normalize_email("owner@example.test")
    peer_key = normalize_email("peer@example.test")
    store = app.extensions["reset_store"]

    for client in (owner_a, owner_b):
        response = sign_in(client, " OWNER@EXAMPLE.TEST ", "demo-owner-password")
        assert response.status_code == 303
        assert response.headers["Location"] == "/demo"
        with client.session_transaction() as session:
            assert session["account_id"] == owner_key
            assert session["session_version"] == 0
    assert sign_in(peer, "peer@example.test", "demo-peer-password").status_code == 303
    with peer.session_transaction() as session:
        assert session["account_id"] == peer_key

    for client in (owner_a, owner_b, peer):
        response = client.get("/demo")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
    with store.lock:
        store.accounts[owner_key].session_version += 1

    for client in (owner_a, owner_b):
        response = client.get("/demo")
        assert response.status_code == 303
        assert response.headers["Location"] == "/"
        with client.session_transaction() as session:
            assert "account_id" not in session
            assert "session_version" not in session
        assert client.get("/demo").headers["Location"] == "/"

    response = peer.get("/demo")
    assert response.status_code == 200
    assert b"peer@example.test" in response.data
    with peer.session_transaction() as session:
        assert session["account_id"] == peer_key
        assert session["session_version"] == 0
    assert store.accounts[peer_key].session_version == 0


@pytest.mark.parametrize(
    ("account_id", "version"),
    [
        ("owner@example.test", 999),
        ("owner@example.test", "0"),
        ("owner@example.test", True),
        ("missing@example.test", 0),
    ],
)
def test_signed_stale_or_invalid_identity_cannot_bypass_guard(
    app, account_id: str, version: int | str | bool
) -> None:
    client = app.test_client()
    with client.session_transaction() as session:
        session["account_id"] = account_id
        session["session_version"] = version
    response = client.get("/demo")
    assert response.status_code == 303
    assert response.headers["Location"] == "/"
    with client.session_transaction() as session:
        assert "account_id" not in session
        assert "session_version" not in session


def test_invalid_credentials_and_input_do_not_authenticate(app) -> None:
    client = app.test_client()
    assert client.get("/demo").headers["Location"] == "/"
    for email, password, expected_status, message in (
        ("owner@example.test", "wrong", 401, b"Invalid email address or password."),
        ("unknown@example.test", "demo-owner-password", 401, b"Invalid email"),
        (" ", "demo-owner-password", 400, b"Enter an email address."),
        ("owner@example.test", "", 400, b"Enter a password."),
    ):
        response = sign_in(client, email, password)
        assert response.status_code == expected_status
        assert message in response.data
        assert client.get("/demo").headers["Location"] == "/"
        with client.session_transaction() as session:
            assert "account_id" not in session
            assert "session_version" not in session

    assert (
        sign_in(client, "owner@example.test", "demo-owner-password").status_code == 303
    )
    assert client.get("/demo").status_code == 200
    assert sign_in(client, "owner@example.test", "wrong").status_code == 401
    assert client.get("/demo").headers["Location"] == "/"


def test_csrf_is_required_and_bound_to_issuing_client(app) -> None:
    first = app.test_client()
    second = app.test_client()
    first.get("/")
    second.get("/")
    with first.session_transaction() as session:
        token = session["_csrf_token"]
    with second.session_transaction() as session:
        assert session["_csrf_token"] != token

    for client, supplied in (
        (first, None),
        (first, "incorrect"),
        (second, token),
    ):
        response = client.post(
            "/sign-in",
            data={
                "email": "owner@example.test",
                "password": "demo-owner-password",
                **({"csrf_token": supplied} if supplied is not None else {}),
            },
        )
        assert response.status_code == 400
        assert client.get("/demo").headers["Location"] == "/"
        with client.session_transaction() as session:
            assert "account_id" not in session

"""Focused TASK-001 foundations for TC-014/015 (routes come in later tasks)."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from flask import render_template_string, session
from werkzeug.security import check_password_hash

from password_reset_demo import create_app
from password_reset_demo.csrf import csrf_token, valid_csrf_token
from password_reset_demo.state import (
    OwnerLink,
    OwnerNotice,
    ResetRecord,
    normalize_email,
    token_digest,
)


class FakeClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PASSWORD_RESET_SESSION_SECRET", "test-only-signing-key")


def test_tc_014_factory_uses_flask_jinja_and_aware_injectable_utc_clock(
    signing_key: None,
) -> None:
    t0 = datetime(2026, 1, 1, 12, tzinfo=UTC)
    first_clock = FakeClock(t0)
    second_clock = FakeClock(t0)
    first_app = create_app(clock=first_clock)
    second_app = create_app(clock=second_clock)
    first_store = first_app.extensions["reset_store"]
    second_store = second_app.extensions["reset_store"]

    assert first_store.now() == second_store.now() == t0
    first_clock.value += timedelta(minutes=30)
    assert first_store.now() == t0 + timedelta(minutes=30)
    assert second_store.now() == t0
    with first_app.app_context():
        assert "<main>" in render_template_string("{% extends 'base.html' %}")

    for invalid in (
        datetime(2026, 1, 1, 12),
        datetime(2026, 1, 1, 12, tzinfo=timezone(timedelta(hours=1))),
    ):
        first_clock.value = invalid
        with pytest.raises(ValueError, match="aware UTC"):
            first_store.now()


def test_tc_015_synthetic_hashes_and_all_store_members_are_per_app(
    signing_key: None,
) -> None:
    first = create_app().extensions["reset_store"]
    second = create_app().extensions["reset_store"]
    a_key = normalize_email("  OWNER@Example.Test ")
    b_key = normalize_email("Peer@EXAMPLE.TEST")
    assert set(first.accounts) == set(second.accounts) == {a_key, b_key}

    for store in (first, second):
        assert check_password_hash(
            store.accounts[a_key].password_hash, "demo-owner-password"
        )
        assert check_password_hash(
            store.accounts[b_key].password_hash, "demo-peer-password"
        )
        assert "demo-owner-password" not in store.accounts[a_key].password_hash
        assert "demo-peer-password" not in store.accounts[b_key].password_hash
        assert store.accounts[a_key].session_version == 0
        assert store.owner_link_outbox is not store.owner_notice_sink
    assert first.accounts[a_key] is not second.accounts[a_key]
    assert first.lock is not second.lock

    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    raw = "only-a-test-token"
    digest = token_digest(raw)
    assert len(digest) == 64 and digest != raw
    with first.lock:
        first.accounts[a_key].session_version += 1
        first.request_times[a_key] = [t0]
        first.reset_records[digest] = ResetRecord(
            owner_key=a_key, issued_at=t0, expires_at=t0 + timedelta(minutes=30)
        )
        first.owner_link_outbox.append(OwnerLink(a_key, f"/reset/{raw}"))
        first.owner_notice_sink.append(OwnerNotice(a_key, t0))

    assert raw not in first.reset_records
    assert first.reset_records[digest].owner_key == a_key
    assert second.accounts[a_key].session_version == 0
    assert second.request_times == {}
    assert second.reset_records == {}
    assert second.owner_link_outbox == []
    assert second.owner_notice_sink == []
    assert first.accounts[b_key].session_version == 0


def test_csrf_is_signed_client_state_independent_of_account(signing_key: None) -> None:
    app = create_app()
    other_app = create_app()
    assert app.session_interface.get_signing_serializer(app) is not None
    with app.test_request_context("/"):
        token = csrf_token()
        assert render_template_string("{{ csrf_token() }}") == token
        assert valid_csrf_token(token)
        session["account_id"] = "owner@example.test"
        assert csrf_token() == token
        assert valid_csrf_token(token)
        assert not valid_csrf_token(None)
        assert not valid_csrf_token("other")
        session_data = dict(session)
    with other_app.test_request_context("/"):
        session.update(session_data)
        assert not valid_csrf_token(token)
        assert csrf_token() != token
    with app.test_request_context("/"):
        assert not valid_csrf_token(token)
        assert csrf_token() != token


def test_factory_requires_environment_signing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PASSWORD_RESET_SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="PASSWORD_RESET_SESSION_SECRET"):
        create_app()

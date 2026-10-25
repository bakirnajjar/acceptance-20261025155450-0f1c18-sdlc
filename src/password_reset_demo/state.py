"""Process-local synthetic state and locked password-reset transition."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import RLock

from werkzeug.security import generate_password_hash

Clock = Callable[[], datetime]


def normalize_email(address: str) -> str:
    """Use the same account-independent key for fixtures and future requests."""
    return address.strip().casefold()


def token_digest(token: str) -> str:
    """Index a future bearer token without keeping its raw value in reset records."""
    return sha256(token.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class Account:
    email: str
    password_hash: str
    session_version: int = 0


@dataclass(slots=True)
class ResetRecord:
    owner_key: str
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None


@dataclass(slots=True)
class OwnerLink:
    owner_key: str
    url: str


@dataclass(slots=True)
class OwnerNotice:
    owner_key: str
    recorded_at: datetime


@dataclass(slots=True)
class ResetStore:
    """Each app owns its own lock and all mutable account/recovery state."""

    clock: Clock = field(default=lambda: datetime.now(UTC), repr=False)
    lock: RLock = field(default_factory=RLock, repr=False)
    accounts: dict[str, Account] = field(default_factory=dict)
    request_times: dict[str, list[datetime]] = field(default_factory=dict)
    reset_records: dict[str, ResetRecord] = field(default_factory=dict)
    owner_link_outbox: list[OwnerLink] = field(default_factory=list)
    owner_notice_sink: list[OwnerNotice] = field(default_factory=list)

    def now(self) -> datetime:
        """Require an aware UTC clock, including when it is injected in a test."""
        value = self.clock()
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("clock must return an aware UTC datetime")
        return value

    def commit_password_reset(self, digest: str, new_hash: str) -> bool:
        """Atomically change the password, consume the link, revoke and notify.

        The process-local lock includes the final clock check and all mutations.
        On an in-process failure, restore even a partially appended notice.
        """
        with self.lock:
            record = self.reset_records.get(digest)
            if record is None or record.consumed_at is not None:
                return False
            account = self.accounts.get(record.owner_key)
            if account is None:
                return False
            now = self.now()
            if now >= record.expires_at:
                return False

            previous_hash = account.password_hash
            previous_consumed_at = record.consumed_at
            previous_version = account.session_version
            previous_notices = self.owner_notice_sink[:]
            try:
                account.password_hash = new_hash
                record.consumed_at = now
                account.session_version = previous_version + 1
                self.owner_notice_sink.append(OwnerNotice(record.owner_key, now))
            except Exception:
                account.password_hash = previous_hash
                record.consumed_at = previous_consumed_at
                account.session_version = previous_version
                self.owner_notice_sink[:] = previous_notices
                raise
            return True


def create_store(clock: Clock | None = None) -> ResetStore:
    """Seed only synthetic A/B accounts, storing hashes rather than passwords."""
    store = ResetStore(clock=clock or (lambda: datetime.now(UTC)))
    store.now()
    for address, synthetic_password in (
        ("owner@example.test", "demo-owner-password"),
        ("peer@example.test", "demo-peer-password"),
    ):
        key = normalize_email(address)
        store.accounts[key] = Account(
            email=address,
            password_hash=generate_password_hash(synthetic_password),
        )
    return store

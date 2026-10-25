"""Private reset-request issuance; the public handler never reports its outcome."""

import re
import secrets
from datetime import timedelta

from password_reset_demo.state import (
    OwnerLink,
    ResetRecord,
    ResetStore,
    normalize_email,
    token_digest,
)

_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_ADDRESS = re.compile(rf"{_ATOM}(?:\.{_ATOM})*@{_LABEL}(?:\.{_LABEL})+")


def valid_address_syntax(address: str) -> bool:
    """Validate a bounded, ordinary dot-atom address without consulting accounts."""
    address = address.strip()
    if len(address) > 254 or _ADDRESS.fullmatch(address) is None:
        return False
    local, _domain = address.split("@")
    return len(local) <= 64


def _issue_reset_request(store: ResetStore, key: str) -> None:
    """Honor at most five requests per normalized key in the preceding 3600s.

    Missing accounts have the same private window, but never receive a link.
    Neither the decision nor the bearer token is returned to the HTTP handler.
    """
    with store.lock:
        key = normalize_email(key)
        now = store.now()
        cutoff = now - timedelta(seconds=3600)
        recent = [
            issued for issued in store.request_times.get(key, ()) if issued > cutoff
        ]
        store.request_times[key] = recent
        if len(recent) >= 5:
            return

        recent.append(now)
        if key not in store.accounts:
            return

        token = secrets.token_urlsafe(32)
        digest = token_digest(token)
        while digest in store.reset_records:
            token = secrets.token_urlsafe(32)
            digest = token_digest(token)
        store.reset_records[digest] = ResetRecord(
            owner_key=key, issued_at=now, expires_at=now + timedelta(minutes=30)
        )
        store.owner_link_outbox.append(OwnerLink(owner_key=key, url=f"/reset/{token}"))

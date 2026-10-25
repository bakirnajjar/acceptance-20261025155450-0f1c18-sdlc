"""Private reset-request boundary; link issuance is implemented in TASK-005."""

import re

from password_reset_demo.state import ResetStore

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
    """Private normalized-key handoff for TASK-005's locked issuance policy.

    No lookup, accounting, link or external delivery is performed in this slice.
    The route never uses a result from this hook to construct its public response.
    """

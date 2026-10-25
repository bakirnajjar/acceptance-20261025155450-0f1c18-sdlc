# Password reset demo scaffold

A Python 3.12 Flask/Jinja2 project managed by [uv](https://docs.astral.sh/uv/).
The app factory provides package-relative Jinja pages, separate in-memory
synthetic A/B stores per app and signed sessions. GET `/` displays the sign-in
card; GET `/forgot-password` displays the reset-request entry form. POST
`/sign-in` authenticates only the synthetic A/B fixtures, and `/demo` is
guarded by the account's current in-memory session version. Reset issuance
and the reset-request POST handler issue opaque, one-use links privately
through the per-app owner-link outbox; no email is sent.
No real accounts, messages, or deployment are configured.

Reset password input in this local demonstration must have 1–1024 characters
and at least one non-whitespace character. Other characters, including spaces,
are preserved as entered; this is an input bound, not a production password
strength policy. A successful reset changes only the link owner's password
hash and consumes the link once. Session revocation and owner notices are
separate later slices.

## Local setup

Install Python 3.12 and uv, then from the repository root:

```sh
uv sync --locked --python 3.12
```

Dependencies (Flask, pytest, and Ruff) are pinned in `pyproject.toml` and
resolved in `uv.lock`. The project installs from `src/password_reset_demo`.
Set `PASSWORD_RESET_SESSION_SECRET` to a private random signing secret before
running the app (or creating it outside tests). It is required; do not commit
or print its value. CSRF tokens are generated separately within each signed
client session, independently of account lookup. Store state, including
synthetic password hashes and session versions, is process-local; recovery
links are available only in the private in-memory owner-link outbox, not in a
public response. The local sign-in credentials are
`owner@example.test` / `demo-owner-password` and
`peer@example.test` / `demo-peer-password` (stored as hashes, not cleartext).

## Run locally

```sh
PASSWORD_RESET_SESSION_SECRET='<private random value>' \
  uv run --locked --python 3.12 flask --app 'password_reset_demo:create_app' run
```

The development server starts on `http://127.0.0.1:5000/`. Visit `/` and follow
the recovery link to `/forgot-password`. Sign in with a synthetic fixture to
view `/demo`. Sign-in requires the form's signed-session CSRF token, and each
guarded request checks the signed account identity and version against the
per-app locked store. A changed version clears that client's stale session
on its next guarded request; other accounts are unaffected. The recovery form
submits to `POST /forgot-password` and always shows an account-neutral
confirmation for a valid address. A privately issued link opens a new-password
form until its 30-minute expiry; a successful reset redirects to the generic
`/reset-complete` page. Session revocation and owner notices are not yet
implemented.
This is only a demonstration, not a production sign-in or durable session
policy.
Do not expose this development server to the public network.

## Build / verify

Run these from the repository root:

```sh
uv run --locked --python 3.12 python -m compileall -q src tests
uv run --locked --python 3.12 pytest -q
uv run --locked --python 3.12 ruff check .
uv run --locked --python 3.12 ruff format --check .
```

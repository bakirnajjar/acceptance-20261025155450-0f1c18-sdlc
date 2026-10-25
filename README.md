# Password reset demo scaffold

A Python 3.12 Flask/Jinja2 project managed by [uv](https://docs.astral.sh/uv/).
The app factory provides package-relative Jinja pages, separate in-memory
synthetic A/B stores per app and signed sessions. GET `/` displays the sign-in
card; GET `/forgot-password` displays the reset-request entry form. POST
`/sign-in` authenticates only the synthetic A/B fixtures, and `/demo` is
guarded by the account's current in-memory session version. Reset issuance
and the reset-request POST handler are **not** implemented yet.
No real accounts, messages, or deployment are configured.

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
synthetic password hashes and session versions, is process-local; no recovery
links are issued yet. The local sign-in credentials are
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
cannot submit until a later task adds `POST /forgot-password` (currently 405).
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

# Local password reset demonstration

A Python 3.12 Flask/Jinja2 project managed by [uv](https://docs.astral.sh/uv/).
The app factory renders local sign-in and recovery pages with Jinja. Only two
synthetic accounts exist; no real identity provider, email service, database,
or deployment is configured. The private owner-link outbox and the separate
owner-notification sink are **in-memory test fixtures**, not delivery channels.

Reset password input in this local demonstration must have 1–1024 characters
and at least one non-whitespace character. Other characters, including spaces,
are preserved as entered; this is an input bound, not a production password
strength policy. A successful reset changes only the link owner's password hash, consumes the
link once, increments the owner's session version and records one owner notice
in the separate in-memory sink before claiming success. A failing in-process
notice append rolls back this local transition; it does not provide a durable
transaction across crashes.

## Local setup

Install Python 3.12 and uv, then from the repository root:

```sh
uv sync --locked --python 3.12
```

Dependencies (Flask, pytest, and Ruff) are pinned in `pyproject.toml` and
resolved in `uv.lock`. The project installs from `src/password_reset_demo`.
Set `PASSWORD_RESET_SESSION_SECRET` in your local environment to a newly
generated private random signing secret before running the app or creating an
app instance outside pytest. It is required; do not commit, share or print
its value. Pytest supplies a test-only value. CSRF tokens live in signed
client sessions independently of account lookup. The local **synthetic**
sign-in credentials (not real accounts or secret production credentials) are
`owner@example.test` / `demo-owner-password` and
`peer@example.test` / `demo-peer-password` (stored as hashes, not cleartext).

## Run locally

```sh
uv run --locked --python 3.12 flask --app 'password_reset_demo:create_app' run
```

The development server starts on `http://127.0.0.1:5000/`. Visit `/` and follow
the recovery link to `/forgot-password`. Sign in with a synthetic fixture to
view `/demo`. Sign-in requires the form's signed-session CSRF token, and each
guarded request checks the signed account identity and version against the
per-app locked store. A successful reset invalidates *all previously signed-in
owner clients* on their next guarded request; unrelated accounts are
unaffected within that app instance. The recovery form submits to
`POST /forgot-password` and always shows an account-neutral confirmation for
a syntactically valid address, including absent or throttled addresses. At
most five eligible links per normalized address are issued in a rolling hour;
links are one-use and expire at exactly 30 minutes. Successful reset redirects
to the generic `/reset-complete` page; the owner notice is recorded only in
the private sink, never sent.

### Inspect a private link in a local test process

The public confirmation never contains a reset link. In a **separate local
test-client process**, with the signing environment variable set as above,
you can exercise issuance and inspect its private outbox in the *same app
instance*:

```python
from password_reset_demo import create_app

app = create_app()
client = app.test_client()
client.get("/forgot-password")
with client.session_transaction() as signed_session:
    csrf = signed_session["_csrf_token"]
response = client.post(
    "/forgot-password",
    data={
        "email": "owner@example.test",
        "csrf_token": csrf,
    },
)
assert response.status_code == 303
store = app.extensions["reset_store"]
with store.lock:
    link = store.owner_link_outbox[-1].url  # test-only bearer URL: do not print or log
assert client.get(link).status_code == 200
```

Use this code only inside a local Python test/harness in the locked environment;
it does **not** read the state of a separately running Flask server. See
`tests/test_state.py::test_tc_015_issued_and_redeemed_link_is_isolated_between_apps`
for a complete test of private issuance and redemption. Absent or throttled
addresses have no new link. Never publish these bearer URLs.

### Limits (not production-ready)

All account hashes, rate counters, reset-token digests, session versions,
private link outbox and owner-notification sink live only in this app factory's
process-local memory. Restart resets them (including fixture passwords), loses
pending links and notices, and can leave signed cookies referring to reset
versions no longer present. Multiple workers have **divergent** counters,
tokens and versions: a link issued by one worker can be unknown to another;
neither issuance limits nor session revocation are globally enforced. No real
notification or link is delivered and no durable audit/transaction exists.
Signed cookies, CSRF checks and local token-page protections are not a
complete production security design: this lacks shared transactional storage,
cross-worker invalidation, real identity integration, durable delivery,
operational abuse controls, retention/privacy policy and a full security
review. Equal public response content does not establish equal timing.
Do not expose the development server to the public network or treat the demo
as a production authentication or password-reset service.

## Build / verify

Run these from the repository root:

```sh
uv run --locked --python 3.12 python -m compileall -q src tests
uv run --locked --python 3.12 pytest -q
uv run --locked --python 3.12 ruff check . && uv run --locked --python 3.12 ruff format --check .
```

# Password reset demo scaffold

A Python 3.12 Flask/Jinja2 project managed by [uv](https://docs.astral.sh/uv/).
This initial scaffold provides an app factory and package-relative base template;
it does **not** implement sign-in or password-reset routes yet. No real accounts,
messages, or deployment are configured.

## Local setup

Install Python 3.12 and uv, then from the repository root:

```sh
uv sync --locked --python 3.12
```

Dependencies (Flask, pytest, and Ruff) are pinned in `pyproject.toml` and
resolved in `uv.lock`. The project installs from `src/password_reset_demo`.
No environment variables are required for the scaffold.

## Run locally

```sh
uv run --locked --python 3.12 flask --app 'password_reset_demo:create_app' run
```

The development server starts on `http://127.0.0.1:5000/`. All paths currently
return 404 until later tasks add routes. Do not expose this development server
to the public network.

## Build / verify

Run these from the repository root:

```sh
uv run --locked --python 3.12 python -m compileall -q src tests
uv run --locked --python 3.12 pytest -q
uv run --locked --python 3.12 ruff check .
uv run --locked --python 3.12 ruff format --check .
```

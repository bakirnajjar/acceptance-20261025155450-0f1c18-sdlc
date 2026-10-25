# Code review assessment (Phase 1)

## Scope and evidence

Review the whole change from `1d608587158f12057d57e53be7b4325dedda5c13` through the working head against approved REQ-001–REQ-014, TASK-001–TASK-012, and TC-001–TC-025. The authorized requirements, UI analysis, solution design, test-case design, risk assessment, and coding outputs have been read; the coding output reports 13 completed tasks and 23 automated test cases, with TC-018 (bounded delivery inspection) and TC-024 (hands-on accessibility) manual. These are predecessor claims, not independent review results. The curated current-run account-recovery standard (source `knowledge`, ID `4d3e7857-9fa5-49cc-a86a-33bcf67fabee`, locator `v1, chunk 0`) requires identical existent/nonexistent reset responses, at most five requests per account per hour, single-use links expiring after 30 minutes, all-session sign-out, and owner notification after every success.

The supplied image shows a white canvas and centered outlined card: bold "Sign in"; labeled "Email address" with `name@example.com` hint; labeled "Password" with a masked `********` hint; a blue underlined "Forgot password?" link directly below; a dark full-width "Sign in" button; and gray "No account? Contact your administrator." text beneath. Only this screen is image-observed; the reset pages and sign-in behavior are proposed in the approved design, not visual facts about the attachment.

## Stack and baseline

The repository contains a Python 3.12 (`.python-version`, `pyproject.toml`) Flask 3.1.3/Jinja app under `src/password_reset_demo`, a locked `uv` dependency set, Ruff and pytest. The app factory creates independently locked process-local synthetic accounts, request timestamps, digest-indexed reset records, a private link outbox, and a separate notification sink; it injects an aware UTC clock, uses signed Flask sessions and CSRF, renders forms on the server, and includes reset-link log/response protections. Eleven pytest modules and project documentation exist. `uv` and Python 3.12 are available; the working tree was clean at assessment. No external identity, notification, database, or Docker service is required for local gates; the session secret is supplied by test setup and must never be printed. No deployment workflow appears in the inspected tree; absence of external deployments cannot be proved from repository inspection.

The existing documented full gates, to execute during an approved review rather than treat predecessor results as a pass, are:

- Build: `uv run --locked --python 3.12 python -m compileall -q src tests`
- Tests: `uv run --locked --python 3.12 pytest -q`
- Lint: `uv run --locked --python 3.12 ruff check . && uv run --locked --python 3.12 ruff format --check .`

## Review focus and risks

Map implementation **and test assertions** for every requirement and approved test case, including public parity under account and throttling differences, normalized rolling-hour boundaries and concurrent issuance; single-use and exact-expiry GET/POST boundaries and concurrent redemption; all owner sessions versus unaffected peer sessions; per-success notices and rollback on sink failure; field/CSRF errors, bearer-token non-disclosure, accessibility, production-limitations documentation and no-deployment scope. Inspect the full base-to-head diff as well as the current files; check for security and correctness defects rather than assuming passing gates establish conformance. The process-local design explicitly does not provide cross-worker counters, revocation or durable delivery; assess against the approved synthetic prototype, not production behavior absent from the requirements.

There is no independent gate result or finding yet. A later plan should preserve `R001`, include no more than two conditional fix rounds and three review rounds, write round-specific evidence and final `review.json`, and require approval before any review or product edits. This assessment changes no source files.

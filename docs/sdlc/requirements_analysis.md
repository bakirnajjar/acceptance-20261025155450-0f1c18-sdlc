# Requirements analysis

Schema version: `1.0` · Stage: `requirements_analysis`

## Source references

- `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`
- `{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"}`
- `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` — ACC-STD-01: sign-in reset link, identical responses, five requests per account per hour; ACC-STD-02: single-use links, 30-minute expiry, sign out all active sessions after reset; ACC-STD-03: notify owner after every successful reset.

## Requirements

### REQ-001 — Sign-in presentation

The server-rendered sign-in page presents the supplied sign-in card and its observed controls and text.

Acceptance criteria:

1. Given a visitor opens the sign-in page, when it renders, then a bordered card shows a 'Sign in' heading, labeled 'Email address' and 'Password' inputs, a 'name@example.com' email hint and a masked password example.
2. Given the rendered sign-in card, when the visitor views its controls, then 'Forgot password?' appears beneath the password field, a dark 'Sign in' button appears below it, and 'No account? Contact your administrator.' appears beneath the button.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`; `{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"}`.

### REQ-002 — Reset entry point

Activating the sign-in page's 'Forgot password?' link starts a password-reset request flow.

Acceptance criteria:

1. Given the sign-in page, when a visitor activates 'Forgot password?', then the visitor can start a password-reset request.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`; `{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"}`; `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-01).

### REQ-003 — Account-existence response parity

A password-reset request returns the same response whether the requested account exists or not.

Acceptance criteria:

1. Given otherwise equivalent reset requests for an existing synthetic account and a nonexistent account, when each request is submitted, then their responses are identical and do not disclose account existence.

Sources: `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-01).

### REQ-004 — Per-account request limit

Password-reset requests are limited to five per account per hour.

Acceptance criteria:

1. Given a synthetic account has received five reset requests within an hour, when a sixth request for that account is attempted within that hour, then no additional reset request for that account is honored.
2. Given the same account has received fewer than five reset requests within an hour, when an eligible request is made, then the five-per-account-per-hour limit does not prevent that request.

Sources: `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-01).

### REQ-005 — Successful reset

An issued, unused, unexpired reset link permits its synthetic account's password to be reset.

Acceptance criteria:

1. Given an issued, unused reset link for a synthetic account before its expiry, when the holder completes a password reset using the link, then that account's password changes.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`; `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-02/03).

### REQ-006 — Single-use reset link

A reset link is single-use.

Acceptance criteria:

1. Given a reset link has already completed a successful reset, when someone attempts another reset with that same link, then it cannot complete another password change.

Sources: `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-02).

### REQ-007 — Reset-link expiry

An issued reset link expires 30 minutes after issuance.

Acceptance criteria:

1. Given an issued reset link, when a reset is attempted at or after 30 minutes from its issue time, then the link cannot complete a password change.

Sources: `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-02).

### REQ-008 — Session sign-out

Successfully resetting an account's password signs that account out of every active session.

Acceptance criteria:

1. Given a synthetic account has active sessions, when its password reset completes successfully, then none of the previously active sessions remains signed in.

Sources: `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-02).

### REQ-009 — Owner notification

Every successful password reset notifies the account owner through the in-memory notification sink.

Acceptance criteria:

1. Given a synthetic account's password reset completes successfully, when the result is inspected, then a notification for that account's owner is recorded in the in-memory notification sink for that successful reset.
2. Given multiple successful resets, when the sink is inspected, then each successful reset has an owner notification.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`; `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-03).

### REQ-010 — Runtime and rendering

The application uses Python 3.12 and Flask with server-rendered pages.

Acceptance criteria:

1. Given the application implementation, when its runtime, framework and user-facing pages are inspected, then it targets Python 3.12, uses Flask and renders the pages on the server.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`.

### REQ-011 — Synthetic data and notification sink

The application uses synthetic accounts and an in-memory notification sink.

Acceptance criteria:

1. Given the application is exercised, when account data and recorded owner notifications are inspected, then the accounts are synthetic and notifications are captured in an in-memory sink rather than sent through an external notification service.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`.

### REQ-012 — Automated tests

The application provides automated pytest tests for the evidenced password-reset and sign-in requirements.

Acceptance criteria:

1. Given the project test suite, when pytest is run, then automated checks cover the sign-in presentation, reset initiation and response parity, the five-per-account-per-hour limit, successful reset, single-use and 30-minute expiry boundaries, session sign-out, and notification after each successful reset.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`; `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` (ACC-STD-01/02/03).

### REQ-013 — Production limitations

The project documents the production limitations of the small synthetic-account, in-memory application.

Acceptance criteria:

1. Given the project documentation, when it is reviewed, then it identifies production limitations of using synthetic accounts and in-memory state or notifications without asserting that this demonstration is production-ready.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`.

### REQ-014 — No deployment

The project neither deploys the application nor adds deployment workflows.

Acceptance criteria:

1. Given the project deliverables, when they are inspected, then no deployment has been performed and no deployment workflow has been added.

Sources: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`.

## Assumptions

1. acceptance-20261025155450-0f1c18-skill-sentinel: the acceptance skill produced this output.
2. The complete pinned story has no end marker to copy; the supplied image has no visible acceptance marker to copy.
3. A1 (sign-in scope): Specify the observed sign-in controls and observable invalidation of any active sessions, but do not assume a complete login/authentication policy. Synthetic sessions may be established by tests to check sign-out.
4. A2 (request accounting): State the five-per-account-per-hour rule and account-existence response parity without prescribing how nonexistent identifiers are counted or an exact rolling-versus-fixed-window algorithm; implementation must preserve response parity.
5. A3 (visual fidelity): Retain the observed structure, labels, examples and relative positions without assuming pixel measurements, breakpoints or additional visual requirements.
6. A4 (link conveyance): An in-memory test mechanism may make issued links exercisable; no external email service, real delivery mechanism or particular link format is assumed.
7. A5 (password and documentation detail): Require a valid-link password change and documentation of limitations grounded in synthetic accounts and in-memory state, but do not invent password-complexity rules or an exhaustive production checklist.

## Open questions (all non-blocking)

1. **Question:** Must the pictured sign-in button authenticate synthetic accounts, or is the depicted UI plus session behavior needed to demonstrate reset sign-out sufficient? **Blocking:** false. **Context / paired assumption:** Working assumption A1: require observed controls and invalidation of active sessions, not a complete login policy.
2. **Question:** How should requests for nonexistent identifiers be counted or limited while responses remain identical, and what precise hourly-window algorithm should apply? **Blocking:** false. **Context / paired assumption:** Working assumption A2: require five per existing account per hour and account-existence response parity without prescribing accounting or window internals.
3. **Question:** How precisely should the sign-in wireframe be reproduced at other viewport sizes, and should the examples be literal content? **Blocking:** false. **Context / paired assumption:** Working assumption A3: preserve the observed labels, hints, card, controls and relative placement without adding pixel or breakpoint targets.
4. **Question:** How should an issued reset link be conveyed or inspected in this synthetic application? **Blocking:** false. **Context / paired assumption:** Working assumption A4: an in-memory test mechanism suffices; no external email delivery or link format is specified.
5. **Question:** What exact password rules and production-limitations topics are expected? **Blocking:** false. **Context / paired assumption:** Working assumption A5: require successful valid-link password change and documented synthetic/in-memory limitations without inventing complexity rules or an exhaustive checklist.

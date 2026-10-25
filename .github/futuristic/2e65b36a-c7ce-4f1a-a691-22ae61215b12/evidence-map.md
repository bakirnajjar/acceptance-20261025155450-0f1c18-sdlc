# Requirements analysis: evidence and coverage map

This is the T001 evidence map, **not** the product requirements contract. It uses the existing `assessment.md` and the complete pinned story, supplied attachment reference, and curated standard. Candidate IDs below reserve coverage for a later contract; they do not prescribe unevidenced implementation choices.

## Authorized sources

| Key | Exact source reference | Evidence and limits |
| --- | --- | --- |
| S | `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}` | Complete story: “Build a small password-reset application with the supplied sign-in wireframe in Python 3.12 with Flask, server-rendered pages and pytest. Use the curated recovery standard. Use synthetic accounts and an in-memory notification sink. Document production limitations. Provide automated tests. Do not deploy anything or add deployment workflows.” The reader returned `next_offset: null`; there is **no story end marker**. |
| W | `{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"}` | Host's direct visual observation of the supplied image: bordered sign-in card, “Sign in” heading, “Email address” field with `name@example.com` hint, “Password” field with masked example, “Forgot password?” link beneath password, dark “Sign in” button, and “No account? Contact your administrator.” beneath the button. Attachment reader returned the reference, not extracted text. **No acceptance marker is visible.** |
| K | `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` | This run's curated account recovery standard: ACC-STD-01 (link starts reset request; identical response for existing/nonexistent accounts; five reset requests per account per hour), ACC-STD-02 (links single-use; expire 30 minutes after issue; successful reset signs out every active session), ACC-STD-03 (notify owner after every successful reset). Search also returned identical excerpts from other runs; **only this run-specific reference** is used. |

There are no approved prior-stage outputs. Repository `assessment.md` corroborates this analysis but is not substituted for a contract source reference.

## Candidate requirement coverage

Functional acceptance sketches use Given/When/Then; each candidate is independently traceable. “Then” clauses describe supported outcomes, not an unapproved token format, HTTP code, email service, UI framework, or password policy.

| Candidate | Supported behavior / constraint and acceptance sketch | Sources |
| --- | --- | --- |
| REQ-001 | Sign-in page presents the observed card and controls. **Given** a visitor opens sign-in, **when** the server-rendered page appears, **then** the bordered card displays “Sign in,” labeled email/password inputs with the observed example hints, the “Forgot password?” link beneath the password field, a dark “Sign in” button, and “No account? Contact your administrator.” beneath it. | S, W |
| REQ-002 | The sign-in link starts a reset request. **Given** the sign-in page, **when** the visitor activates “Forgot password?”, **then** they can start a password-reset request. | W, K (ACC-STD-01), S |
| REQ-003 | Do not disclose account existence in a reset-request response. **Given** requests for an existing and a nonexistent account, **when** each request is made, **then** the response is identical. | K (ACC-STD-01) |
| REQ-004 | Limit reset requests to five per account per hour. **Given** an account has reached five requests within an hour, **when** another is attempted within that hour, **then** the per-account limit prevents an additional request from being honored. Exact handling of nonexistent identifiers and presentation of the limit remain open below. | K (ACC-STD-01) |
| REQ-005 | A valid issued reset link enables a password reset. **Given** an issued, unexpired link for a synthetic account, **when** its holder completes the reset, **then** the account password changes. This is the minimal completion behavior implied by a password-reset application and ACC-STD-02/03, not a new password-policy specification. | S, K (ACC-STD-02, ACC-STD-03) |
| REQ-006 | A reset link is single-use. **Given** a link already used successfully, **when** it is used again, **then** it cannot complete another reset. | K (ACC-STD-02) |
| REQ-007 | A reset link expires 30 minutes after issue. **Given** an issued link, **when** a reset is attempted at or after its 30-minute expiry, **then** that link cannot complete the reset. | K (ACC-STD-02) |
| REQ-008 | Successful reset signs the account out of every active session. **Given** an account with active sessions, **when** its password is reset successfully, **then** every previously active session is signed out. | K (ACC-STD-02) |
| REQ-009 | Notify account owner after every successful reset. **Given** a successful reset, **when** completion is recorded, **then** an owner notification is present in the in-memory notification sink; unsuccessful attempts do not satisfy the “successful reset” trigger. | S, K (ACC-STD-03) |
| REQ-010 | Implementation constraint: Python 3.12, Flask and server-rendered pages, including the sign-in page. | S |
| REQ-011 | Data and integration constraint: synthetic accounts and an in-memory notification sink, not real accounts or an external notification service. | S |
| REQ-012 | Verification constraint: provide automated tests using pytest for evidenced behaviors and constraints, including standard boundaries. | S, K |
| REQ-013 | Documentation constraint: document production limitations of this small synthetic, in-memory application. Do not silently assert any particular deployment readiness. | S |
| REQ-014 | Scope exclusion: do not deploy the application or add deployment workflows. | S |

Coverage check: W's heading, field labels/examples, link position, button style and administrator message are included in REQ-001/002; ACC-STD-01 maps to REQ-002–004, ACC-STD-02 to REQ-005–008, and ACC-STD-03 to REQ-009; every explicit story constraint maps to REQ-001/005 and REQ-010–014. The standard's five/hour and 30-minute values are the only supported numeric limits; do not invent others.

## Non-blocking questions and paired working assumptions

| Question (non-blocking) | Paired assumption for later requirements |
| --- | --- |
| Must the pictured sign-in button authenticate accounts, or is the depicted sign-in UI plus session behavior needed to prove reset sign-out sufficient? | Specify the observed sign-in controls and the observable invalidation of any active sessions; do not invent a complete login/authentication policy. Tests may establish synthetic sessions to check invalidation. |
| How are requests for nonexistent identifiers counted or limited while keeping existing/nonexistent responses identical? What is the precise request-window boundary? | State the explicit per-account five-per-hour rule and identical response. Leave nonexistent-identifier accounting and finer boundary algorithms as implementation decisions that must not reveal account existence; do not prescribe a rate-limit data structure or response text. |
| How precisely should the wireframe be reproduced at other viewport sizes, and are the example hints literal content? | Retain the visually observed structure, labels, hints and relative placement; do not invent pixel measurements, responsive breakpoints, or an extra accessibility/performance target. |
| How is a reset link conveyed or inspected in a synthetic test application? | Allow an in-memory test mechanism for exercising issued links without asserting real email delivery, link format, or an external notification provider. Owner notification **after successful reset** remains mandatory. |
| What exact password rules and production-limitations topics are expected? | Require a successful valid-link password change and a production-limitations document grounded in synthetic accounts/in-memory state; do not invent complexity rules or an exhaustive production security checklist. |

The eventual contract must include an assumption beginning **`acceptance-20261025155450-0f1c18-skill-sentinel`** followed by a short note that the acceptance skill produced the output. No story end marker or image acceptance marker exists to copy into an assumption. Preserve the exact source objects above in future `source_references`, use non-blocking questions with their paired assumptions, and use Given/When/Then criteria for functional requirements.

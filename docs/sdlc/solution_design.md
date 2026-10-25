# Solution design — synthetic password reset

**Status:** proposed architecture and implementation backlog, not an implemented application, test result, deployment or production-readiness assertion. This document is the readable companion to `solution_design.json` (`schema_version: 1.1`, `stage: solution_design`). The approved `requirements_analysis` defines REQ-001–REQ-014; approved `ui_analysis` distinguishes observed from proposed UI; the approved risk output describes prospective risks rather than existing defects. Those prior-stage reads supplied no citable `stage_output` locator, so the REQ identifiers are retained without a fabricated predecessor citation.

## Evidence

| Evidence | Exact source reference | Use and limit |
| --- | --- | --- |
| Pinned story | `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"}` | Python 3.12, Flask, server rendering, pytest, synthetic accounts, in-memory notification sink, documented limits, no deployment/workflows. |
| Supplied image | `{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"}` | Visual sign-in card only; not behavior or a recovery-screen design. |
| Current-run account recovery standard | `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}` | ACC-STD-01: reset entry, same existing/nonexistent request responses, five requests/account/hour. ACC-STD-02: single-use, 30-minute links and all-session sign-out. ACC-STD-03: notification after **every** successful reset. Other similarly titled standards from other runs are not used. |

## Architecture and interaction

The **observed** white canvas contains one centered outlined rectangular card: bold “Sign in”; labeled “Email address” with `name@example.com` hint; labeled “Password” with masked `********` example; blue underlined “Forgot password?” immediately below the password field; dark full-width “Sign in” button; then gray “No account? Contact your administrator.” The image does not establish populated field values, authentication behavior, click destination, pixels, breakpoints or any recovery screen. Treat examples as hints, not actual credentials. The link destination, synthetic sign-in, reset-request form, neutral confirmation, new-password form, unusable-link view and success view below are **proposals**. Labels, keyboard use, focus order, associated errors and status announcements are proposed accessibility affordances, not image-observed properties. [Image; Story]

- **Flask app factory and Jinja templates (Python 3.12):** server-render forms and confirmations, centralize CSRF checking and output escaping, and keep public reset responses account-existence-neutral. Browser ↔ Flask is the only network boundary; there is no JSON API, external identity provider or delivery service. [Story; Standard]
- **Recovery service, clock and locked in-memory store:** each app instance owns synthetic accounts with normalized fixture email keys and password hashes, request timestamps for normalized keys, digest-indexed reset records `(account_id, issued_at, expires_at, consumed)`, and per-account session versions. Inject an aware UTC clock. Under one process-local lock, account for requests/issue tokens and validate/commit resets to avoid local oversubscription and replay. [Story; Standard]
- **Private link outbox and separate owner-notification sink:** eligible existing-account requests put an owner-directed reset URL into a test-inspectable in-memory outbox, never in the public request response. Each committed reset appends one owner-directed notice to a distinct in-memory sink. Neither is actual mail delivery or a durable audit log. [Story; Standard]
- **Session guard:** a proposed minimal synthetic sign-in sets account ID/version in a signed Flask session cookie. Every authenticated request compares the cookie version to the account's current store version; a completed reset bumps the version, making every prior account session unusable on next guarded access, including another client or the resetter. A cookie alone does not revoke itself. This is a demonstrator mechanism, not an inferred sign-in policy. [Standard; Image]

### Proposed route and data contracts

| Route | Proposed request, response and state effect |
| --- | --- |
| `GET /` | Sign-in card with observed copy/relative arrangement and `href="/forgot-password"`; no prefilled secrets. |
| `POST /sign-in` | CSRF-checked synthetic email/password only; on success set `(account_id, session_version)` in signed cookie and redirect to a guarded demo view; generic invalid-credential feedback. Every guarded route checks current version. |
| `GET /forgot-password` | Labeled email-address form with CSRF state and field-associated errors. |
| `POST /forgot-password` | For equivalent syntactically valid inputs, normalize/account privately and **always** respond with the same neutral `303` to `/reset-requested`, including same account-dependent headers/cookies. No address, token, lookup result or throttle banner in the response. Empty/malformed addresses have account-independent field errors. CSRF state is initialized before and independently of lookup. |
| `GET /reset-requested` | Static conditional confirmation with link back to sign-in, not a claim that an email or link was delivered. |
| `GET /reset/<token>` | Digest-lookup; unused and `now < issued_at + 30 minutes` renders proposed new-password form without consuming. Unknown/used/expired tokens lead to non-success retry path. |
| `POST /reset/<token>` | CSRF-check and minimal documented input validation; under lock recheck digest, unused status and strict expiry at **commit time**. A valid attempt hashes the new password, consumes the token, bumps the account session version and appends one owner notice before returning `303` to `/reset-complete`. An invalid, replayed or expired attempt makes no success claim or state change. |
| `GET /reset-complete` | Generic proposed completion state and link to sign-in; no token or account details. |

At UTC instant `t`, the proposed **rolling** account window discards timestamps `<= t - 3600 seconds`, honors only when fewer than five remain and records an honored request. The sixth before the oldest timestamp leaves the window is silently suppressed; at exactly one hour the oldest falls out. Apply the same private accounting to normalized nonexistent identifiers without a link; all equivalent valid public responses remain identical even at the threshold. This algorithm, as opposed to a calendar-hour bucket or visible `429`, is a design choice rather than an extra sourced criterion. Generate a cryptographically random opaque URL-safe token; keep only its digest as the reset-record key, while its URL remains a sensitive private outbox value. Link expiry is **exactly** 30 minutes after issue: valid only at `now < expires_at`; equality is expired. GET does not consume and a later POST must recheck. [Standard]

The process-local success operation holds the lock while validating and committing password hash, consumed token, session-version bump and exactly one owner-notification append; prepare/restore state if an in-process append fails and do not advertise success on partial failure. Concurrent posts for the same token yield at most one success. This does **not** supply a durable transaction or delivery guarantee across process crashes. [Standard; Story]

### Persistence, protection and operation

No database or migration is proposed. Synthetic fixtures initialize each per-app store. Restart loses rate history, tokens, session versions, link outbox and notices; multiple workers diverge. Production would need shared transactional persistence, durable notification delivery, broader abuse controls, retention/privacy and security review; none is authorized here. `hosting.kind` is `none`; no deployment or deployment workflow is proposed. No existing package manager or runnable build/test/lint command was verified, so `package_manager` and `quality_gates` are null; TASK-010/011 propose pytest checks for future implementation, not a passed gate. [Story]

Protect state-changing forms with CSRF, escape template output, hash passwords using an appropriate framework hasher, and configure signed session cookies as `HttpOnly`, `SameSite=Lax` and `Secure` under HTTPS; keep secrets out of tracked files. Token URLs are bearer secrets: token-bearing responses use `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, no third-party assets and token-path redaction in ordinary request/error logs. Avoid logging passwords, raw tokens or submitted addresses. Internal counters may record anonymous request, throttle, expiry/replay, reset and notice events, but logging cannot weaken identical public account-existence responses. Equal static responses alone do not prove equal timing; production-grade privacy, audit, delivery, multi-worker invalidation and availability are outside this prototype. Local pytest with fake UTC time and multiple clients should verify status, redirects, confirmation bodies and account-dependent headers/cookies, as well as private effects. [Story; Standard]

### Significant choices and alternatives

| Chosen proposal | Alternative considered | Rationale and boundary |
| --- | --- | --- |
| Per-app locked in-memory store and injectable UTC clock | SQL database/distributed cache | Matches synthetic scope and deterministic boundary/race tests; not persistent or multi-worker safe. |
| Rolling 3600-second per-normalized-key window, silent suppression and private nonexistent-key accounting | Calendar-hour bucket or visible `429` | Precise fifth/sixth boundary with parity; window and accounting are design choices, not specified standard details. |
| Opaque random link, digest index and private test outbox | Public confirmation link or actual email | Exercises reset without disclosing account existence or introducing delivery; outbox URLs remain sensitive. |
| Per-account session version checked on every guarded route | Browser-local logout or enumerating session IDs | Invalidates all prior cookies for an account within the single process; no cross-worker guarantee. |
| Strict commit-time expiry and consume on successful POST | Check only on GET or consume on GET | Preserves exact 30-minute boundary and prevents replay or prefetch consumption. |
| Minimal synthetic sign-in and proposed recovery screens | Infer full authentication policy or pictured reset screens | Supports observable sign-out without claiming behavior unseen in the wireframe. |
| Synchronous in-memory owner notice per committed reset | Fire-and-forget event or real email | Allows per-success verification; cannot promise durable external delivery. |

## Ordered implementation tasks

These are **proposed** slices, not application code or work already done. The criteria below mirror the JSON contract. Every dependency points to an earlier task; task source keys `S`, `I`, `K` mean the **exact** story, image and knowledge references in the evidence table, respectively (not predecessor-stage citations).

### TASK-001 — Scaffold isolated Flask state and clock
**REQ-010, REQ-011 · Depends on:** none · **Sources:** S, K. Establish Python 3.12 runtime/dependency metadata, Flask factory/Jinja base, per-app synthetic hashed accounts, locked normalized-key/timestamp/digest-token/session-version state, private link outbox, distinct owner sink, injectable aware UTC clock, signed cookie configuration and account-independent CSRF state. No stored secrets or durable migration.

**Acceptance:** (1) Python 3.12 Flask renders a server-side template without database, real accounts or external notification. (2) Two app instances isolate all fixtures/state/sinks and each fake UTC clock advances independently. (3) Credentials use hashes, reset records are digest-indexed and later transitions can lock atomically.

### TASK-002 — Render sign-in and reset-entry forms
**REQ-001, REQ-002, REQ-010 · Depends on:** TASK-001 · **Sources:** S, I, K. Render observed card on `GET /`; propose labeled, CSRF-ready `GET /forgot-password`, keyboard/focus/error handling and a return path; prepare sign-in form for TASK-003 without inferring authentication from the picture.

**Acceptance:** (1) Server-rendered white canvas/centered outlined card shows bold Sign in, labeled Email address and Password, `name@example.com` hint and masked `********` example, neither prefilled. (2) Blue underlined Forgot password? immediately below Password, dark full-width Sign in button, and gray No account? Contact your administrator. beneath button. (3) Activating the link opens a proposed labeled request form with usable focus order and associated errors.

### TASK-003 — Demonstrate guarded synthetic sessions
**REQ-008, REQ-010, REQ-011 · Depends on:** TASK-001, TASK-002 · **Sources:** S, I, K. Add CSRF-checked minimal synthetic `POST /sign-in`, signed versioned sessions and a guarded demo view with version comparison on every authenticated request, rejecting/clearing stale cookies.

**Acceptance:** (1) Two independent clients sign in to one synthetic account; invalid credentials do not authenticate. (2) After its version changes both clients fail next guarded access, while another account remains signed in. (3) A signed cookie cannot bypass version guard; no real identity or durable session service is added.

### TASK-004 — Return neutral reset-request responses
**REQ-002, REQ-003, REQ-010 · Depends on:** TASK-001, TASK-002 · **Sources:** S, K. Add CSRF-checked `POST /forgot-password`, static `GET /reset-requested` and a private issuance hook for TASK-005, with CSRF state independent of lookup.

**Acceptance:** (1) Equivalent valid existing/nonexistent requests return identical neutral redirect, destination and account-dependent headers/cookies without exposing address, link or delivery assertion. (2) Empty/malformed input gets the same accessible field error regardless of account existence. (3) Private issuance handoff cannot alter public response; full issuance is deferred to TASK-005.

### TASK-005 — Enforce rolling-hour issuance ceiling
**REQ-003, REQ-004, REQ-005, REQ-011 · Depends on:** TASK-001, TASK-004 · **Sources:** S, K. Implement under-lock normalized-key rolling-hour accounting, private nonexistent-key accounting, random opaque link generation with digest record and owner-directed test outbox. Suppress over-limit issuance silently.

**Acceptance:** (1) Exactly five links for five eligible existing-account requests, no sixth just before one hour, renewed eligibility at oldest timestamp plus one hour, and no parallel oversubscription. (2) Nonexistent keys get no link; equivalent existing/nonexistent and under/over-limit public status, redirect, confirmation and account-dependent headers/cookies match. (3) Tokens stay in private outbox, not public response/cookie/log; no external mail service.

### TASK-006 — Present usable or unusable reset links
**REQ-005, REQ-006, REQ-007, REQ-010 · Depends on:** TASK-001, TASK-005 · **Sources:** S, K. Propose `GET /reset/<token>` password form for unused pre-expiry tokens and a non-success retry view for invalid ones; digest-lookup without consuming, protect token pages and provide CSRF-ready accessible controls.

**Acceptance:** (1) Valid unused pre-expiry GET renders server-side form without consuming; unknown/used/expired links show no success and offer a new-request path. (2) Form unavailable at or after exact 30-minute expiry; earlier GET does not promise a later POST will pass. (3) Token responses use no-store/no-referrer, no third-party assets and no token echo in ordinary content.

### TASK-007 — Commit one-use password changes
**REQ-005, REQ-006, REQ-007 · Depends on:** TASK-001, TASK-006 · **Sources:** S, K. Add CSRF-checked `POST /reset/<token>`, minimal documented password validation and generic `GET /reset-complete`; lock/recheck at commit and prepare atomic extension for TASK-008/009 with rollback on in-process failure.

**Acceptance:** (1) Valid unused link before 30 minutes updates only owner hash, invalidates old password and claims success only after commit. (2) Expired at equality or later, used or concurrent replayed links do not produce another change/success; at most one racing POST succeeds. (3) Initially valid GET followed by expired POST fails; invalid input has field-associated error and leaves state unchanged.

### TASK-008 — Revoke every prior account session
**REQ-008 · Depends on:** TASK-003, TASK-007 · **Sources:** K, S. Extend locked success transition with owner session-version increment; rely on TASK-003's check for **every** protected request.

**Acceptance:** (1) At least two formerly signed-in owner clients, including a signed-in resetter, fail next guarded access; unrelated account still works. (2) Failed/expired/replayed resets do not revoke. (3) Password change, token consumption and version bump are one process-local locked transition.

### TASK-009 — Record each successful owner notice
**REQ-009, REQ-011 · Depends on:** TASK-007, TASK-008 · **Sources:** S, K. Extend the same locked success boundary to append one owner-directed record per committed reset to the distinct in-memory sink; restore/abort on in-process sink failure, never claim durable delivery.

**Acceptance:** (1) Two separate successful resets for one synthetic account yield two owner-directed records. (2) Expired/unknown/invalid/replayed/losing concurrent attempts produce no notice or false success. (3) A simulated sink failure cannot leave a claimed password success without its record; no external service.

### TASK-010 — Test sign-in, parity and hourly edges
**REQ-001, REQ-002, REQ-003, REQ-004, REQ-012 · Depends on:** TASK-002, TASK-004, TASK-005 · **Sources:** S, I, K. Add pytest/Flask-client checks for card/entry, parity and five-per-hour edges with fake time and private outbox.

**Acceptance:** (1) Assert observed controls/copy/order and recovery entry without inventing unseen pixels or sign-in policy. (2) Compare public status, Location, destination body and account-dependent headers/cookies across existing/nonexistent and below/at/above limit, inspecting private issuance separately. (3) Five links at `t0`, no sixth at `t0+3599s`, new eligibility at `t0+3600s`, identical public responses and account-independent invalid-input errors.

### TASK-011 — Test reset boundaries and effects
**REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-012 · Depends on:** TASK-006, TASK-007, TASK-008, TASK-009, TASK-010 · **Sources:** S, K. Add isolated pytest with aware fake UTC clock and multiple clients after integrated reset effects; check non-success UI and token response protections.

**Acceptance:** (1) Separate links pass one microsecond before 30 minutes, fail at/after exact expiry, and fail when a valid GET precedes expired POST. (2) Reuse/concurrent replay and invalid/expired attempts do not alter password/version/notice count. (3) All prior owner sessions fail, unrelated account remains signed in; two distinct successful resets yield two owner notices. Run pytest on Python 3.12 and report real outcomes rather than assume success.

### TASK-012 — Document limitations and inspect delivery scope
**REQ-013, REQ-014 · Depends on:** TASK-010, TASK-011 · **Sources:** S. Document local setup, pytest, synthetic fixtures, private link inspection, process-local volatility, restart/multi-worker limits, lack of actual delivery and incomplete production protections; review final changes/execution for prohibited deployment/workflows.

**Acceptance:** (1) Documentation identifies synthetic/in-memory/notification limits without claiming production readiness. (2) Final review confirms neither deployment nor added deployment workflow; local tests are not deployment. (3) No production service, durable migration, deployment configuration, workflow or host is introduced.

## Requirement coverage

| Approved ID | Tasks | Retained outcome |
| --- | --- | --- |
| REQ-001 | TASK-002, TASK-010 | Observed sign-in card controls/copy/relative placement. |
| REQ-002 | TASK-002, TASK-004, TASK-010 | Forgot-password entry and request form. |
| REQ-003 | TASK-004, TASK-005, TASK-010 | Identical existing/nonexistent public response, also throttled. |
| REQ-004 | TASK-005, TASK-010 | Five eligible/hour; sixth suppressed; boundary checked. |
| REQ-005 | TASK-005, TASK-006, TASK-007, TASK-011 | Issued, unused, unexpired link changes owner password. |
| REQ-006 | TASK-006, TASK-007, TASK-011 | One use; replay cannot change password. |
| REQ-007 | TASK-006, TASK-007, TASK-011 | Valid before, invalid at/after exact 30 minutes. |
| REQ-008 | TASK-003, TASK-008, TASK-011 | All former owner sessions signed out. |
| REQ-009 | TASK-009, TASK-011 | Notice per successful reset. |
| REQ-010 | TASK-001, TASK-002, TASK-003, TASK-004, TASK-006 | Python 3.12/Flask/server rendering. |
| REQ-011 | TASK-001, TASK-003, TASK-005, TASK-009 | Synthetic accounts and in-memory notification sink. |
| REQ-012 | TASK-010, TASK-011 | Automated pytest across sign-in and recovery edges. |
| REQ-013 | TASK-012 | Production-limitations documentation. |
| REQ-014 | TASK-012 | No deployment or deployment workflow. |

`coverage_dispositions: []`: all fourteen approved IDs have at least one task; there is no silent exclusion. TASK-001–TASK-012 are unique and dependency-ordered.

## Assumptions and open questions

The image depicts only the sign-in card, not authentication or reset UI behavior; examples are treated as hints. Minimal synthetic sign-in, a process-local private link outbox, rolling 3600-second accounting including private nonexistent-key counters and a minimal documented password-input rule are proposed choices, not sourced mandates. No existing executable test gate or implementation is claimed. REQ identifiers are approved predecessor identifiers, but no predecessor source-reference locator was supplied.

All questions are currently nonblocking **design confirmations**, not permission to weaken ACC-STD-01/02/03: Should sessions be created via a minimal synthetic sign-in or test setup? Are the image examples placeholders and what responsive fidelity is desired? Should link inspection be tests-only or also local-only? Is rolling-window/nonexistent-key accounting acceptable? What password-input rule and recovery-page copy should be used?

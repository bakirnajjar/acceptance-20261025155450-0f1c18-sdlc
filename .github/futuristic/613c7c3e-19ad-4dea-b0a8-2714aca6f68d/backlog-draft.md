# Solution-design implementation backlog (T002 draft)

**Status:** proposed dependency-ordered implementation slices, not production implementation, an approved implementation plan, or the final `docs/sdlc` contract. This draft elaborates `architecture-draft.md` using `assessment.md`, the approved `requirements_analysis` identifiers and exact criteria, the approved `ui_analysis` observed/proposed distinction, and the approved prospective risk register. The prior-stage output service supplied no citable locator: use predecessor **REQ-001–REQ-014** as identifiers, but do not fabricate `stage_output` source references. The only citable sources in task records are the exact story, attachment, and current-run knowledge references below. No tests have been run or deployment performed.

**Scope and slice rules.** Python 3.12, Flask, server-rendered Jinja pages, pytest, synthetic fixtures, one synchronized process-local in-memory store with injectable aware UTC clock and in-memory outbox/notification sink. The wireframe shows only the sign-in card; all navigation behavior and recovery screens are proposed. Minimal synthetic sign-in is a **nonbinding design assumption** to make every-session sign-out observable, not evidence of an authentication policy. Keep source IDs, requirement IDs, and task IDs stable when transferring this draft to the future contract. All tasks are sized for one developer and independently reviewable; prerequisites precede dependents. No external delivery, durable persistence, migration, real account integration, deployment, or deployment workflow belongs to any slice.

## Task records (proposed `DesignTask` fields)

### TASK-001 — Scaffold isolated Flask state and clock

- **description:** Establish Python 3.12 dependency/runtime metadata, a Flask application factory and server-rendered Jinja base, and per-app synthetic account fixtures with framework-hashed passwords. Supply a synchronized in-memory store with normalized synthetic email keys, request timestamps, digest-indexed reset records, per-account session versions, an owner-directed link outbox, a distinct owner-notification sink, and an injectable timezone-aware UTC clock. Provide local/test configuration for a signed session cookie (`HttpOnly`, `SameSite=Lax`, `Secure` under HTTPS) and account-independent CSRF form state. Keep secrets out of tracked files. This is a single-process demonstrator, not a persistence migration or production auth system.
- **requirement_ids:** `["REQ-010", "REQ-011"]`
- **acceptance_criteria:**
  - On Python 3.12, a Flask app instance renders a server-side template without a database, real-account service, or external notification service.
  - Two app instances have isolated synthetic accounts, counters, tokens, session versions, outbox, and notification sink; a fake UTC clock can advance either instance deterministically.
  - Fixture credentials are checked against password hashes, and reset-token records are keyed by digest rather than raw token; locking supports atomic subsequent transitions.
- **depends_on:** `[]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-002 — Render sign-in and reset-entry forms

- **description:** Render the observed sign-in card on `GET /` and propose `GET /forgot-password` with a labeled email field, CSRF-protected submission to the later request handler, field-associated input feedback, keyboard-operable controls and a neutral return path. Preserve the observed text/order/relative placement without inferring pixel dimensions, field values, responsive breakpoints, a sign-in policy or any pictured recovery screen. Give sign-in a form action for the next slice; only the recovery `href` must work in this slice.
- **requirement_ids:** `["REQ-001", "REQ-002", "REQ-010"]`
- **acceptance_criteria:**
  - The server-rendered white sign-in canvas contains one centered outlined rectangular card with bold `Sign in`, labeled `Email address` and `Password`, a `name@example.com` hint and masked `********` example (neither exposed as prefilled credentials).
  - A blue underlined `Forgot password?` is immediately below the password field; a dark full-width `Sign in` button follows; gray `No account? Contact your administrator.` follows the button.
  - Activating `Forgot password?` opens a proposed, labeled reset-request form. Control names, focus order and associated validation messages are usable without relying on visual styling alone.
- **depends_on:** `["TASK-001"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-003 — Demonstrate guarded synthetic sessions

- **description:** Add only the minimal synthetic `POST /sign-in` needed to establish independent signed Flask sessions, plus a demonstrator authenticated route. Record `(account_id, session_version)` in each session; on **every** authenticated request compare its version with the current store value and reject/clear stale sessions. Use generic invalid-credential feedback and CSRF checking. This mechanism tests account-wide invalidation; it does not infer full authentication requirements from the pictured button.
- **requirement_ids:** `["REQ-008", "REQ-010", "REQ-011"]`
- **acceptance_criteria:**
  - Two separate test clients may independently sign in to the same synthetic account and access a guarded view; invalid synthetic credentials do not establish a session.
  - If that account's stored session version changes, neither old client's next guarded request is authenticated; a different account's still-current session remains valid.
  - A signed cookie alone does not bypass the current-version check; no real identity provider or durable session service is added.
- **depends_on:** `["TASK-001", "TASK-002"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-004 — Return neutral reset-request responses

- **description:** Implement CSRF-checked, syntactically validated `POST /forgot-password` and static `GET /reset-requested`. For equivalent valid requests, always produce the same `303` status, `/reset-requested` location, public headers/cookies and neutral confirmation, regardless of account existence; do not echo an address, token, account state or individualized flash value. Build the route around a private request-service hook to be filled by TASK-005. Invalid/empty addresses receive the same field-associated form error irrespective of account existence. Any CSRF state must be initialized before, and independently of, account lookup.
- **requirement_ids:** `["REQ-002", "REQ-003", "REQ-010"]`
- **acceptance_criteria:**
  - Existing and nonexistent syntactically valid addresses yield identical observable redirect, destination content and account-dependent headers/cookies; neither response reveals whether a link was issued.
  - Empty or malformed addresses have equivalent, accessible validation feedback without checking an account; the confirmation does not assert delivery or display a token.
  - The route exposes a private handoff for issuance without placing sensitive data into the public response. End-to-end issuance follows in TASK-005.
- **depends_on:** `["TASK-001", "TASK-002"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-005 — Enforce rolling-hour issuance ceiling

- **description:** Fill the request-service hook under the store lock. Normalize fixture addresses consistently; at UTC time `t` discard timestamps `<= t - 3600 seconds` and honor an eligible existing-account request only when fewer than five retained timestamps remain, then record its timestamp. Use the same private counter policy for nonexistent normalized identifiers without sending a link. Existing eligible accounts receive a cryptographically random opaque URL-safe link, stored by token digest with issue/expiry time, in the private owner-directed test outbox. The sixth within the rolling hour is silently suppressed; public route/confirmation behavior stays unchanged. This precise rolling-window choice is a design decision, not an additional sourced criterion.
- **requirement_ids:** `["REQ-003", "REQ-004", "REQ-005", "REQ-011"]`
- **acceptance_criteria:**
  - An existing synthetic account receives exactly five privately inspectable links for five eligible requests in a rolling hour, no sixth link just before the oldest request's one-hour boundary, and a fresh link when that oldest timestamp is exactly one hour old; parallel submissions cannot exceed the ceiling.
  - Nonexistent identifiers receive no link; valid existing, nonexistent, eligible and throttled attempts remain identical in externally observable status, redirect, confirmation content and account-dependent headers/cookies.
  - The outbox is process-local/test-inspectable only: no public response, cookie or log contains a token, and no external email service is introduced.
- **depends_on:** `["TASK-001", "TASK-004"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-006 — Present usable or unusable reset links

- **description:** Add proposed `GET /reset/<token>` form and a recoverable non-success view with a link to request another reset. Digest-lookup the token; show the password form only for an unused token with `now < issued_at + 30 minutes`. GET never consumes. Set `Cache-Control: no-store` and `Referrer-Policy: no-referrer`; omit third-party assets and mask token path segments in application logs. Add CSRF form state, labels and associated errors without representing the recovery view as wireframe-observed.
- **requirement_ids:** `["REQ-005", "REQ-006", "REQ-007", "REQ-010"]`
- **acceptance_criteria:**
  - Opening an issued unused link before its exact expiry renders a server-side new-password form without consuming it; an unknown, used or expired link shows no success claim and offers a fresh-request path.
  - At `issued_at + 30 minutes` exactly, and after that instant, the form is unavailable; a valid-looking GET beforehand does not promise that a later POST will succeed.
  - Token-bearing responses are non-cacheable and have no-referrer policy; templates do not load third-party assets or echo bearer tokens into ordinary page content.
- **depends_on:** `["TASK-001", "TASK-005"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-007 — Commit one-use password changes

- **description:** Implement CSRF-checked `POST /reset/<token>` with a minimal documented password validation rule (not an invented production complexity policy), and a generic `GET /reset-complete` view. Recheck token digest, unused state and strict `now < expires_at` under the store lock at **commit time**; on validity change the synthetic password hash and mark the token used in one synchronized transition. Prepare the transition so TASK-008 can add session-version invalidation and TASK-009 can append notifications within the same success boundary. If any part of the in-process transition fails, restore state and do not render success.
- **requirement_ids:** `["REQ-005", "REQ-006", "REQ-007"]`
- **acceptance_criteria:**
  - An unused link submitted just before its 30-minute expiry changes only its owning synthetic account's password and redirects to success only after commit; the old password no longer matches.
  - At exactly 30 minutes or later, or after a prior success, GET/POST cannot make another password change or claim success; two concurrent posts with one token yield at most one success.
  - A token whose GET was initially valid but whose POST arrives at expiry is rejected at POST; invalid input is field-associated and leaves the token/password unchanged.
- **depends_on:** `["TASK-001", "TASK-006"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-008 — Revoke every prior account session

- **description:** Extend the TASK-007 synchronized reset-success transition to increment the account's session version along with password mutation and token consumption. Exercise the existing TASK-003 guard on every protected route; stale cookies may be cleared on next access. Do not rely on a browser-only sign-out or claim that stateless signed cookies revoke themselves without the server-side version check.
- **requirement_ids:** `["REQ-008"]`
- **acceptance_criteria:**
  - After one successful reset, two or more previously authenticated, distinct clients for that account all fail their next guarded request, including a resetter who was signed in; an unrelated account's session still works.
  - A failed, expired or replayed reset does not increment the version; no prior session is spuriously revoked.
  - Password change, token consumption and version bump form one locked process-local transition, not separate success claims.
- **depends_on:** `["TASK-003", "TASK-007"]`
- **source_references:** `[{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"},{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"}]`

### TASK-009 — Record each successful owner notice

- **description:** Extend the same process-local successful-reset transition to append exactly one owner-directed notification record to the distinct in-memory sink for **each** committed reset, including later successful resets using freshly issued links. Prepare/append atomically with password, consumed token and version bump or restore prior state on an in-process sink failure; do not advertise success before recording the notice. The record is not evidence of email delivery or durable notification after a process crash.
- **requirement_ids:** `["REQ-009", "REQ-011"]`
- **acceptance_criteria:**
  - Each of two distinct successful resets for the same synthetic account has its own owner-addressed sink record; success count and that account's notification count match.
  - Expired, unknown, invalid-input, replayed and losing concurrent POST attempts add no notification and cannot claim reset success.
  - A simulated in-process sink failure cannot leave a claimed successful password change without its record; no external mail or event service is added.
- **depends_on:** `["TASK-007", "TASK-008"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-010 — Test sign-in, parity and hourly edges

- **description:** Add pytest/Flask-client tests for observed sign-in presentation and the proposed recovery entry; test neutral request responses across synthetic existing/nonexistent identifiers and under/at/over the issuance ceiling using the fake clock and private outbox. Compare full public response surfaces, not just copied text. This slice covers request behavior independently of reset completion.
- **requirement_ids:** `["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-012"]`
- **acceptance_criteria:**
  - Pytest asserts the observed card controls/copy/order and that `Forgot password?` opens the request form; tests do not assert unseen recovery pixels or a complete pictured auth policy.
  - For equivalent valid existing/nonexistent requests, assert equal status, `Location`, body after redirect, account-dependent headers/cookies and no token/address leakage, both below limit and at/above the throttle edge; inspect private outbox separately.
  - At fixed `t0`, requests one through five yield five existing-account links, sixth at `t0 + 3599 seconds` yields none, and request at `t0 + 3600 seconds` is eligible after the oldest timestamp leaves the rolling window; assert same public response throughout. Invalid inputs have account-independent field errors.
- **depends_on:** `["TASK-002", "TASK-004", "TASK-005"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-011 — Test reset boundaries and effects

- **description:** Add pytest cases with isolated fixtures, fake UTC time and multiple Flask clients to verify issued-link password change, strict expiry, replay/racing, all-session invalidation and one owner notification per distinct success. Check non-success UI, cache/referrer controls and no mutation on failure. Test after TASK-009 integrates all effects; keep acceptance assertions explicit rather than treating a green smoke test as coverage.
- **requirement_ids:** `["REQ-005", "REQ-006", "REQ-007", "REQ-008", "REQ-009", "REQ-012"]`
- **acceptance_criteria:**
  - Separate links and isolated clocks verify a successful password change at `issued_at + 30 minutes - 1 microsecond`, rejection **at** `issued_at + 30 minutes`, and rejection **after** it; a valid GET followed by an expired POST fails without mutation.
  - A used link, including a repeated or concurrent POST, cannot change the password again or emit another owner notification; failed and expired attempts preserve password/version/notification count.
  - With two or more simultaneous sessions for the owner and another account's session, each valid reset signs out **all** prior owner sessions only; two distinct successful resets produce two owner notification records in the in-memory sink. Run pytest on Python 3.12 and report actual results rather than assuming a pass.
- **depends_on:** `["TASK-006", "TASK-007", "TASK-008", "TASK-009", "TASK-010"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"},{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}]`

### TASK-012 — Document limitations and inspect delivery scope

- **description:** Document local setup, pytest execution, synthetic fixtures, private link inspection, non-durable in-memory counters/tokens/session versions/outbox/owner sink, process-restart and multi-worker limits, and absence of actual notification delivery or a complete production authentication/security system. Review final changed paths and execution record for accidental deployment actions and new deployment workflows. This is a documentation/review slice, **not** permission to deploy, create CI/CD workflows, or implement persistent infrastructure.
- **requirement_ids:** `["REQ-013", "REQ-014"]`
- **acceptance_criteria:**
  - Project documentation identifies synthetic data and process-local state/notifications as production limitations without calling the demonstration production-ready or promising actual owner email delivery.
  - Final deliverable review confirms no deployment occurred and no deployment workflow was added; local pytest/build work alone is not a deployment.
  - No production service, migration, deployment configuration, workflow or hosted environment is introduced to satisfy this documentation task.
- **depends_on:** `["TASK-010", "TASK-011"]`
- **source_references:** `[{"source_type":"user_story","source_id":"user_story","locator":"characters 0-8000"}]`

## Requirement coverage and disposition

| Approved requirement | Implementing or checking task IDs | Criterion retained |
| --- | --- | --- |
| REQ-001 | TASK-002, TASK-010 | Observed sign-in controls, text and relative layout. |
| REQ-002 | TASK-002, TASK-004, TASK-010 | Active reset entry and request form. |
| REQ-003 | TASK-004, TASK-005, TASK-010 | Existing/nonexistent responses identical, including throttling. |
| REQ-004 | TASK-005, TASK-010 | Five honored per account within an hour; eligible earlier requests and rolling-hour boundary. |
| REQ-005 | TASK-005, TASK-006, TASK-007, TASK-011 | Issued unused unexpired link changes its synthetic account password. |
| REQ-006 | TASK-006, TASK-007, TASK-011 | One-use token, no replay password change. |
| REQ-007 | TASK-006, TASK-007, TASK-011 | Valid strictly before, invalid at/after exact 30-minute expiry. |
| REQ-008 | TASK-003, TASK-008, TASK-011 | All previously active account sessions signed out on success. |
| REQ-009 | TASK-009, TASK-011 | One owner notification for *each* successful reset. |
| REQ-010 | TASK-001, TASK-002, TASK-003, TASK-004, TASK-006 | Python 3.12, Flask and server-rendered pages. |
| REQ-011 | TASK-001, TASK-003, TASK-005, TASK-009 | Synthetic accounts and in-memory notification sink. |
| REQ-012 | TASK-010, TASK-011 | Automated pytest covering REQ-001–REQ-009, including boundaries. |
| REQ-013 | TASK-012 | Document production limitations without production-readiness claim. |
| REQ-014 | TASK-012 | No deployment or new deployment workflow. |

**`coverage_dispositions`: `[]`.** All fourteen approved predecessor requirement IDs have at least one implementing or explicit verification slice; none is silently left out or assigned a “not implemented” exception. TASK-001 through TASK-012 are unique and contiguous. Every `depends_on` reference points to an earlier TASK ID; there are no forward edges or cycles. The proposed final verification is pytest under Python 3.12 plus source/coverage and no-deployment review; this draft makes no claim that any gate has run.

## Open choices carried forward (not additional requirements)

- Confirm whether minimal synthetic sign-in or test-established sessions are preferred for exercising all-session revocation; the proposed TASK-003 mechanism is not a full sign-in policy.
- Confirm whether the image examples are placeholders/hints, and desired responsive fidelity; only the pictured labels, examples, ordering and relative placement are observed.
- Confirm local-only link inspection convention, the chosen rolling-window/nonexistent-key counting policy, password-validation rule and recovery-page copy. None may weaken identical existing/nonexistent public responses, the five-per-account-per-hour ceiling, strict 30-minute single use, all-session sign-out or notification after every success.

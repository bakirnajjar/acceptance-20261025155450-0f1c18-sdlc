# T001 working coverage map — test case design

This is a **prospective mapping**, not the final test-case contract or evidence that an application, tests, or deployment exist. The 14 approved `requirements_analysis` identifiers have **18 acceptance criteria** (ACs). Each AC below has a proposed observable check and existing `solution_design` TASK identifier(s). The `ui_analysis` predecessor distinguishes the **image-observed sign-in presentation** from **proposed** navigation, recovery pages, and behavior. `solution_design.coverage_dispositions` is empty; there is no justified untestable criterion or uncovered AC.

## Authorized evidence and traceability

- **S** — `source_type: user_story`, `source_id: user_story`, `locator: characters 0-16000`. Scope, technology, synthetic accounts, in-memory notification sink, tests, documentation and non-deployment.
- **I** — `source_type: attachment`, `source_id: c2d1eadb-60f9-4b3e-a07e-956604ee291e`, `locator: sign-in-wireframe.png`. White page, centered outlined sign-in card, bold heading, labeled email and password fields, `name@example.com` and masked `********` examples, blue underlined recovery link, dark full-width button and gray administrator text. **Only presentation is observed**; no authenticated behavior, form-value state or recovery screen is evidenced by the image.
- **K** — `source_type: knowledge`, `source_id: 4d3e7857-9fa5-49cc-a86a-33bcf67fabee`, `locator: v1, chunk 0`. Current-run account recovery standard: identical existing/nonexistent reset-request responses, five requests per account per hour, single-use links expiring 30 minutes after issuance, all-session sign-out and owner notification after each successful reset. Other similarly named libraries are not used.
- Approved predecessor names `requirements_analysis`, `ui_analysis` and `solution_design` establish the REQ/TASK identifiers and proposed design decisions. Their stage-output reads supplied **no citable source_reference locator**; these names are traceability labels, not invented citations. In particular, a rolling 3600-second window, a private link outbox, an injected UTC clock, minimal synthetic sign-in and specific routes are **solution-design proposals**, not wireframe observations or externally specified implementation facts.

## Criterion-by-criterion map

Each `TC-*` is a **candidate scenario ID** for the next task. The italicized criterion text reproduces the approved requirement AC; the check states proposed preconditions/data, action and expected observable result. A check's evidence column refers to the exact source-reference triples above, not to an unsupported stage-output citation.

### REQ-001 — observed sign-in presentation

1. **AC 1:** *Given a visitor opens the sign-in page, when it renders, then a bordered card shows a 'Sign in' heading, labeled 'Email address' and 'Password' inputs, a 'name@example.com' email hint and a masked password example.* **Tasks:** TASK-002, TASK-010 (TASK-001 supplies server rendering). **TC-001:** With a fresh client GET the sign-in page; inspect rendered HTML and accessible field labels. Expect one centered outlined sign-in card on a white page, the two labeled inputs and shown examples; neither example is asserted to be a populated credential. **Evidence:** S, I. The card/wording are image-observed; markup and hint implementation are proposed checks, not an authentication requirement.
2. **AC 2:** *Given the rendered sign-in card, when the visitor views its controls, then 'Forgot password?' appears beneath the password field, a dark 'Sign in' button appears below it, and 'No account? Contact your administrator.' appears beneath the button.* **Tasks:** TASK-002, TASK-010. **TC-002:** Inspect the rendered sign-in view and relative DOM/visible order: Password → blue underlined Forgot password? → dark full-width Sign in → gray administrator sentence. Expect exact observed wording and order; do not assert unsupported pixels or responsive breakpoints. **Evidence:** S, I. This is image-observed presentation, not proof the button signs anyone in.

### REQ-002 — entry to reset request

3. **AC 1:** *Given the sign-in page, when a visitor activates 'Forgot password?', then the visitor can start a password-reset request.* **Tasks:** TASK-002, TASK-004, TASK-010. **TC-003:** From fresh sign-in page activate the link with keyboard or client navigation; expect a server-rendered, labeled address-entry reset-request form with an operable submit action. The link's appearance is observed (I); its destination/form are proposed under S, K and approved `ui_analysis`, not shown in the image. **Evidence:** S, I, K.

### REQ-003 — account-existence response parity

4. **AC 1:** *Given otherwise equivalent reset requests for an existing synthetic account and a nonexistent account, when each request is submitted, then their responses are identical and do not disclose account existence.* **Tasks:** TASK-004, TASK-005, TASK-010. **TC-004:** Initialize equivalent fresh client/CSRF state; submit syntactically valid, differently normalized existing and nonexistent addresses under matching conditions. Compare public status, redirect Location, destination body, account-dependent headers and cookies, and absence of addresses/tokens, not just message text. Expect the same neutral public response; inspect private outbox separately, never as a public channel. **Evidence:** K. Repeat at the throttle boundary in TC-019.

### REQ-004 — five requests per account per hour

5. **AC 1:** *Given a synthetic account has received five reset requests within an hour, when a sixth request for that account is attempted within that hour, then no additional reset request for that account is honored.* **Tasks:** TASK-005, TASK-010. **TC-005:** Fix injected UTC time `t0`; send five eligible requests for the same normalized synthetic account, then a sixth at `t0+3599s`. Expect the sixth creates no additional private link/issuance, while the public response remains neutral and matches the first five. **Evidence:** K. The injected clock and rolling-window arithmetic are approved design choices.
6. **AC 2:** *Given the same account has received fewer than five reset requests within an hour, when an eligible request is made, then the five-per-account-per-hour limit does not prevent that request.* **Tasks:** TASK-005, TASK-010. **TC-006:** In an isolated store, check first and fifth requests for one account are honored (five distinct private links total); after the sixth is suppressed, advance the proposed rolling clock to exactly `t0+3600s` and expect the next eligible request is honored without any changed public confirmation. **Evidence:** K. The exact oldest-timestamp boundary tests the design's chosen policy, not an externally imposed window algorithm.

### REQ-005 — usable valid link

7. **AC 1:** *Given an issued, unused reset link for a synthetic account before its expiry, when the holder completes a password reset using the link, then that account's password changes.* **Tasks:** TASK-005, TASK-006, TASK-007, TASK-011. **TC-007:** Issue a link privately for account A, open it before expiry, submit CSRF-valid new password meeting the implementation's **documented** minimal rule. Expect success only after commit: A's hash changes, old credential fails and new credential works in the synthetic sign-in demonstration; account B's password remains unchanged. Do not infer a complexity rule or an external delivery mechanism. **Evidence:** S, K.

### REQ-006 — single use

8. **AC 1:** *Given a reset link has already completed a successful reset, when someone attempts another reset with that same link, then it cannot complete another password change.* **Tasks:** TASK-006, TASK-007, TASK-011. **TC-008:** Successfully redeem a link, then GET and POST it again with an otherwise valid different password. Expect a non-success/retry path, no second password mutation and no second successful-reset notice; the first password change persists. Add concurrent replay in TC-022. **Evidence:** K.

### REQ-007 — 30-minute expiry

9. **AC 1:** *Given an issued, unused reset link and an otherwise valid password change, when the change is submitted and completed before 30 minutes have elapsed from the link's issue time, then the link permits the password change.* **Tasks:** TASK-006, TASK-007, TASK-011. **TC-009:** With fake aware UTC clock, issue an unused link at `t0`, submit a valid change at `t0+30m−1µs`; expect one committed password change and success. Observe password state, not merely a success page. **Evidence:** K.
10. **AC 2:** *Given an issued reset link, when a password change is attempted at or after 30 minutes from its issue time, then the link cannot complete the password change.* **Tasks:** TASK-006, TASK-007, TASK-011. **TC-010:** Use separate unused links at `t0+30m` and `t0+30m+1µs`; also GET a valid form before expiry but POST it at exactly expiry. Expect no committed change, success claim or notice; GET at expiry offers a new-request path, and POST rechecks expiry instead of trusting the earlier GET. **Evidence:** K. The form/retry view is proposed, not image-observed.

### REQ-008 — account-wide session revocation

11. **AC 1:** *Given a synthetic account has active sessions, when its password reset completes successfully, then none of the previously active sessions remains signed in.* **Tasks:** TASK-003, TASK-008, TASK-011. **TC-011:** Establish two separately signed-in clients for account A plus one for B; reset A successfully, then request a guarded page from all three. Expect both previously active A clients rejected/cleared and B still authorized; check a copied but stale signed cookie cannot bypass the version guard. Failed/replayed/expired resets must not revoke A. **Evidence:** K. The demonstration sign-in/guard are design proposals, not pictured authentication behavior.

### REQ-009 — per-success owner notices

12. **AC 1:** *Given a synthetic account's password reset completes successfully, when the result is inspected, then a notification for that account's owner is recorded in the in-memory notification sink for that successful reset.* **Tasks:** TASK-009, TASK-011 (TASK-007/008 contribute the success transition). **TC-012:** Start with empty sink; successfully reset A once and inspect the separate process-local notice sink. Expect exactly one owner-addressed entry for A and no claim of external delivery. **Evidence:** S, K.
13. **AC 2:** *Given multiple successful resets, when the sink is inspected, then each successful reset has an owner notification.* **Tasks:** TASK-009, TASK-011. **TC-013:** Reset A with two different valid links in sequence (request a fresh link after the first success). Expect two distinguishable owner-directed sink entries, one for each committed success, and no extra entries from rejected attempts. **Evidence:** S, K.

### REQ-010 — implementation stack

14. **AC 1:** *Given the application implementation, when its runtime, framework and user-facing pages are inspected, then it targets Python 3.12, uses Flask and renders the pages on the server.* **Tasks:** TASK-001, TASK-002, TASK-004, TASK-006 (TASK-003/007 supply additional routes). **TC-014:** Inspect runtime/dependency metadata, run the app under Python 3.12 when supplied, and request sign-in and proposed recovery pages with a Flask test client. Expect Flask/Jinja-rendered HTML in responses, not a client-only app; this is a future verification, not a claim of existing code. **Evidence:** S.

### REQ-011 — synthetic, in-memory boundaries

15. **AC 1:** *Given the application is exercised, when account data and recorded owner notifications are inspected, then the accounts are synthetic and notifications are captured in an in-memory sink rather than sent through an external notification service.* **Tasks:** TASK-001, TASK-003, TASK-005, TASK-009. **TC-015:** Inspect fixtures, app wiring, and two isolated app instances; issue and redeem a link in one instance. Expect only synthetic fixture accounts and process-local outbox/notice sink, no external delivery call, with counters/tokens/notices not shared across instances. **Evidence:** S. App-instance isolation and a separate link outbox are approved design proposals.

### REQ-012 — automated pytest coverage

16. **AC 1:** *Given the project test suite, when pytest is run, then automated checks cover the sign-in presentation, reset initiation and response parity, the five-per-account-per-hour limit, successful reset, single-use and 30-minute expiry boundaries, session sign-out, and notification after each successful reset.* **Tasks:** TASK-010, TASK-011. **TC-016:** Once code/test suite exists, enumerate collected pytest cases against TC-001–TC-013 and TC-019–TC-025 as applicable; execute under Python 3.12. Expect automated assertions for each specifically listed behavior and a recorded pytest outcome; this map **does not assert tests have been run or passed**. **Evidence:** S, K.

### REQ-013 — production limitations

17. **AC 1:** *Given the project documentation, when it is reviewed, then it identifies production limitations of using synthetic accounts and in-memory state or notifications without asserting that this demonstration is production-ready.* **Tasks:** TASK-012. **TC-017:** Review project documentation for synthetic-only identity, volatile accounts/counters/tokens/session versions/outbox/sink, restart/multi-worker behavior, lack of real delivery and incomplete production security. Expect an explicit non-production limitation statement and local test instructions, not production-ready claims. **Evidence:** S.

### REQ-014 — no deployment

18. **AC 1:** *Given the project deliverables, when they are inspected, then no deployment has been performed and no deployment workflow has been added.* **Tasks:** TASK-012. **TC-018:** Inspect the bounded project deliverable diff/tree and available execution record for new deployment workflows, deployment configuration, hosted URLs and deploy commands. Expect none within reviewed scope; running locally or under pytest is not deployment. A repository/record check **cannot prove a universal absence of deployments outside the available evidence**; flag any inaccessible records instead of asserting global non-deployment. **Evidence:** S.

## Additional negative, security, boundary and accessibility checks

These proposed scenarios strengthen the above AC mappings; they do not add new requirements or claim unobserved UI is pictured.

| Candidate | Links | Proposed preconditions, action and expected result | Evidence |
| --- | --- | --- | --- |
| **TC-019** | REQ-003/004; TASK-004/005/010 | Compare valid existing and nonexistent normalized address requests at under-limit and throttled states, with equivalent CSRF/client state. Public status, Location, destination, account-dependent headers/cookies and neutral content stay identical; private outbox gains no link for nonexistent or throttled keys. | K |
| **TC-020** | REQ-002/003/005; TASK-002/004/007/010/011 | Submit empty/malformed reset address and missing/invalid CSRF, and empty/invalid new password (according to the eventual documented rule). Expect field-associated accessible errors for invalid data, rejection of untrusted CSRF requests, and no link/password mutation, notice or account-existence leak. Do not invent a password-complexity threshold. | S, K |
| **TC-021** | REQ-004; TASK-001/005/010 | Send concurrent eligible requests around the fifth/sixth boundary for one normalized key. Inspect locked state/outbox: at most five links are honored in the design's 3600-second window; public responses do not distinguish the winner. | K |
| **TC-022** | REQ-005/006/007/009; TASK-007/009/011 | Submit two concurrent valid POSTs using one unused link before expiry. Expect at most one success, one password change and one notice; the losing attempt cannot claim success or mutate the final password. | S, K |
| **TC-023** | REQ-005/008/009; TASK-007/008/009/011 | Inject an in-process notification-sink failure during an otherwise valid reset; inspect hash, token, session version, sink and public result. Expect rollback/abort without success claim or an inconsistent committed reset; no owner session is revoked by a failed transition. This is a design integrity check, not a promise of durable transactions. | S, K |
| **TC-024** | REQ-001/002/003/005/006/007; TASK-002/004/006/007/010/011 | Keyboard-only and accessibility inspection for sign-in and **proposed** reset-request, confirmation, new-password, success and unusable-link states. Expect logical focus/activation, programmatic labels, discernible button/link names, readable contrast, field-associated errors and announced outcomes; do not claim these properties are proven by the image. | S, I, K |
| **TC-025** | REQ-003/005/006/007/011; TASK-001/004/005/006/007/011 | Exercise unknown, used and expired bearer-token URLs and inspect responses, cookies, ordinary logs and page content. Expect no password mutation or success, no public issued-link disclosure; proposed token pages have no-store/no-referrer policies and no third-party assets. Private outbox is test-only and does not prove delivery. | S, K |

## Manual completeness and evidence limits

- **14/14 REQ identifiers; 18/18 distinct requirement ACs** explicitly enumerated above (REQ-001: 2; 002: 1; 003: 1; 004: 2; 005: 1; 006: 1; 007: 2; 008: 1; 009: 2; 010–014: 1 each). **25 proposed check IDs**: 18 primary criterion checks plus 7 supplementary checks. **12/12 approved TASK IDs** appear in mapping. No missing or formally untestable AC; no coverage disposition is proposed because each has an observable prospective check.
- The standard fixes a limit but not rolling versus fixed windows, nonexistent-key accounting or throttle copy. The design-selected rolling 3600-second boundary/private counters are tested as **design proposals**; public account-existence parity remains mandatory.
- The exact password rule, recovery-screen copy, link inspection UX, responsive measures and full sign-in policy are not specified. Resolve these choices in implementation/documentation rather than turning them into invented image facts. The sign-in examples are presentation examples, not verified input state.
- There is no supplied implementation, test result, actual notification delivery, production security assessment or global deployment audit. Tests are **proposed**, and evidence for REQ-014 is inherently bounded by reviewed deliverables and available execution records.

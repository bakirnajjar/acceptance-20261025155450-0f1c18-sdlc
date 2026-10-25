# Proposed password-reset test cases

**Status:** design only. None of these tests is claimed to have run or passed. The JSON contract is [`test_case_design.json`](test_case_design.json); the IDs, links, steps and expected results below correspond to its `test_cases` entries. The only observed screen is the sign-in wireframe; recovery screens, routes, synthetic sign-in, private outbox and atomic store are approved **design proposals**, not image observations or evidence of implementation.

## Evidence and working conventions

| Key | Exact source reference | Scope |
| --- | --- | --- |
| S | `source_type: user_story`; `source_id: user_story`; `locator: characters 0-16000` | Python 3.12, Flask/server rendering, synthetic accounts, in-memory notification sink, pytest, limitations, no deployment. |
| I | `source_type: attachment`; `source_id: c2d1eadb-60f9-4b3e-a07e-956604ee291e`; `locator: sign-in-wireframe.png` | Sign-in card appearance and link only; not field state, behavior or recovery pages. |
| K | `source_type: knowledge`; `source_id: 4d3e7857-9fa5-49cc-a86a-33bcf67fabee`; `locator: v1, chunk 0` | ACC-STD-01–03: response parity, five requests per account per hour, single-use/30-minute link, all-session sign-out, per-success owner notice. |

REQ-001–REQ-014 and TASK-001–TASK-012 are approved predecessor identifiers, not citations: authorized prior-stage reads supplied **no citable `stage_output` locator**, so none is invented. Case-level evidence keys expand to exactly the source triples above. The other similarly named knowledge libraries are not used.

Unless overridden in a case, use a fresh isolated proposed app/store and aware injected UTC clock `t0 = 2026-01-01T12:00:00Z`; synthetic A = `owner@example.test`, B = `peer@example.test`, absent N = `absent@example.test`. Use independent cookie jars for independent clients and obtain valid per-client form CSRF before authorized POSTs. `P_old`, `P_new1`, `P_new2`, `P_new3` are distinct fixture passwords chosen to meet the eventual **documented** minimal rule; `P_invalid` is rejected by that rule. Snapshot private hashes, versions, tokens, counters, link outbox and **distinct** notification sink before testing mutations. Issued links are inspected only through a private test outbox, not public responses and not real delivery. Reset each scenario's fixtures except for consecutive steps inside that scenario. The exact rolling 3600-second rule, private nonexistent-key accounting, synthetic sign-in, guarded page and process-local rollback are approved design choices, not requirements read from the image or a claim of production security.

## Primary acceptance-criterion cases

### TC-001 — Observed sign-in card and examples
**Links:** REQ-001 AC1; TASK-001, TASK-002, TASK-010. **Evidence:** S, I.

**Steps**
1. Preconditions/data: fresh unauthenticated client; no entered credentials. GET the proposed `/` sign-in page.
2. Inspect the visible card, rendered HTML, label/input associations, field types, displayed examples and initial input values.

**Expected results**
1. One centered outlined sign-in card on a white page has a bold Sign in heading, programmatically labeled Email address and Password fields, a visible `name@example.com` example and a masked `********` example.
2. Examples are presentation hints, not populated credentials: initial inputs are empty and no plaintext password example is exposed. No exact dimensions or sign-in behavior are inferred.

### TC-002 — Observed sign-in control order
**Links:** REQ-001 AC2; TASK-002, TASK-010. **Evidence:** S, I.

**Steps**
1. Preconditions/data: fresh unauthenticated client; GET the proposed `/` page.
2. Inspect visual and DOM order of Password, recovery link, submit button and administrator sentence; check their relative visual treatment without pixel measurements.

**Expected results**
1. A blue underlined `Forgot password?` link follows Password; a dark full-width `Sign in` button follows the link; gray `No account? Contact your administrator.` appears beneath the button.
2. Wording and order match the image; button presence does not establish an authentication policy.

### TC-003 — Start reset request from recovery link
**Links:** REQ-002 AC1; TASK-002, TASK-004, TASK-010. **Evidence:** S, I, K.

**Steps**
1. Preconditions/data: fresh unsigned-in client on the sign-in page; focus its `Forgot password?` link with Tab.
2. Activate the link with Enter and inspect the proposed `/forgot-password` destination, address field, submit action and focus order.

**Expected results**
1. The link opens a server-rendered reset-request form with a programmatically labeled editable address field and operable submit control rather than a dead end.
2. Focus order reaches the address and submit controls. Only the originating link is image-observed; its destination is proposed.

### TC-004 — Existing and nonexistent request response parity
**Links:** REQ-003 AC1; TASK-004, TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: separate matched fresh stores and clients at fixed UTC `t0 = 2026-01-01T12:00:00Z`, with zero request history; synthetic A `owner@example.test` and absent N `absent@example.test`. Match headers, valid per-client CSRF and pre-POST cookie state; use syntactically valid differently normalized addresses.
2. Submit A and N independently at the same fixed time. Record public status, Location, response body, account-dependent headers/cookies, and followed redirect destination; repeat with execution order and client assignment swapped on new matched fixtures.
3. Inspect each private outbox separately from public responses.

**Expected results**
1. For every matched pair, public status, Location, destination status/body and account-dependent headers/cookies are identical; no address or bearer token is echoed. Compare equivalent CSRF cookie attributes rather than unrelated random bytes.
2. Only A obtains a private owner-directed link. Clock advancement, previous cookie state, throttling history and run order cannot explain any public difference.

### TC-005 — Suppress the sixth request within an hour
**Links:** REQ-004 AC1; TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh synthetic A `owner@example.test`, empty private outbox/counter, injected aware UTC `t0 = 2026-01-01T12:00:00Z` and a CSRF-valid client.
2. Submit five eligible requests for A's normalized key at t0, refreshing CSRF if required; record public responses and private link count.
3. At t0 + 3599 seconds submit a sixth and inspect outbox, honored-issuance count and public response.

**Expected results**
1. The first five requests produce five distinct private A links; the sixth adds no link and is not honored.
2. The sixth has the same neutral valid-request public status, redirect, destination and account-dependent headers/cookies as the first five; throttle state is not exposed.

### TC-006 — First, fifth and rolling-hour boundary requests
**Links:** REQ-004 AC2; TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh A store, empty history, injected UTC `t0 = 2026-01-01T12:00:00Z`, valid CSRF per request. Submit one A request and four more at t0.
2. Inspect private outbox after first and fifth; attempt sixth at t0 + 3599 seconds and another exactly t0 + 3600 seconds.
3. Compare public responses for first, fifth, suppressed sixth and boundary request.

**Expected results**
1. One then five distinct private links exist after first and fifth; the sixth adds none. At the proposed rolling boundary, timestamps `<= t - 3600 seconds` age out and the next eligible request adds a link.
2. All syntactically valid public responses remain the same neutral response. Exact oldest-timestamp arithmetic is a design choice, not a standard-mandated window algorithm.

### TC-007 — Valid link changes only owner password
**Links:** REQ-005 AC1; TASK-005, TASK-006, TASK-007, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh synthetic A `owner@example.test` and B `peer@example.test` with separate P_old fixture hashes at UTC t0; privately issue an unused A link. Select distinct P_new1 satisfying the documented minimal password rule.
2. Before t0 + 30 minutes, GET the private link using a new client, obtain valid form CSRF and POST P_new1.
3. Inspect A/B hashes and attempt synthetic sign-in for A with P_old and P_new1 and B with its original credential.

**Expected results**
1. Success is reported only after commit: A's hash changes, A's old credential fails and P_new1 succeeds in the proposed demonstration.
2. B's hash and credential remain unchanged. Private link inspection and synthetic sign-in do not imply external delivery or a production authentication policy.

### TC-008 — Consumed link cannot change password again
**Links:** REQ-006 AC1; TASK-006, TASK-007, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh A link at t0, clock before expiry; choose distinct documented-valid P_new1 and P_new2, valid CSRF and empty owner-notice sink.
2. Redeem the link with P_new1, recording hash, session version and notice count; GET and CSRF-valid POST the same link again with P_new2.
3. Inspect non-success view, hash, version, notices and the effective credential.

**Expected results**
1. Second GET offers no usable password form but a new-request path; second POST cannot report success.
2. Replay does not change hash or session version and adds no notice; P_new1 remains effective. Concurrent replay is separately checked in TC-022.

### TC-009 — Link valid at last instant before expiry
**Links:** REQ-007 AC1; TASK-006, TASK-007, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: isolated unused A link issued at aware UTC `t0 = 2026-01-01T12:00:00Z`, documented-valid P_new1 and valid form CSRF obtained before expiry.
2. At t0 + 30 minutes - 1 microsecond POST P_new1 and inspect result, A hash and proposed synthetic old/new sign-in behavior.

**Expected results**
1. The proposed strict `now < issue + 30 minutes` check accepts the unused link; exactly one password change commits.
2. A changed hash and old-password rejection/new-password acceptance corroborate the success; success text alone is insufficient.

### TC-010 — Exact expiry and valid GET followed by expired POST
**Links:** REQ-007 AC2; TASK-006, TASK-007, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: three separate fresh unused A links issued at UTC t0, documented-valid P_new1, valid per-client CSRF; snapshot hash, token state, session version and notices.
2. In store 1 GET and POST at t0 + 30 minutes; in store 2 POST at t0 + 30 minutes + 1 microsecond; in store 3 GET the valid form at t0 + 29 minutes and POST with its CSRF at exactly t0 + 30 minutes.
3. Inspect each response and private state.

**Expected results**
1. No case commits a password change, successfully consumes the token, bumps the session version, records a notice or claims success.
2. Expiry-time GET offers a recoverable new-request path; a prior valid GET does not authorize an expired POST, which rechecks time at commit.

### TC-011 — Revoke all owner sessions but not another account
**Links:** REQ-008 AC1; TASK-003, TASK-008, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: via proposed synthetic sign-in, independently authenticate A on clients A1 and A2 and B on B1; confirm initial guarded access, save A1's signed cookie and snapshot versions.
2. Using a separate client, issue and successfully redeem A's unused link before expiry with valid CSRF and documented-valid P_new1.
3. Request the guarded page with A1, A2, B1 and a fresh jar containing A1's stale cookie; separately inspect A's version and check failed, expired and replayed resets against an otherwise valid A session.

**Expected results**
1. A's version increments once and both previous A clients plus the copied signed cookie are unauthenticated on their next guarded request; B1 stays authorized and B's version is unchanged.
2. Failed, expired or replayed resets do not revoke a valid A session; a valid cookie signature does not bypass the account-version guard.

### TC-012 — Exactly one owner notice for a successful reset
**Links:** REQ-009 AC1; TASK-007, TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh A/B fixtures and empty distinct in-memory owner-notification sink; obtain one unused A link from the private outbox, valid form CSRF and documented-valid P_new1.
2. Reset A before expiry; inspect committed hash and process-local notice sink independently of the public response.

**Expected results**
1. Exactly one owner-addressed A notice corresponds to the committed A reset; none is for B and there are no extra entries.
2. Public success follows commit. A local sink entry is not real, durable or externally delivered notification.

### TC-013 — One separate notice for each of two successes
**Links:** REQ-009 AC2; TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh A and empty sink; choose distinct documented-valid P_new1 and P_new2, separate valid CSRF and clock before expiry of each link.
2. Issue A link L1 and reset with P_new1; issue fresh L2 after success and reset with P_new2; inspect the sink after each commit.
3. Replay consumed L1 and inspect sink again.

**Expected results**
1. After first success there is one A-owner record; after second there are two distinct records for the two committed resets.
2. Replaying L1 produces no third notice or success. Only the local sink, not external delivery, is verified.

### TC-014 — Python 3.12 Flask server-rendered pages
**Links:** REQ-010 AC1; TASK-001, TASK-002, TASK-004, TASK-006. **Evidence:** S.

**Steps**
1. Preconditions/data: once implementation artifacts exist, inspect runtime/dependency metadata and proposed Flask app factory/Jinja templates; prepare local Python 3.12 without deploying.
2. Under Python 3.12 use a Flask test client to request sign-in, reset-request and usable/unusable proposed link pages; inspect content types, response HTML and template-rendering path.

**Expected results**
1. Runtime metadata targets Python 3.12, Flask is the framework and requested user-facing pages return server-rendered HTML containing the relevant forms/states, not client-only rendering.
2. Unavailable Python 3.12 or missing artifacts is a validation problem, not a pass or a reason to deploy.

### TC-015 — Synthetic accounts and process-local notification sink
**Links:** REQ-011 AC1; TASK-001, TASK-003, TASK-005, TASK-009. **Evidence:** S.

**Steps**
1. Preconditions/data: inspect fixture sources and integrations; create two independent proposed app instances with synthetic A/B fixtures and empty private outboxes and distinct notice sinks at fixed UTC t0.
2. In instance 1 privately issue and redeem an A link; compare both instances' accounts, counters, token records, outboxes, versions and sinks.
3. Inspect integrations for real identity lookup, external notification service or persistent account/notification backend.

**Expected results**
1. Only synthetic fixtures are used; the owner notice exists in instance 1's separate in-memory sink, not instance 2's. Links, counters, token, version and password mutations do not cross instances.
2. No external notification service is invoked; a private test link outbox is distinct from the notice sink and proves neither durability nor delivery.

### TC-016 — Collect and run automated pytest coverage
**Links:** REQ-012 AC1; TASK-010, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: only after implementation and tests exist, under Python 3.12 collect pytest cases, inspect assertions and map each required behavior to test names.
2. Run pytest locally; record command, environment, collection and actual pass/fail/skip/blocked outcome for each targeted behavior group.

**Expected results**
1. Automated assertions cover sign-in presentation, reset entry, existing/nonexistent and throttled parity, first/fifth/sixth/hour boundary, successful reset, single-use/replay, just-before and exact 30-minute expiry, all-session sign-out and an owner notice after each success.
2. Collection alone is not a pass; missing, skipped or failing assertions remain reported gaps. This proposed case does not assert pytest has run or passed.

### TC-017 — Document synthetic prototype production limitations
**Links:** REQ-013 AC1; TASK-012. **Evidence:** S.

**Steps**
1. Preconditions/data: once project documentation exists, inspect README, local run/test instructions and all production-readiness claims.
2. Check for synthetic-only identities, volatile process-local accounts/counters/tokens/session versions/link outbox/notice sink, restart/multi-worker divergence, lack of real delivery and incomplete production security.

**Expected results**
1. Documentation explicitly identifies synthetic and in-memory limitations, gives local/test instructions, and does not claim production readiness or durable/external delivery.
2. Absent documentation or an unqualified production-ready claim fails this future review; the checklist is not a production security certification.

### TC-018 — Bounded no-deployment review
**Links:** REQ-014 AC1; TASK-012. **Evidence:** S.

**Steps**
1. Preconditions/data: obtain final bounded project tree/diff and available execution/delivery records; do not deploy, trigger workflows or contact a hosted environment.
2. Inspect added workflows, deployment scripts/configuration, hosted endpoints and deploy commands; distinguish local Flask execution or pytest from deployment. Record reviewed paths/records and inaccessible environments.

**Expected results**
1. No deployment workflow or performed deployment is found within the inspected deliverables and available records; flag any deployment-related addition.
2. Inspection cannot prove absence of deployments outside those records; missing external evidence is a stated limit, never a global non-deployment claim.

## Supplementary negative, concurrency, security and accessibility cases

### TC-019 — Parity under limit and throttling with normalized keys
**Links:** REQ-003, REQ-004; TASK-004, TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: for each comparison use separate matched stores and independent clients with equivalent valid CSRF/headers/cookie state; fix UTC t0 and seed normalized existing A `owner@example.test` and absent N `absent@example.test` keys with equal private counts of zero, four or five at t0. Use mixed-case/whitespace variants normalized to baseline keys.
2. At counts zero and four submit one valid request per key at t0; at five submit one per key at t0 + 3599 seconds. Follow redirects; repeat each pair with order and client assignment swapped on fresh matched stores.
3. Compare public status, Location, confirmation body and account-dependent headers/cookies; inspect private counts/outboxes separately.

**Expected results**
1. For every matched A/N pair, account-dependent public surfaces are indistinguishable below and at the ceiling; they disclose neither account existence nor issuance. CSRF randomness, wall time and run order cannot explain differences.
2. Eligible A alone gets a private link; N never does; neither suppressed key gets a link. Proposed private normalized-key accounting cannot be bypassed by case/whitespace variants.

### TC-020 — Invalid address, password and CSRF rejection
**Links:** REQ-002, REQ-003, REQ-005; TASK-002, TASK-004, TASK-007, TASK-010, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh matched A/N stores and CSRF-capable clients; snapshot counters, outbox, A hash, token state, version and notice sink. Choose empty/malformed address, empty password and P_invalid rejected by the eventual documented rule.
2. Submit empty/malformed address for A/N-equivalent paths, comparing feedback within each input class; submit an otherwise valid request with missing or invalid CSRF on fresh clients.
3. Obtain an unused A link privately; POST empty/P_invalid passwords with valid CSRF and a documented-valid password with missing/invalid CSRF; inspect responses and captured state.

**Expected results**
1. Invalid addresses have readable field-associated, account-independent feedback; untrusted CSRF requests are rejected without issuing a link. No particular invalid-input HTTP status or equality between different invalid-value classes is prescribed.
2. Invalid passwords have field-associated feedback; rejected request/reset inputs do not change hash, consume token, bump session version, record notice or claim success.

### TC-021 — Concurrent fifth/sixth issuance ceiling
**Links:** REQ-004; TASK-001, TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh A with four honored links at fixed UTC t0, two independent CSRF-valid clients and synchronized test barrier; hold clock at t0 + 1 second.
2. Release two concurrent valid requests for normalized A (one mixed-case variant); inspect both public responses and locked private count/outbox.

**Expected results**
1. Exactly one additional link is issued, totaling five; no interleaving permits six or duplicate issuance.
2. Both public responses are indistinguishable on account-dependent surfaces and reveal neither winner nor throttle state.

### TC-022 — Concurrent redemption commits at most once
**Links:** REQ-005, REQ-006, REQ-007, REQ-009; TASK-007, TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh unused A link at t0, clock held at t0 + 1 minute; two clients with independent valid CSRF and distinct documented-valid P_new1/P_new2; snapshot A hash/version and empty notice sink.
2. Release simultaneous POSTs to the same token using a barrier; compare responses, final hash, consumed token, session version and notices.

**Expected results**
1. Exactly one POST commits and may claim success; the loser cannot report success or overwrite the winner's password, whose chosen credential alone authenticates.
2. The token is consumed once, A's version changes once and exactly one A-owner notice is appended; fixed time excludes expiry as the cause.

### TC-023 — Notification failure rolls back process-local reset
**Links:** REQ-005, REQ-008, REQ-009; TASK-007, TASK-008, TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh unused A link, two independently active A sessions and one B session, valid CSRF and documented-valid P_new1 before expiry; snapshot hash, token, versions and sink. Inject an in-process sink-append failure, including a variant throwing after partial append.
2. Submit the otherwise valid reset and inspect public result, private state and guarded access from A's two clients and B's client.

**Expected results**
1. No success is claimed and no inconsistent partial success remains: A hash, token usability, A/B versions and sink contents match the pre-call snapshot, including no orphan notice after partial append.
2. A and B sessions retain pre-failure access. This is a proposed process-local rollback check, not a durable distributed-transaction claim.

### TC-024 — Keyboard, labels, errors and announced outcomes
**Links:** REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007; TASK-002, TASK-004, TASK-006, TASK-007, TASK-010, TASK-011. **Evidence:** S, I, K.

**Steps**
1. Preconditions/data: keyboard-only client and accessibility-tree/screen-reader inspection for pictured sign-in and proposed request, confirmation, new-password, success and unusable-link views; arrange empty/invalid inputs and expired link.
2. Tab and keyboard-activate links, submit and retry controls in each view; inspect focus order, visible focus, accessible names/labels and readable contrast.
3. Trigger invalid input and success/non-success transitions; inspect field-error association and whether focus reaches or announces each outcome.

**Expected results**
1. No keyboard trap; implemented views have logical focus order, visible focus, programmatic labels, discernible button/link names and readable contrast.
2. Errors are readable and associated with fields; outcomes are focused or announced; success is never announced before commit and unusable links never announce success. These behaviors and recovery views are proposals, not image-observed facts.

### TC-025 — Unusable tokens and issued-link non-disclosure
**Links:** REQ-003, REQ-005, REQ-006, REQ-007, REQ-011; TASK-001, TASK-004, TASK-005, TASK-006, TASK-007, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: separate fixtures with unknown opaque token, consumed A token and unused A token at t0 + 30 minutes; prepare valid CSRF and documented-valid P_new1 for attempted POSTs and snapshot hashes, versions and sink.
2. GET and POST each token; inspect response, cookies, HTML, ordinary logs, headers and outgoing asset URLs. Independently issue an eligible A link and inspect public request/confirmation and private outbox.
3. Inspect proposed token-page `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, absence of third-party assets and redaction of token path segments in ordinary logs.

**Expected results**
1. Unknown, used and expired token URLs yield recoverable non-success/new-request behavior without password mutation, version bump, notice or success claim. Issued tokens occur only in the private process-local test outbox, not public confirmation, cookies, ordinary logs or page body.
2. Token-page policies and log/asset constraints match approved design proposals; a private outbox proves neither external link delivery nor production-grade confidentiality.

## Acceptance-criterion coverage matrix

The criterion labels below enumerate the **18 approved acceptance criteria**, not extra JSON case properties. Primary tests cover each criterion; supplementary tests strengthen the indicated behavior.

| Requirement | Approved acceptance criterion (condensed without changing meaning) | Primary case | Supplementary cases |
| --- | --- | --- | --- |
| REQ-001 AC1 | Bordered sign-in card, heading, labeled fields and email/masked examples | TC-001 | TC-024 |
| REQ-001 AC2 | Recovery link below Password, dark Sign in button, administrator line | TC-002 | TC-024 |
| REQ-002 AC1 | Activate Forgot password? to start reset request | TC-003 | TC-020, TC-024 |
| REQ-003 AC1 | Identical non-disclosing existing/nonexistent request responses | TC-004 | TC-019, TC-020, TC-024, TC-025 |
| REQ-004 AC1 | Sixth request within hour is not honored after five | TC-005 | TC-019, TC-021 |
| REQ-004 AC2 | Eligible request when fewer than five is not prevented | TC-006 | TC-019, TC-021 |
| REQ-005 AC1 | Valid unused unexpired link changes the owning account's password | TC-007 | TC-020, TC-022, TC-023, TC-024, TC-025 |
| REQ-006 AC1 | Already-used link cannot complete another password change | TC-008 | TC-022, TC-024, TC-025 |
| REQ-007 AC1 | Change completed before 30 minutes is permitted | TC-009 | TC-022, TC-024 |
| REQ-007 AC2 | Change attempted at/after 30 minutes is rejected | TC-010 | TC-024, TC-025 |
| REQ-008 AC1 | Successful reset signs out every active owner session | TC-011 | TC-023 |
| REQ-009 AC1 | Owner notice recorded in in-memory sink for a success | TC-012 | TC-022, TC-023 |
| REQ-009 AC2 | Each of multiple successful resets has an owner notice | TC-013 | TC-022 |
| REQ-010 AC1 | Python 3.12, Flask, server-rendered pages | TC-014 | — |
| REQ-011 AC1 | Synthetic accounts and in-memory, not external, notification sink | TC-015 | TC-025 |
| REQ-012 AC1 | Automated pytest checks cover required sign-in/reset behaviors | TC-016 | — |
| REQ-013 AC1 | Production limits documented without a production-ready claim | TC-017 | — |
| REQ-014 AC1 | No deployment performed or workflow added | TC-018 | — |

**Coverage summary:** 14/14 approved requirements, 18/18 acceptance criteria, 25/25 proposed cases and 12/12 approved TASK identifiers linked. **Uncovered requirements: none. Uncovered criteria: none. Justified untestable dispositions: none** (the approved design's `coverage_dispositions` is empty). This is prospective **design coverage**, not executed test or implementation coverage.

## Nonblocking questions and validation limits

- What exact minimal password rule will be documented? Select valid/invalid test data after that decision, not by inventing a complexity threshold.
- What recovery-page wording, focus/error treatment and local-only link-inspection UX will be chosen? Only sign-in presentation is pictured.
- Is the design-selected rolling 3600-second accounting for nonexistent normalized keys acceptable? Public parity and the five-per-hour ceiling remain mandatory regardless.
- Is any more complete sign-in policy or responsive fidelity required? The proposed synthetic guarded sign-in exists to make account-wide revocation observable, not to claim the wireframe establishes authentication behavior.
- Missing implementation, Python 3.12, pytest assertions/outcomes or delivery records must be reported as **not validated**, never passed. A bounded review cannot establish absence of external deployment outside available records. No actual test execution, external notification, production security assessment or deployment is claimed here.

# T002 — proposed test scenarios

These are **test designs, not executed tests or evidence that software exists**. The approved `requirements_analysis` ACs and `solution_design` TASKs supply traceability; their prior-stage reads returned no citable `stage_output` locator. The wireframe proves sign-in presentation only. Routes, synthetic sign-in, a private outbox, an injected aware UTC clock, digest-indexed tokens, a rolling 3600-second window, account-independent CSRF state, and process-local atomic effects below are **solution-design proposals**, not observed application behavior or additional requirements. Use the implemented and documented minimal password-input rule when selecting a valid test password; no particular complexity threshold is assumed. No actual email, durable storage, production security, or deployment is inferred.

## Evidence key and common data

- **S:** `source_type: user_story`; `source_id: user_story`; `locator: characters 0-16000`.
- **I:** `source_type: attachment`; `source_id: c2d1eadb-60f9-4b3e-a07e-956604ee291e`; `locator: sign-in-wireframe.png`.
- **K:** `source_type: knowledge`; `source_id: 4d3e7857-9fa5-49cc-a86a-33bcf67fabee`; `locator: v1, chunk 0` (the current-run recovery standard, ACC-STD-01–03).

Unless a scenario says otherwise, initialize a **fresh isolated** proposed app/store and aware injected UTC clock at `t0 = 2026-01-01T12:00:00Z`; use synthetic A `owner@example.test`, synthetic B `peer@example.test`, and absent key N `absent@example.test`. Create independent client/cookie jars for independent users; obtain a valid form CSRF token per client before POST. `P_old`, `P_new1`, `P_new2` and `P_new3` mean distinct test passwords selected **after** the implementation documents its minimal valid-input rule; `P_invalid` means a value rejected by that documented rule (empty is always an invalid candidate for the proposed form). Establish the initial A/B fixture hashes from their respective `P_old` fixtures and snapshot hashes, session versions, request counters, private link outbox, and distinct notification sink before mutation. Obtain issued URLs only through the private test outbox, never through a public response. A successful sign-in and a guarded page are proposed test affordances, not behavior established by the image. Each scenario resets its fixture unless it explicitly describes consecutive actions within that scenario. Compare observable HTTP response surfaces after following redirects as well as state in explicitly private test hooks; do not confuse a private outbox with delivery.

## Primary acceptance-criterion scenarios

### TC-001 — observed sign-in card and examples
**Links:** REQ-001 AC1; TASK-001, TASK-002, TASK-010. **Evidence:** S, I.

**Steps**
1. Preconditions/data: fresh unauthenticated client; no account credentials entered; request the proposed `GET /` sign-in page.
2. Inspect rendered HTML and the visible page, including field-label associations, field type, displayed example text and initial input values.

**Expected results**
1. One centered outlined sign-in card on a white canvas has a bold `Sign in` heading, programmatically labeled `Email address` and `Password` inputs, visible `name@example.com` email example and masked `********` password example.
2. The examples are presentation hints rather than populated credentials: initial credential inputs are empty; no password example appears as a real plaintext password. No authentication behavior or exact dimensions are inferred.

### TC-002 — observed sign-in control order
**Links:** REQ-001 AC2; TASK-002, TASK-010. **Evidence:** S, I.

**Steps**
1. Preconditions/data: fresh unauthenticated client and rendered sign-in page from a new `GET /`; inspect visual and DOM reading order.
2. Locate the password input, recovery link, submit button and administrator sentence; inspect relative positioning and basic visual treatment without measuring pixels.

**Expected results**
1. A blue underlined `Forgot password?` link follows the Password field; a dark full-width `Sign in` button follows the link; gray `No account? Contact your administrator.` follows the button.
2. Text and order match the observed image; the presence of the button is not taken as proof of a pictured authentication policy.

### TC-003 — enter the proposed reset-request flow
**Links:** REQ-002 AC1; TASK-002, TASK-004, TASK-010. **Evidence:** S, I, K.

**Steps**
1. Preconditions/data: fresh client at the sign-in page, valid keyboard focus; do not start signed in.
2. Focus `Forgot password?` using keyboard Tab and activate it with Enter; follow the proposed navigation to `GET /forgot-password`.
3. Inspect the destination's address label, editable field, submit action and focus order.

**Expected results**
1. Activation opens a server-rendered reset-request form with a programmatically labeled address field and operable submit control, not a dead link.
2. Focus progresses logically to the request field and submit action. This destination/form is proposed; the image shows only the source link.

### TC-004 — existing versus nonexistent account public parity
**Links:** REQ-003 AC1; TASK-004, TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: prepare two **separate identical fresh** stores/clients (or equivalent state snapshots), one queried for A and the other for N; initialize their CSRF state independently of account lookup to equivalent pre-POST state; pin **each independent clock** to the same `t0`. Neither key has request history. Use syntactically valid, differently normalized address strings; choose matching client state, request headers, and CSRF validity.
2. In each isolated store obtain its form CSRF and submit one address at `t0`; record the first public status, `Location`, response body and account-dependent headers/cookies, then GET each redirect destination using its respective client.
3. Repeat with address-to-client assignment and execution order swapped on fresh identical fixtures, still at the same fixed `t0`; inspect private outboxes separately from public responses.

**Expected results**
1. For each matched pair, public status and `Location`, destination status/body and account-dependent headers/cookies are identical; neither address nor bearer token is echoed. If per-client random CSRF bytes differ, compare equivalent cookie attributes and account-dependent values rather than treating unrelated randomness as an existence difference.
2. Only A obtains a private owner-directed link. No shared clock advancement, previously submitted client cookie, throttling history or run order explains the comparison; a response cannot disclose account existence.

### TC-005 — sixth request suppressed within the hour
**Links:** REQ-004 AC1; TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: new A store, empty private outbox/counter, clock `t0`, one CSRF-valid client; use A's normalized key for all requests.
2. Submit five syntactically valid A reset requests at `t0` (fresh CSRF as needed); record public responses and private outbox size after each.
3. Advance only the injected clock to `t0 + 3599 seconds`; submit the sixth A request; inspect account counter, outbox and public response.

**Expected results**
1. The first five eligible requests produce five distinct private A links; the sixth produces no sixth link and does not count as an honored issuance.
2. The sixth public neutral response has the same valid-request status, redirect, destination and account-dependent headers/cookies as eligible requests; throttle state is not exposed.

### TC-006 — first, fifth and exact rolling-hour boundary
**Links:** REQ-004 AC2; TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh A store, empty history, fixed UTC `t0`, valid CSRF. Submit one A request and then four more at `t0`.
2. Check the private outbox after request 1 and request 5; submit a sixth at `t0 + 3599 seconds`, then advance the injected clock to exactly `t0 + 3600 seconds` and submit one more.
3. Compare the public outcomes of the first, fifth, blocked sixth and boundary request.

**Expected results**
1. The first and fifth requests are honored, yielding one then five distinct private links. The sixth adds none. At the exact proposed rolling-hour boundary, timestamps `<= t - 3600s` age out and another eligible A request adds one private link.
2. Each valid request has the same neutral public response. The exact oldest-timestamp rule is a **solution-design choice**; the standard establishes five per account per hour without prescribing the window algorithm.

### TC-007 — valid link changes only its owner's password
**Links:** REQ-005 AC1; TASK-005, TASK-006, TASK-007, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh A and B with separate original password hashes; clock `t0`; privately issue one unused A link; select `P_new1` satisfying the implementation's documented input rule.
2. Before expiry, GET the private A link using a new client, obtain valid form CSRF and POST `P_new1` while the aware clock remains before `t0 + 30 minutes`.
3. Inspect the persisted in-memory A/B hashes and use proposed synthetic sign-in to try A's old and new credentials.

**Expected results**
1. Only after the successful commit is the result a success state; A's hash changes, A's old credential ceases to authenticate and its new credential authenticates through the proposed demonstration.
2. B's hash and credentials remain unchanged. Neither the outbox nor synthetic sign-in implies real delivery or a production authentication policy.

### TC-008 — consumed link cannot reset twice
**Links:** REQ-006 AC1; TASK-006, TASK-007, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh A link at `t0`, clock held before expiry; valid CSRF and `P_new1`, `P_new2` meeting the documented rule; empty notice sink.
2. Redeem the link with `P_new1` successfully; record hash, session version and one success notice.
3. GET the same link again and attempt a CSRF-valid POST using the same token URL and `P_new2`; inspect public result and private state.

**Expected results**
1. The second GET provides no usable new-password form and offers a path to request another link; the second POST gives no success claim.
2. The second attempt changes no password or session version and adds no notice; `P_new1` remains effective. Concurrent replay is tested separately in TC-022.

### TC-009 — last instant before expiry remains valid
**Links:** REQ-007 AC1; TASK-006, TASK-007, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: isolated A link issued at UTC `t0`, unused; select documented-valid `P_new1`, acquire a valid form CSRF while still before expiry.
2. Set the injected clock to `t0 + 30 minutes - 1 microsecond`; POST the change and inspect the result and A hash.

**Expected results**
1. The strict proposed `now < issue + 30 minutes` check accepts the still-unused link and exactly one password change commits.
2. Success is supported by A's changed hash and the proposed old/new sign-in check, not solely by rendered success text.

### TC-010 — expiry boundary and GET/POST time-of-check
**Links:** REQ-007 AC2; TASK-006, TASK-007, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: prepare **separate unused A links and stores** issued at `t0`, documented-valid `P_new1` and valid CSRF; snapshot hash, token state, session version and notices in each.
2. In store 1, GET at `t0 + 30 minutes` and POST at that instant; in store 2, POST at `t0 + 30 minutes + 1 microsecond`.
3. In store 3, GET a valid form at `t0 + 29 minutes`, retain its CSRF, advance to exactly `t0 + 30 minutes` and POST; inspect each public and private result.

**Expected results**
1. At or after expiry, no password mutation, token consumption as a successful use, version bump, owner notice or success claim occurs in any store.
2. An expiry-time GET gives a recoverable non-success/new-request path. A formerly valid GET does not authorize a later expired POST: commit time is rechecked. The recovery view is proposed, not pictured.

### TC-011 — revoke all owner's active sessions, isolate other account
**Links:** REQ-008 AC1; TASK-003, TASK-008, TASK-011. **Evidence:** K.

**Steps**
1. Preconditions/data: independently sign in A on clients A1 and A2, and B on client B1 using the proposed synthetic flow; verify each guarded request initially succeeds; retain a copy of A1's signed cookie and record A/B versions.
2. Privately issue and redeem A's link from a separate client with documented-valid `P_new1` before expiry.
3. Request the guarded page again from A1, A2 and B1; retry from a new jar containing A1's old signed cookie. Separately check that a failed/expired/replayed attempt does not change A's version.

**Expected results**
1. A's version increments on the successful reset; **both** previously active A clients and the copied stale signed cookie are rejected as unauthenticated on the next guarded request, while B1 remains authorized and B's version stays unchanged.
2. Failure, expiry and replay do not revoke an otherwise valid A session. Cookie signature alone cannot bypass the version guard; sign-out is not just a browser-side cookie action.

### TC-012 — one in-memory owner notice per success
**Links:** REQ-009 AC1; TASK-007, TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh A/B fixtures, empty distinct owner-notification sink, one unused A link from the private outbox, valid CSRF and documented-valid `P_new1`.
2. Reset A before expiry and inspect the committed hash and process-local notification sink independently of the public response.

**Expected results**
1. Exactly one record addressed to A's owner corresponds to the committed A reset; none is addressed to B and no extra notice is created.
2. The public success claim follows the commit. A sink record is **not** evidence of real, durable or external message delivery.

### TC-013 — separate notices for consecutive successful resets
**Links:** REQ-009 AC2; TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh A fixture and empty sink; documented-valid distinct `P_new1` and `P_new2`; clock before expiry of each separately issued link.
2. Issue link L1 for A and successfully reset with `P_new1`; issue a new link L2 after that success and successfully reset with `P_new2`; inspect sink after each commit.
3. Attempt a repeat POST with consumed L1 and inspect sink again.

**Expected results**
1. After success 1 there is one A-owner entry; after success 2 there are two **distinct** entries corresponding to two committed resets.
2. Replaying L1 adds no third notice or success. Only the local sink is inspected; external delivery is not claimed.

### TC-014 — Python 3.12 Flask server rendering
**Links:** REQ-010 AC1; TASK-001, TASK-002, TASK-004, TASK-006. **Evidence:** S.

**Steps**
1. Preconditions/data: when implementation artifacts exist, inspect runtime/dependency metadata and the proposed Flask app factory/Jinja templates; prepare Python 3.12 locally without deploying.
2. Under Python 3.12, use a Flask test client to request sign-in, reset-request and both usable/unusable proposed link pages.
3. Inspect response content type, server-produced HTML and template-rendering path, not merely the presence of JavaScript.

**Expected results**
1. Runtime metadata targets Python 3.12, imports/use identify Flask, and requested user-facing pages arrive as server-rendered HTML with the relevant form/state in the returned response.
2. Failure to provision Python 3.12 or missing artifacts is a **validation problem to report**, not a reason to claim this check passed or to substitute a deployment.

### TC-015 — synthetic fixtures and process-local sinks
**Links:** REQ-011 AC1; TASK-001, TASK-003, TASK-005, TASK-009. **Evidence:** S.

**Steps**
1. Preconditions/data: inspect proposed app wiring, fixture sources and notification integrations; create two independent app instances with synthetic A/B fixtures and empty outbox/sink; freeze their clocks at `t0`.
2. In instance 1 issue and redeem one A link; inspect its accounts, rate counters, token records, outbox, versions and owner-notice sink alongside untouched instance 2.
3. Inspect integrations for external identity lookup, external email/notification delivery and persistent account or notification backends.

**Expected results**
1. Accounts are synthetic fixture data; instance 1 records the owner notice only in its distinct in-memory sink. Instance 2 does not acquire instance 1's link, counter, session version, account mutation or notice.
2. No external notification service is invoked; the private link outbox is not the notification sink. Instance isolation and outbox separation are design choices, not evidence of durability.

### TC-016 — pytest collects and executes required automated coverage
**Links:** REQ-012 AC1; TASK-010, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: only once implementation and tests exist, inspect test names/assertions and collect pytest cases under Python 3.12; map them against TC-001–TC-013 and the relevant supplemental boundary/security cases.
2. Run pytest locally and record the command, environment, collection list and actual outcome (pass, fail, skip or blocked) for the targeted behavior groups.

**Expected results**
1. Automated assertions cover observed sign-in presentation, reset entry and public response parity, first/fifth/sixth/hour boundary, valid reset, single use, just-before/exact-expiry, all-session sign-out and a notice after **each** successful reset.
2. Collection alone is not a pass. A missing assertion, skip or failure remains a reported gap; this document does **not** claim tests were run or succeeded.

### TC-017 — production limitations documented
**Links:** REQ-013 AC1; TASK-012. **Evidence:** S.

**Steps**
1. Preconditions/data: when project documentation exists, review README/local-run and test instructions and any stated production claims.
2. Find explicit limits for synthetic accounts, volatile process-local accounts/counters/tokens/session versions/link outbox/notice sink, restart and multi-worker state divergence, lack of real notification delivery, and incomplete production security.

**Expected results**
1. Documentation identifies synthetic and in-memory limitations, provides local/test use instructions and explicitly avoids claiming production readiness or durable/external delivery.
2. Absent documentation or an unqualified production-ready claim fails the future review; the proposed checklist is not a certification of production security.

### TC-018 — bounded non-deployment review
**Links:** REQ-014 AC1; TASK-012. **Evidence:** S.

**Steps**
1. Preconditions/data: obtain the bounded final project tree/diff and **available** execution or delivery record; do not deploy, trigger workflows or access a hosted environment as part of this test.
2. Inspect additions for deployment workflows, deploy scripts/configuration, hosted endpoints and deployment commands; distinguish local Flask execution/pytest from deployment.
3. Record the paths and records actually examined, plus inaccessible records or unobservable external environments.

**Expected results**
1. No deployment workflow or performed deployment is found **within the inspected deliverables and available records**; any deployment-related addition is flagged.
2. Inspection alone cannot prove universal absence of deployment outside those records. Missing external evidence is a stated limit, never silently converted to a global non-deployment claim.

## Supplementary negative, security, race, rollback and accessibility scenarios

### TC-019 — parity at under-limit and suppressed issuance
**Links:** REQ-003, REQ-004; TASK-004, TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: for each comparison prepare **separate matched fresh stores and independent clients** with equivalent CSRF validity, headers and public cookie state; pin each store's UTC clock to the identical instant `t0`. Seed both A's normalized key and N's normalized nonexistent key with equal private request counts (zero, four, then five at `t0`); use mixed-case/whitespace address variants resolving to the same key as its baseline.
2. At count 0 and count 4 submit one valid request for each key at `t0`; at count 5 submit another at `t0 + 3599s` in matched stores with clocks frozen to that **same** instant. Follow redirects independently; repeat each pair with execution order and client assignments reversed on fresh matched fixtures.
3. Compare public status, `Location`, confirmation body, account-dependent headers/cookies and any address/token disclosure; separately inspect private counts and outboxes.

**Expected results**
1. Every matched A/N pair has indistinguishable account-dependent public surfaces regardless of eligibility or throttle; responses do not identify whether issuance happened. Distinct CSRF randomness, run order and elapsed wall time do not masquerade as account existence differences.
2. An eligible A request alone issues a private link; N never does; both suppressed keys issue none. Under the proposed private nonexistent-key accounting, normalization cannot bypass the counter.

### TC-020 — invalid input and CSRF rejection
**Links:** REQ-002, REQ-003, REQ-005; TASK-002, TASK-004, TASK-007, TASK-010, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh A and N stores with matching clocks and CSRF-capable clients; capture counters, outbox, A hash, token state, version and sink. Choose empty and syntactically malformed address values, empty and `P_invalid` new-password inputs defined by the eventually documented rule.
2. Submit empty/malformed address forms for A/N-equivalent paths; compare feedback **within each invalid-input class**, then submit an otherwise valid request with missing and invalid CSRF using separate fresh clients.
3. Obtain an unused A link privately; submit empty/`P_invalid` new-password forms with valid CSRF, and a documented-valid value with missing/invalid CSRF; inspect feedback, public results and all captured private state.

**Expected results**
1. Invalid address input gets a field-associated, readable account-independent error; untrusted CSRF requests are rejected without a successful request/reset. Do **not** prescribe an HTTP status for invalid input or infer account existence from different invalid-value classes.
2. Invalid password input has associated accessible feedback; no link is issued for invalid/CSRF-rejected request input, and no invalid/CSRF-rejected reset changes A's hash, consumes a link, bumps version, creates a notice or claims success.

### TC-021 — concurrent fifth/sixth request ceiling
**Links:** REQ-004; TASK-001, TASK-005, TASK-010. **Evidence:** K.

**Steps**
1. Preconditions/data: fresh A account with four honored requests for its normalized key at fixed UTC `t0`, four private outbox links, two independent clients with valid per-client CSRF, synchronized test barrier and clock held at `t0 + 1 second`.
2. Release two concurrent valid A requests (one using a case-variant address normalizing to A); capture their public responses and the locked counter/outbox after both complete.

**Expected results**
1. Exactly one additional A link is honored, giving five total; neither interleaving produces six or duplicate token issuance.
2. The two public neutral responses are indistinguishable on account-dependent surfaces and reveal neither the winner nor throttle state.

### TC-022 — concurrent redemption of one link
**Links:** REQ-005, REQ-006, REQ-007, REQ-009; TASK-007, TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh unused A link before expiry with clock fixed to `t0 + 1 minute`; two independent clients obtain their own valid CSRF and choose distinct documented-valid `P_new1` and `P_new2`; snapshot A hash/version and empty notice sink.
2. Release concurrent POSTs to the **same** link at a test barrier; inspect both responses, final hash, consumed-token state, version and sink.

**Expected results**
1. Exactly one POST commits and can report success; the loser cannot claim success or overwrite the winner's hash. Final credentials match the winner's chosen value only.
2. Token is consumed once, A's version changes once, and exactly one A-owner notice appears. The clock is stable so the result cannot be attributed to expiry.

### TC-023 — in-process notification failure rolls back reset
**Links:** REQ-005, REQ-008, REQ-009; TASK-007, TASK-008, TASK-009, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: fresh unused A link, two independently active A sessions and one B session; before expiry use valid CSRF and documented-valid `P_new1`; snapshot hash, token state, A/B versions and sink; inject an in-process sink-append failure, including a variant that raises after a partial append.
2. Submit the otherwise-valid reset while failure injection is active; inspect public result, private state and guarded requests from A's two clients and B's client.

**Expected results**
1. No success is claimed and no inconsistent partial success remains: A hash, token usability, A/B versions and sink contents equal the pre-call snapshot (including no orphan entry after partial append).
2. Both A sessions and B's session retain their pre-failure authorization state. This is a proposed **process-local** rollback invariant, not a claim of durable distributed transactions.

### TC-024 — keyboard, labels, errors and announced outcomes
**Links:** REQ-001, REQ-002, REQ-003, REQ-005, REQ-006, REQ-007; TASK-002, TASK-004, TASK-006, TASK-007, TASK-010, TASK-011. **Evidence:** S, I, K.

**Steps**
1. Preconditions/data: prepare a keyboard-only client and accessibility-tree/screen-reader inspection for the pictured sign-in card and **proposed** reset request, neutral confirmation, new-password, success and unusable-link views; separately arrange empty/invalid input and an expired link.
2. Tab through each interactive view and activate link/submit/retry controls using keyboard only; inspect focus sequence, accessible names/labels and contrast/readability of controls and text.
3. Trigger each invalid-input error and success/non-success transition; inspect programmatic field-error association and whether focus reaches or announces the resulting message.

**Expected results**
1. No keyboard trap; logical visual/DOM focus order, visible focus, programmatic field labels, discernible link/button names and readable contrast are verified for the implemented views.
2. Invalid input produces associated readable errors, and status/error transitions are announced or focused; success is not announced before commit and unusable links never announce success. Only the sign-in card's appearance is pictured; the accessibility behavior and recovery states are proposals to verify.

### TC-025 — unknown, used and expired token non-disclosure
**Links:** REQ-003, REQ-005, REQ-006, REQ-007, REQ-011; TASK-001, TASK-004, TASK-005, TASK-006, TASK-007, TASK-011. **Evidence:** S, K.

**Steps**
1. Preconditions/data: use separate fixtures with an unknown opaque URL token, a previously consumed A token, and an unused A token at `t0 + 30 minutes`; prepare separate valid CSRF/`P_new1` where a POST is attempted, and snapshot hashes, versions and sink.
2. GET and attempt POST for each token state; inspect responses, ordinary logs, cookies, HTML, response headers and outgoing asset URLs. Separately submit an eligible A request and inspect the public request/confirmation and private outbox.
3. Check the proposed token pages' `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, no third-party assets and redaction of token path segments in ordinary logs.

**Expected results**
1. Unknown, used and expired URLs yield recoverable non-success/new-request behavior without password mutation, version bump, notice or success claim. Issued tokens appear only in the private process-local test outbox, not the public confirmation, cookies, ordinary logs or page body.
2. Token-page policy headers and asset/log constraints match the **solution-design proposal**; no external link delivery or production-grade confidentiality is inferred from an in-memory outbox.

## Coverage and outstanding validation

The primary scenarios cover **18/18 approved ACs**: REQ-001 (TC-001–002), REQ-002 (TC-003), REQ-003 (TC-004), REQ-004 (TC-005–006), REQ-005 (TC-007), REQ-006 (TC-008), REQ-007 (TC-009–010), REQ-008 (TC-011), REQ-009 (TC-012–013), and REQ-010–REQ-014 (TC-014–018, respectively). The seven additional cases TC-019–TC-025 exercise parity under suppression, validation/CSRF, concurrency, rollback, accessibility and token handling. **14/14 REQ identifiers and 12/12 TASK identifiers are linked; uncovered ACs: none.** These are prospective mappings, not test execution outcomes.

Open implementation choices: exact minimal password rule, non-sign-in recovery copy/visuals, precise focus treatment and link inspection UX have not been specified by the evidence; use documented implementation choices when executing, without converting them into wireframe facts. Rolling-hour arithmetic, private nonexistent-key counters, synthetic guarded sign-in and token response protections are approved design proposals. If implementation, Python 3.12, tests or delivery records are unavailable, report the corresponding check as **not validated**, not passed. A review of available records cannot establish non-deployment outside its documented scope.

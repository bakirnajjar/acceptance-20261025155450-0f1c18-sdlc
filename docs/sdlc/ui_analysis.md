# UI analysis

**Applicable.** The supplied wireframe depicts the sign-in entry point. **Observed** means visible in that image; **Proposed (inferred, not observed)** means a design or state to satisfy an approved requirement. This analysis does not claim that any page or behavior has been implemented.

## Evidence and traceability

| Key | Source type | Source ID | Locator | Use |
| --- | --- | --- | --- | --- |
| [A] | `attachment` | `c2d1eadb-60f9-4b3e-a07e-956604ee291e` | `sign-in-wireframe.png` | Visible sign-in composition only |
| [S] | `user_story` | `user_story` | `characters 0-16000` | Application and delivery scope |
| [K] | `knowledge` | `4d3e7857-9fa5-49cc-a86a-33bcf67fabee` | `v1, chunk 0` | Current-run account recovery standard |

The approved requirements analysis supplies **REQ-001–REQ-014** as predecessor identifiers. Its read result supplied no citable `stage_output` locator, so these IDs provide cross-stage links without a fabricated stage-output reference. No similarly named knowledge source from another run is cited.

## Screen inventory and step-by-step flows

1. **Observed — sign-in entry [A], REQ-001 and the visible entry of REQ-002.** On a white canvas, one centered outlined rectangular card has, top to bottom: bold **Sign in** heading; labeled **Email address** field and light-gray `name@example.com` example; labeled **Password** field and masked `********` example; blue underlined **Forgot password?** link immediately beneath the password field; dark, full-width **Sign in** button beneath the link; and light-gray **No account? Contact your administrator.** beneath the button. These are visible elements, not proof of link activation, login functionality, placeholder-versus-value state, or form submission.
2. **Proposed (inferred, not observed) — reset request [K], REQ-002–REQ-004.** From sign-in, activate **Forgot password?** → open a reset-request form with an account-address label, field and submit control → submit → show an account-existence-neutral confirmation and return-to-sign-in action. Otherwise equivalent requests for existing and nonexistent accounts have identical responses. Honor the five-requests-per-account-per-hour limit without revealing existence through throttling feedback. No reset form or confirmation is pictured.
3. **Proposed (inferred, not observed) — password change [S][K], REQ-005–REQ-007.** Open an issued, unused, unexpired reset link → show a new-password form → submit a valid change → show success *only after* the account password changes. A link works at most once and cannot reset at or after 30 minutes from issue. If already used or expired, show a recoverable **non-success** state and path to request a fresh link. The wireframe shows none of these screens; link conveyance and password rules are unspecified.
4. **Proposed (inferred, not observed) — post-success effects [S][K], REQ-008–REQ-009.** A successful change signs the account out of every active session and records an owner notification for *each* success in the in-memory sink. These are behavioral outcomes, not evidence for another screen, an external delivery channel or prescribed success copy.

## Requirement-to-visual coverage

| Approved IDs | Coverage |
| --- | --- |
| REQ-001 | **Observed** composition and controls [A]; server rendering comes from [S], not the image. |
| REQ-002 | **Observed** link appearance [A]; **Proposed** activation and request transition [K]. |
| REQ-003–REQ-004 | **No visual evidence** of response parity or the five-per-account-per-hour limit; neutral confirmation and parity-preserving throttling are **Proposed** [K]. |
| REQ-005–REQ-007 | **No visual evidence** of password change, single-use links or 30-minute expiry; new-password, success and unusable-link states are **Proposed** [S][K]. |
| REQ-008–REQ-009 | **No visual evidence** of session sign-out or per-success owner notification; behavioral requirements [S][K], not grounds for an extra UI. |
| REQ-010–REQ-014 | **No visual evidence**: Python 3.12/Flask server rendering, synthetic accounts/in-memory sink, pytest tests, production-limitations documentation and no deployment/workflows are technical, test, documentation or delivery-only constraints [S]; they require no new screen merely by virtue of being requirements. |

## Proposed states and accessibility

All provisions in this section are **Proposed (inferred, not observed)**, not properties established by [A].

| Surface | Empty / validation | Processing / error / outcome |
| --- | --- | --- |
| Sign-in [A][S] | Associate empty-field and invalid-input feedback with the relevant fields; do not assume a password rule or complete login policy. | Indicate submission/loading without promising authentication; show a readable, announced error if needed. |
| Reset-request form [K] | Handle blank/malformed account address with labeled, field-associated feedback. | Indicate processing without account-sensitive clues; handle errors and throttling without an account-existence oracle; existing/nonexistent requests receive identical responses in equivalent circumstances. |
| Neutral confirmation [K] | No input-specific empty state. | Announce neutral completion and provide return to sign-in; any loading/error display must not expose account existence. |
| New-password form [S][K] | Handle empty/invalid input without inventing password-complexity rules. | Indicate processing or error; validate link eligibility before declaring success. |
| Success / unusable-link result [K] | Neither result has a form-specific empty state. | Announce success only after completion; used/expired links have a non-success message and fresh-request path. Pending feedback must not assert a completed change. |

Across every surface, provide keyboard access and logical focus order; preserve visible and programmatic labels and screen-reader names for fields, links and buttons; ensure usable contrast; associate validation errors with inputs; and move focus to, or announce, important error and status messages. The image alone does not establish accessibility or responsive measurements.

## Assumptions and open questions

- **Assumptions:** Only the sign-in screen is observed. Examples may be hints rather than populated values; no authentication policy, pixel dimensions or breakpoints are inferred. Rate-limit internals, nonexistent-identifier accounting, password rules, link format and delivery mechanism remain open; the synthetic demonstration need not use external email. Predecessor IDs are linked without inventing a `stage_output` locator.
- **Nonblocking:** Must the pictured **Sign in** action authenticate synthetic accounts, or can test-established sessions demonstrate post-reset sign-out?
- **Nonblocking:** Are `name@example.com` and `********` placeholders, populated values or presentation examples? What responsive layout is intended?
- **Nonblocking:** How are issued links conveyed or inspected in the synthetic demonstration?
- **Nonblocking:** How are nonexistent identifiers accounted for, and what throttled response and hourly-window algorithm preserve response parity?
- **Nonblocking:** What password-validation rules, reset-page wording and precise focus/error behavior are intended?

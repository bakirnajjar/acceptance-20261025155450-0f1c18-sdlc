# UI evidence and coverage map (T001)

This is planning evidence for a later UI-analysis contract, **not** an implemented-screen inventory or a product output. UI analysis is applicable because the supplied wireframe depicts the sign-in entry point. The approved `requirements_analysis` defines REQ-001–REQ-014; its read result provides no citable `stage_output` locator, so the identifiers below link to that approved output without an invented citation.

## Citable sources

| Key | Source type | Source ID | Locator | Scope |
| --- | --- | --- | --- | --- |
| [A] | `attachment` | `c2d1eadb-60f9-4b3e-a07e-956604ee291e` | `sign-in-wireframe.png` | Visible sign-in layout only |
| [S] | `user_story` | `user_story` | `characters 0-16000` | Application and delivery constraints |
| [K] | `knowledge` | `4d3e7857-9fa5-49cc-a86a-33bcf67fabee` | `v1, chunk 0` | Current-run ACC-STD-01–03 reset behavior |

## Screen inventory and flow

| Screen / purpose | Components, data, actions and requirement coverage |
| --- | --- |
| **Observed** sign-in entry [A] | White canvas with one centered, outlined rectangular card. Top to bottom: bold **Sign in** heading; labeled **Email address** field with light-gray `name@example.com` example; labeled **Password** field with masked `********` example; blue underlined **Forgot password?** link immediately below that field; dark, full-width **Sign in** button below the link; light-gray **No account? Contact your administrator.** below the button. The link and button are visible affordances, not evidence of their behavior. This directly covers REQ-001's appearance and only the entry-link appearance of REQ-002. No pixel measurements, breakpoints, placeholder-versus-value interpretation, authentication behavior, or interaction outcome follows from the image. |
| **Proposed (inferred, not observed)** reset-request form [K] | Follow **Forgot password?** from sign-in to a form for an account address, then submit a reset request (REQ-002). **Proposed (inferred, not observed)** neutral confirmation after submission: identical response for existing and nonexistent accounts (REQ-003); the five-per-account-per-hour limit is behavioral and does not itself dictate a distinct screen (REQ-004). |
| **Proposed (inferred, not observed)** new-password form and result [S][K] | Follow an issued valid, unused, unexpired link to enter a new password, submit, and reach a completion state only on successful reset (REQ-005). **Proposed (inferred, not observed)** an unusable-link state for expired or previously used links (REQ-006–REQ-007). The reset must sign out all active account sessions and record an owner notification after each successful reset (REQ-008–REQ-009), but neither effect is visually evidenced and no particular UI disclosure or delivery channel is specified. |

## Requirement-to-visual coverage

| Requirement IDs | Visible evidence versus proposed/nonvisual coverage |
| --- | --- |
| REQ-001 | **Observed** sign-in card, controls, examples, text and order [A]; server rendering comes from [S], not the image. |
| REQ-002 | **Observed** link only [A]; **Proposed (inferred, not observed)** activation and reset-request transition [K]. |
| REQ-003–REQ-004 | **No visible coverage** of identical responses or the five-per-account-per-hour limit [K]. Neutral confirmation is proposed; throttling must not reveal account existence. |
| REQ-005–REQ-007 | **No visible coverage** of password change, single use, or 30-minute expiry [S][K]. New-password, success and unusable-link states are proposed. |
| REQ-008–REQ-009 | **No visible coverage** of session sign-out or post-success owner notification [S][K]. These are behavioral effects, not grounds to invent screens or an external service. |
| REQ-010–REQ-014 | **No visible coverage**: Python 3.12/Flask server rendering (REQ-010), synthetic accounts/in-memory notification sink (REQ-011), pytest tests (REQ-012), production-limitations documentation (REQ-013), and no deployment or deployment workflows (REQ-014) are story constraints [S], not visual screen requirements. |

## Proposed states and accessibility (all inferred, not observed)

- **Sign-in:** provide empty-field and malformed-address/password validation, an error presentation and a submission/loading indication without assuming a complete sign-in policy (REQ-001). The button's actual authentication behavior remains open.
- **Reset request:** handle blank/malformed address validation and submission/loading; show the same neutral submitted response for existing and nonexistent accounts (REQ-002–REQ-003). Handle a throttled request without additional reset issuance (REQ-004), while preserving account-existence response parity; exact throttling copy and accounting remain open.
- **Neutral confirmation:** show neutral content and a way back to sign-in; ensure the same visible result for otherwise equivalent submissions regardless of account existence (REQ-003). If loading/error is needed, keep account-sensitive details out of it.
- **New password:** handle empty/invalid submission, submission/loading and errors without inventing password-complexity rules; show success only after a valid reset (REQ-005). For used or expired links, provide a non-successful invalid-link state and a path to request a fresh link (REQ-006–REQ-007); the precise message is unspecified.
- **Success and invalid-link states:** propose readable status/error messaging and a sign-in or retry path respectively; they have no form-specific empty state, and any processing/loading feedback must not imply success before completion (REQ-005–REQ-007).
- Across every proposed screen and the sign-in entry: ensure keyboard access and logical focus order; move focus to or announce validation and status messages; use visible labels and screen-reader control names, including the link and button; maintain usable contrast and accessible error associations. These accessibility provisions are **Proposed (inferred, not observed)**, not qualities established by [A].

## Open questions / assumptions

- Does **Sign in** authenticate synthetic accounts, or is its observed presentation plus test-established sessions sufficient to verify post-reset sign-out? No complete login policy is assumed.
- Are `name@example.com` and `********` placeholders, prefilled values, or presentation examples? The image alone does not resolve this.
- How are issued links conveyed or inspected within the synthetic demonstration [S], without assuming email delivery or an external service?
- How are nonexistent identifiers handled under the per-account rate limit, and what throttled feedback preserves identical responses for existing and nonexistent accounts [K]? No hourly-window algorithm is specified.
- What responsive layout and precise focus/error behavior are intended? No viewport breakpoints or pixel targets are inferred from [A].
- What password-validation rules are wanted? No complexity rule or production-readiness claim is inferred from [S] or [K].

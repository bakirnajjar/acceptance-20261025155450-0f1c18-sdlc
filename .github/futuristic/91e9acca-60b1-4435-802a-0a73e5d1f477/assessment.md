# Phase 1 assessment: Risk notes

## Scope and evidence

The requested output is a delivery-risk document, not an implementation or deployment. Its later JSON contract must use `stage: custom_document`, `stage_key: acceptance_20261025155450_0f1c18_risk`, schema version `1.0`, and item IDs beginning `REA6D7-`; each risk must link to at least one approved `REQ-` identifier. A companion readable Markdown document is required. No product output is written in this phase.

- Pinned story: `{"source_type":"user_story","source_id":"user_story","locator":"characters 0-16000"}`. It calls for a Python 3.12 Flask, server-rendered password-reset demonstration with pytest, synthetic accounts, an in-memory notification sink, documented production limitations, and no deployment or deployment workflows.
- Supplied image: `{"source_type":"attachment","source_id":"c2d1eadb-60f9-4b3e-a07e-956604ee291e","locator":"sign-in-wireframe.png"}`. Observed: a bordered sign-in card with heading "Sign in", labeled email and password fields, email hint `name@example.com`, masked password example, "Forgot password?" link beneath the password input, dark "Sign in" button, and "No account? Contact your administrator." beneath the button. The image does not establish authentication behavior or responsive breakpoints.
- Curated, run-specific account recovery standard: `{"source_type":"knowledge","source_id":"4d3e7857-9fa5-49cc-a86a-33bcf67fabee","locator":"v1, chunk 0"}`. ACC-STD-01 requires a reset entry point, identical existing/nonexistent-account responses, and five requests per account per hour. ACC-STD-02 requires single-use links, 30-minute expiry, and sign-out of all active sessions after reset. ACC-STD-03 requires owner notification after each successful reset.
- Authorized approved predecessor: `requirements_analysis` (read via the prior-stage-output service), containing `REQ-001` through `REQ-014` and five non-blocking open questions. This is the source of approved requirement identifiers; the other similarly titled knowledge-search results belong to different runs and will not be used.

## Delivery-risk coverage to develop after plan approval

Risks should be actionable delivery uncertainties, not assertions that implementation defects already exist. Candidates grounded in approved requirements include visual/entry-point fidelity (`REQ-001`, `REQ-002`); account enumeration and rate-limit edge cases (`REQ-003`, `REQ-004`); token replay and expiration boundaries (`REQ-005` through `REQ-007`); cross-session sign-out and per-reset notification (`REQ-008`, `REQ-009`); Python/Flask rendering and synthetic in-memory constraints (`REQ-010`, `REQ-011`, `REQ-013`); and incomplete pytest coverage or accidental deployment scope (`REQ-012`, `REQ-014`). Describe the failure mode, impact, and practical mitigation/verification for each without inventing an implementation.

## Assumptions and unresolved points

No application implementation or test evidence is approved at this point; likelihood, actual defects, and production readiness cannot be claimed. The predecessor leaves login-button behavior, rate-limit accounting/window algorithm, responsive/pixel fidelity, in-memory reset-link conveyance, and password policy/documentation depth unspecified. Treat these as bounded delivery risks or open questions, not new requirements. Preserve account-existence response parity when discussing rate limiting, and distinguish the demo's in-memory notification capture from production delivery. No consequential blocker is evident for documenting risks at the approved-requirement level.

# T013 / TASK-012 coding report — local synthetic password reset

## Delivered and provenance

The approved plan and assessment, `docs/sdlc/test_case_design.json` (TC-001
through TC-025), the approved solution design and the existing application
and pytest suite were reviewed. The sign-in card reflects only the supplied
wireframe; recovery screens, synthetic sign-in, private link inspection and
the minimal 1–1024-character/non-whitespace password rule are demonstration
choices, not image-observed authentication requirements. No real identity,
delivery or hosting integration was added.

README now explains Python 3.12/uv setup, local Flask execution, exact quality
gates, synthetic fixture credentials, and how to inspect a private reset link
inside the same app instance using a test client. It warns that accounts and
password hashes, hourly counters, token digests, session versions, the private
link outbox and the distinct owner-notification sink are all process-local:
restart loses state and separate workers diverge. Local success notices are not
delivered messages; local rollback is not crash-durable. It explicitly rejects
a production-readiness claim. TC-017 has an automated README contract test.

`tests.json` has schema version `1.0`, exactly one entry for each TC-001–025,
and real collected pytest node IDs for the 23 automated entries. The
TC-016 inventory test checks actual Python 3.12 pytest collection of every
automated reference; full suite execution is recorded separately below.
Shared/parameterized tests cover multiple boundaries; a reference to one
collected parameter is not a claim that this parameter alone covers the entire
case. TC-024's DOM assertions are partial only. TC-018 and TC-024 remain manual.

## Validation performed in repository root

| Check | Actual result |
| --- | --- |
| `uv run --locked --python 3.12 python -m compileall -q src tests` | Passed (exit 0). |
| `uv run --locked --python 3.12 pytest --collect-only -q` | Passed; 88 tests collected. |
| `uv run --locked --python 3.12 pytest -q` | Passed; 88 passed in 30.06s, no skips reported. |
| `uv run --locked --python 3.12 ruff check . && uv run --locked --python 3.12 ruff format --check .` | Passed; all checks passed and 36 files already formatted. |
| `uvx --from detect-secrets==1.5.0 detect-secrets scan README.md tests/test_delivery_docs.py tests/test_issuance.py .github/futuristic/d40bbe8d-773b-4cba-a51e-cab7ab35cbc4/coding-report.md .github/futuristic/d40bbe8d-773b-4cba-a51e-cab7ab35cbc4/tests.json` | Exit 0; empty `results` (no findings in these added/edited documents and tests). |
| `git --no-pager diff --check` | Passed; no whitespace errors. |

An initial full pytest run had one **new TC-016 mapping assertion** failure
because combined test names abbreviated the second TC identifier; the new
traceability test names and corresponding inventory references were corrected.
An initial Ruff format check identified two new lines (README Python example
and new test); both were formatted. The full three required gates were rerun
after those changes and passed. No test was skipped, relaxed or suppressed.

The suite covers request parity across matched existing/absent clients,
hourly issuance edges and concurrency, strict reset expiry, replay, password
change, session revocation, owner notices, rollback, CSRF/input errors,
process-local isolation, token-response protections, rendered DOM semantics
and local documentation. These are local Flask client/in-memory tests, not
browser accessibility, delivery or hosted-environment verification.

## Bounded delivery review (TC-018; manual)

Reviewed the bounded tracked tree (`git ls-files`, 53 tracked paths), tracked
diff from scaffold checkpoint `f5386e8` to `HEAD`, this task's working diff and
status, `.github` directories and the tracked `.github/workflows/**` path set.
No tracked workflow directory/file or delivery configuration/script was found
in that bounded tree/diff; this task modifies only README, a traceability test
name, a new documentation/collection test, and this report and inventory. No deployment
command was run as part of this task. An available local execution event
record was parsed only for metadata (2,833 JSONL entries, zero malformed
entries); a command-level search of that record was **denied by run policy**
and was not retried. Therefore the execution record is **not** certified free
of prior deployment commands; its command contents and any external
environments remain unverified. TC-018 stays manual, and this bounded review
cannot establish the absence of deployment outside the accessible materials.

## Remaining manual work and limits

- **TC-018:** authorized human review of any accessible execution/delivery
  records and external environment, without performing deployment. The
  current record's command-level inspection was policy-blocked.
- **TC-024:** real keyboard-only navigation and activation, screen-reader
  announcements/accessibility tree, visible focus and color contrast across
  sign-in and all recovery/error/success views. Passing DOM assertions do
  **not** finish this case.

The fixture is not production-ready: no durable multi-worker storage,
cross-worker revocation, actual notification delivery, full identity
management, operational abuse controls, comprehensive privacy/security
review or real-browser accessibility evaluation is provided.

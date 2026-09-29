# Decision log: e2e-fixes

Goal: Developer-approved panel-review decisions for End-to-end testing: (e2e F7b) run remembers the workflow record's report count before starting and fails with no_result unless a new report appeared; (headless-sessions F3b) on wait_exceeded, start() writes session.json with end wait_exceeded and the progress-file path before raising, listed in Usage with a scenario and test; (e2e F5) End-to-end testing lists tests/concorde/workflows/run_script.mjs as a shared file of its own tool realization and says in Design that the driver runs Workflows' test sandbox, accepting that coupling; (swe-bench-cases) the order 'reviewed before the case's issue is worked' is a condition on how the tool is used, not a promise of the tool: state it as such outside the SHALL. Specs and tests.

## Decisions (task session, 2026-09-29)

- **F7b as a requirement.** Options: prose only in Usage, or a new requirement. Chose a new
  `req.e2e.own-result` with `scenario.e2e.stale-result` and a test, because "print only a result
  the run saved" is a promise of `run` that a scenario verifies. `latest_report` became
  `saved_reports` (the list); the old test of `latest_report` was replaced by one that drives
  `run_workflow` with a stubbed headless session. The `no_result` detail names both counts, or the
  missing file when the newest saved result is absent.
- **F3b record shape.** On `wait_exceeded`, `session.json` gets `end: "wait_exceeded"` and a
  `progress` field with the run progress file path; the raised error also gains `session` naming
  `session.json`, so `run`'s propagated error names the kept session (e2e Usage says so). The
  record writing moved into a local `save()` in `start()` so both paths write the same record.
  `req.headless-sessions.wait-bounded` and `logs-kept` were extended to cover the kept record;
  new `scenario.headless-sessions.wait-exceeded` with a test using a stand-in `claude -p` whose
  run host outlives a 0.3 s wait limit.
- **F5 wording.** `tests/concorde/workflows/run_script.mjs` added to `realization.e2e.tool`
  entries (Workflows keeps listing it through `tests/concorde/workflows/`); the realization
  paragraph names it as shared, and a Design paragraph states the accepted coupling and why a
  second stand-in runtime would drift. spec-validation reports no overlap finding.
- **swe-bench-cases.** The SHALL of `req.swe-bench-cases.repair-specs-only` no longer says "before
  the case's issue is worked"; a following paragraph in the same requirement states the order as a
  condition on how the developer uses the tool, which `repair-specs` does not check.
- **Not acted on:** `uvx ruff check` (a newer ruff than the project pins) reports pre-existing
  findings in `scripts/e2e/*.py` and `tests/concorde/e2e/test_cases.py` (PLW1510, RUF100, SIM102,
  ISC004, SIM117) on lines this task did not touch; left alone as outside the goal. `ruff format`
  passes twice without changes.
- Full suite on the final input: 663 passed, 4 skipped.

## Closed: merged, 2026-09-28T17:23:10Z

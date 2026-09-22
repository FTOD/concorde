# Semantic audit of the slow end-to-end Python tests

## Motivation

The user found the full Python suite too slow and asked two things: (1) audit which tests are
unnecessary or of unclear meaning and clean them up; (2) run the suite in parallel. Item (2) was
implemented as `change.b0b2efdc-1909-42cd-8bba-0fd533eb358d` (pytest + pytest-xdist, single
entry `.venv/bin/python -m pytest`, ~200 s wall instead of 29.5 min serial). Item (1) was
deliberately left out of that change and is recorded here.

## Measured facts (primary at c5b2d709, 2026-09-22)

- 1057 collected tests; median duration 0.07 s; 585 tests take < 0.1 s and together cost ~10 s.
  Deleting small tests would not make the suite faster.
- 33 tests take > 10 s and account for 61 % of serial time (1181 s of 1933 s); 5 take > 60 s
  (724 s). Parallel wall time is now bounded by the single longest test (~197 s:
  `harness/test_installed_worker_runtime.py::test_ignored_installed_runtime_launches_programmer_and_readonly_reviewer`).
- Heaviest files: `harness/test_installed_worker_runtime.py` (2 tests, 347 s),
  `harness/test_worktree_lifecycle.py` (46 tests, ~10 s each, real git worktrees),
  `operations/test_review.py` (59 tests, 228 s), `distribution/test_install_concorde.py`
  (24 tests, 176 s, each provisioning an installer target), `distribution/test_local_installation.py`
  (one 140 s test), `harness/test_tester_tmp.py` (one 134 s test),
  `spec/test_distribution.py` (one 103 s test).
- 724 of 1025 `def test_` carry `@verifies("scenario....")`; removing or merging one changes
  Spec verification coverage and needs the paired Spec process.

## Agreed scope of the audit

Read the ~33 tests above one by one and answer, per test: does it repeat an expensive
environment build (installer, venv, `npm ci`, git worktree) that a class-level or module-level
fixture could share; does another end-to-end test already cover the same scenario so one of them
is redundant; is the asserted behavior actually specified (which `scenario.*`), or is the test
of unclear meaning. Produce a list of concrete delete / merge / share-fixture proposals with the
affected scenario IDs for the user to decide on; do not delete tests during the audit itself.

## Non-goals

- Do not weaken assertions or turn real end-to-end tests into mocks to save time.
- Do not remove sub-0.1 s tests for speed; they are essentially free.
- Not part of this note: the tester-harness hermeticity fixes (ambient
  `CONCORDE_SESSION_SELECTION` / `PI_SUBAGENT_EXTENSION_BINDINGS` leaking into 21 tests, and
  `test_worker_sandbox.py` creating fixtures under in-repo `tests/concorde/.tmp`); those were
  folded into the pytest-migration change at the user's request.

## Evidence

- Per-test timing from an 8-process run: `/tmp/timing.json` (transient; regenerate with
  `.venv/bin/python -m pytest --durations=50` or the `--json=` summary of the evidence plugin).
- Status record: `.concorde/status/change.b0b2efdc-1909-42cd-8bba-0fd533eb358d.json`.

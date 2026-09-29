# Decision log: panel-larger-commands

Goal: Finish the 2026-09-28 panel review's larger items for Commands, Delivery, Validation, Scaffold and Checks: split bundled scenarios with their tests' @verifies, add Scaffold's missing scenarios and tests, and open Commands' Usage with a worked normal path

## Brief from the main agent (panel-review LARGER items)

These items are the "larger" findings left from the 2026-09-28 `spec_panel` review (decision
history in `/home/zhenyu/concorde/.concorde/tasks/panel-review-fixes.decisions.md`). They are
confirmed real problems that need no design decision but are not small edits. Full review reports
(chair report and verdict per Module) are readable at
`/tmp/claude-1000/-home-zhenyu-concorde--claude-worktrees-panel-review-fixes/dbd505b3-74e1-499b-9440-e3cc4b821993/work/reports/module.<name>.md`
and `module.<name>.verdict.md`.

How to work:
- The project has changed a lot since the review. Check each item against the current Specs and
  code first. If it is already solved or no longer applies, record that here with the reason and
  skip it.
- If doing an item needs a design decision (narrowing or changing a promise, changing behaviour,
  a word choice that is not obvious), do not decide it: escalate to the main agent with options
  and a recommendation. Never narrow a Spec promise to fit the code; a Spec/code difference where
  it is unclear which is intended is escalated.
- Splitting a scenario: keep the original id on the first scenario; each new scenario id needs a
  test with `@verifies`, otherwise spec-validation warns `CONCORDE-COVERAGE-001`. Change the Spec
  and the tests' `@verifies` in the same commit, and only where the existing test really checks
  that scenario's outcome; otherwise add or extend a test.
- Diagrams: `d2 illustrative` blocks, following the diagram rules in the Protocol
  (`.concorde/protocol/`) and the project's Specs. "Don't draw diagrams for trivia": when the prose
  already says it plainly, skipping is fine; record why here.
- Usage items: restructure Usage so it opens with / contains a worked normal path, keeping every
  existing statement true.
- Use the glossary terms (`specs/concorde/glossary.json`) exactly. Edit only files of your
  Modules where possible; if another Module's file (or the glossary) must change, keep the change
  minimal and say so in your report.
- Never commit files a Bash sandbox mounts into the worktree (`.bashrc`, `.claude/...`).
- When done: task-validation and delivery, then report to the main agent: each item done or
  skipped (with reason), the decisions you took on your own, and anything waiting for a decision.

### Items of this task (handover list)

**module.commands**
- B · F3: Usage should open with `task-validation` followed by `delivery` (a worked normal path).

**module.delivery**
- A · F3: split the extra situations out of `unverified-scenarios` and `nothing`.

**module.validation**
- A · F17: split out `submodule-commit` from `submodule-content`, plus the other bundled scenario.

**module.scaffold**
- A · F17 (new scenarios and tests): `scaffold_invalid` keeps nothing; an existing target file gives `stale_proposal`.

**module.checks**
- A · F8: split `service-run`, `project-python` (missing/present/primary fallback/invalid environment), `selective` (skip/run/readiness).
- A · F12: the BUT of `timing-standalone-directory` flips its GIVEN; split out `scenario.checks.timing-invalid-directory`.
- C · F18: `run_checks` flow diagram (the verifier suggested not drawing it).

### Verdict text for each item (from the review's verification agents)

#### module.commands

##### F3 LARGER — Usage has no worked normal path
Real: Usage opens with synopses, the flag rules and the catalog, and gives the normal order in one closing sentence. Suggested: open Usage with a short worked path in a bound workspace (`task-validation` returning an `ok` result with a ready readiness, then `delivery` validating again and returning the delivery commit), then the flags, catalog and refusals. This restructures the section, so it was not edited.


#### module.delivery

##### F3 LARGER — unverified-scenarios and nothing each hold a second situation
The finding is real: the AND/BUT steps describe setups that the GIVEN does not establish. Splitting creates new scenario ids, and the tests' `@verifies` would have to move with them, or spec-validation warns about coverage. The tests are not in my owned files. Proposed change, to apply together:
(1) Remove the last AND and the BUT from `scenario.delivery.unverified-scenarios`.
(2) Add `scenario.delivery.verified-scenarios — A verifying test lets the code change through`: GIVEN the workspace of the previous scenario / AND a test in a file Module A binds declaring that it verifies `scenario.a.sum` / WHEN delivery runs / THEN the workspace is delivered, `ok`.
(3) Add `scenario.delivery.spec-only-scenarios — A scenario added without code needs no test`: GIVEN a workspace that adds `scenario.a.sum` without changing code / WHEN delivery runs / THEN it is delivered, `ok`, without a test.
(4) Remove the BUT from `scenario.delivery.nothing`. Add `scenario.delivery.redeliver — Delivering a delivered head again`: GIVEN a clean workspace whose head is its latest delivery commit / WHEN delivery runs / THEN it ends `ok` and reports that commit with `recovered` true / AND commits nothing.
(5) In `tests/concorde/delivery/test_delivery.py`, change `test_a_code_change_with_an_untested_new_scenario_is_refused` to `@verifies("scenario.delivery.unverified-scenarios", "scenario.delivery.verified-scenarios")`, `test_a_spec_only_change_needs_no_test` to `@verifies("scenario.delivery.spec-only-scenarios")` and `test_nothing_new_after_a_delivery` to `@verifies("scenario.delivery.redeliver")`.



#### module.validation

##### F17 LARGER — two bundled scenarios should be split (needs test declaration changes)
The finding is real: each scenario covers two situations. Splitting without updating the tests' `@verifies` would raise coverage warnings, and the tests are not in my owned files. Proposed change, to apply together:
(1) In `scenarios.md`, remove the BUT step from `scenario.validation.submodule-content`. Add `scenario.validation.submodule-commit — Moving a submodule's commit is a change`: GIVEN a workspace with a submodule / WHEN the submodule is moved to another commit / THEN it is a changed path and an uncommitted change.
(2) Narrow `scenario.validation.confirm-refused` to "a confirmation whose declaring document no longer has the recorded digest". Add `scenario.validation.confirm-invalid — Confirmation that would break the Specs is refused`: GIVEN a confirmation whose clearing would leave a structural error / WHEN Delivery asks Validation to apply the confirmations / THEN the application is refused / AND every Spec document is left as it was.
(3) In `tests/concorde/validation/test_validate.py`, `test_only_a_submodules_commit_is_measured` becomes `@verifies("scenario.validation.submodule-content", "scenario.validation.submodule-commit")` and `test_a_structural_error_after_confirmation_rolls_back` becomes `@verifies("scenario.validation.confirm-invalid")`.



#### module.scaffold

##### F17 LARGER — no scenarios for atomic failure or destination collision
Real: no scenario shows `scaffold_invalid` with nothing kept, or an existing target file ending `stale_proposal`. Adding them requires new tests with `@verifies`, or new scenarios would be reported uncovered. Suggested scenarios: `scenario.scaffold.invalid-not-kept` (a proposal whose files would add a structural error: `failed`, `scaffold_invalid`, one cause per finding, worktree unchanged) and `scenario.scaffold.target-exists` (a child's folder or entry already exists: `blocked`, `stale_proposal`, nothing written). The wording part is fixed: `vendored-external` now says "validates with no new error", matching `req.scaffold.atomic`.


#### module.checks

##### F8 LARGER — service scenarios pack several situations
Confirmed for service-run ("BUT asked for Module B…"), project-python (missing / present / primary
fallback / invalid env) and selective (skip / run / readiness). Splitting creates new scenario ids,
and the validator warns (CONCORDE-COVERAGE-001) for any scenario no test declares, so the split must
go together with test edits (not files this Module's Spec owns). Proposed split: keep
`scenario.checks.service-run` for A; new `scenario.checks.service-no-checks` (Module without checks
returns no result). Keep `scenario.checks.project-python` for the present-interpreter case (runs
with it, sees MARK, no PYTHONPATH); new `scenario.checks.project-python-missing`,
`scenario.checks.project-python-primary`, `scenario.checks.check-env-invalid`. Keep
`scenario.checks.selective` for the run with selected tests; new `scenario.checks.selective-none`
(skipped when no test verifies) and `scenario.checks.readiness-only` (a `when: readiness` check runs
only with `stage="readiness"`). Add the new ids to the `@verifies(...)` of
`tests/concorde/harness/checks/test_service.py` lines 41, 86/262 and 304, which already exercise
these cases.

##### F12 LARGER — timing-standalone-directory's BUT flips the GIVEN
Real. Splitting adds a scenario id that needs a test declaration (coverage warning otherwise).
Proposed: in timing.md delete the step "BUT a directory that does not meet these conditions
receives nothing, the telemetry is marked incomplete and the work runs unchanged" and add after the
scenario:
```
### scenario.checks.timing-invalid-directory — A refused timing directory receives nothing

- GIVEN no trace is open and `CONCORDE_DIAGNOSTIC_TIMING_DIR` names a directory that is relative, missing, a symbolic link, not canonical, inside the working directory or inside a `.concorde/status` or `.concorde/runs` directory
- WHEN host code marks a unit of work as a span
- THEN nothing is written to that directory or to the working directory
- AND one `CONCORDE_TIMING_INCOMPLETE` line is written to standard error
- AND the work returns exactly as unmarked work would
```
and in `tests/concorde/harness/checks/test_timing.py:165` change the decorator to
`@verifies("scenario.checks.timing-standalone-directory", "scenario.checks.timing-invalid-directory")`
(that test already covers every refused case).

##### F18 LARGER — activity diagram for run_checks
The rewritten numbered steps (F5/F6) now state each exit explicitly (unknown_module,
invalid_check/project_python_missing/check_input_missing before a command, check_sandbox_unavailable
with the log kept, stale_evidence, "a failure in any step ends the call without results"). A
`d2 illustrative` activity view beside them is optional; given the standing rule that diagrams are
not drawn for trivia I would not add one now.



## Task session decisions (2026-09-29)

Every item was checked against the current Specs and tests first; all were still open.

- **Delivery F3 — done** (commit baa20b15). Applied the verifier's proposal as given:
  `unverified-scenarios` keeps only the refusal; new `verified-scenarios`, `spec-only-scenarios`
  and `redeliver`; `nothing` loses its BUT. `@verifies` moved in `test_delivery.py` as proposed.
  Decision: kept `redeliver` separate from `recover` although both end `ok` with `recovered` true,
  because their GIVENs differ (a completed delivery run vs. one interrupted before its result);
  merging them would change `recover`'s situation.
- **Validation F17 — done** (45aa4908). `submodule-content` keeps the in-submodule change and is
  retitled "A file changed inside a submodule is not measured" (the old title "Only a submodule's
  commit is measured" described both halves); new `submodule-commit`. `confirm-refused` narrowed to
  the stale-digest case; new `confirm-invalid`. `@verifies` updated as proposed.
- **Scaffold F17 — done** (b55cad24). New `target-exists` and `invalid-not-kept` with new tests
  `test_an_existing_target_writes_nothing` and
  `test_a_scaffold_that_would_not_validate_keeps_nothing`. Decisions:
  - The structural error is produced by a child purpose linking to an undefined anchor
    (CONCORDE-LINK-001); it appears in the child's entry and in the parent's introducing paragraph,
    so two causes. The scenario says "one cause for each structural error the scaffold would add".
  - An existing child entry is caught by the recheck (the child's folder exists), so the
    `stale_proposal` names the folder `specs/shop/checkout/`, not the file. The scenario states that
    exactly. Open point (not changed, not mine to decide in this task): `req.scaffold.no-overwrite`
    says the error names "the existing file"; the per-file check in the plan step is effectively
    unreachable because the folder check fires first. Reported to the main agent.
- **Checks F8 — done** (28f98739). `service-run` keeps A; new `service-no-checks`.
  `project-python` keeps the present-interpreter case; new `project-python-missing`,
  `project-python-primary` (worded with `.venv/bin/python`, as its test uses) and
  `check-env-invalid`. `selective` keeps the selected-tests run and the digest statement; new
  `selective-none` and `readiness-only` (worded with the service's `stage` parameter). Existing
  tests already exercise each case; only `@verifies` changed.
- **Checks F12 — done** (28f98739). Removed the BUT; added `timing-invalid-directory` as proposed,
  with "the working directory or inside it" because the test refuses the working directory itself.
- **Checks F18 — skipped.** `run_checks`' numbered steps already state each exit; an activity
  diagram would repeat them (the rule against diagrams for trivia), as the verifier also advised.
- **Commands F3 — done** (35faf190). Usage now opens with the worked path `task-validation` then
  `delivery` in the bound workspace `severity` (ok with `ready` true or `blocked` with every
  finding; delivery decides again and returns `concorde: deliver severity`; the bundle lists the
  validation run, as `test_deliver_a_validated_task` checks), then the synopses, flag rules,
  catalog and the scaffold placement. The old closing sentence moved into the opening; no statement
  was dropped.
- Formatting: `uvx ruff format` needed `UV_TOOL_DIR=$TMPDIR/uvtools` because the sandbox keeps
  `~/.local/share/uv` read-only.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES. Sent back: scenario.scaffold.target-exists wrote the code's
  behaviour (the error names the child folder) into the very situation req.scaffold.no-overwrite
  promises "naming the existing file", which settles a Spec/code difference. Decision (mine):
  make the scenario neutral (blocked, stale_proposal, nothing written, file unchanged) and bring
  the difference to the developer with options (a) widen the requirement to "the existing file or
  the folder of the child that would hold it" (recommended), (b) make the recheck name the files,
  (c) leave as is.

## After the main agent's review (2026-09-29)

- On the main agent's request, `scenario.scaffold.target-exists` no longer says what the
  `stale_proposal` names (it had named the folder). The scenario now leaves the open difference with
  `req.scaffold.no-overwrite` ("naming the existing file") to the developer. The outcome stays
  `blocked` with `stale_proposal`, nothing written and the existing file unchanged. The test still
  asserts the folder the code names today, with a comment saying this goes beyond the scenario;
  its `@verifies("scenario.scaffold.target-exists")` claims only what the scenario states. The
  requirement and the code are unchanged. Delivered again afterwards.

## Closed: merged, 2026-09-28T19:59:49Z

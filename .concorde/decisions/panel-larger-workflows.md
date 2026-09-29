# Decision log: panel-larger-workflows

Goal: Finish the 2026-09-28 panel review's larger items for Workflows: split bundled scenarios with their tests' @verifies, add a brownfield walkthrough with a resume example, and the brownfield procedure diagram

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

**module.workflows**
- A · F24: split `step-cached`/retry, `step-starts`/`task-validation`, `step-waits`/lock waiting, `lost`/finished precedence.
- B · F23: a module.shop brownfield walkthrough plus an example of resuming after a pause.
- C · F22: the brownfield procedure diagram.

### Verdict text for each item (from the review's verification agents)

#### module.workflows

##### F22 LARGER — no process view of the brownfield procedure
The finding is real and is a new diagram. Add a `d2 illustrative` activity view next to the step
table: survey → (interactive with open decisions: stop) → scaffold → describe loop (providers
first; no-ask continues past a non-ok describe, interactive stops) → spec_review (interactive and
not ok: stop) → validate (not ok or not ready: stop) → delivery → report.

##### F23 LARGER — Usage lacks a normal-path walkthrough and a resume example
The finding is real and needs several new paragraphs. After the launch example, add a module.shop
walkthrough: survey proposes checkout/inventory, scaffold creates them, three describes, review,
validation, delivery and the saved report. Then add a one-pause resume: key `survey` pauses;
relaunch with answers creates `survey@<digest>` with `--input` = first survey run; later steps are
superseded if they existed. Put retry/restart transport detail after that.

##### F24 LARGER — scenarios pack several situations
The finding is real (step-cached/retry, step-starts/task-validation, step-waits/lock waiting,
lost/finished precedence). Splitting needs new scenario ids, and those need `@verifies`
declarations moved or added in `tests/concorde/workflows/test_workflows.py`. Without that, the
coverage check warns. My F4 edit added one more AND to step-waits because the existing test
verifies that case. The split should go with the test change.



## Task session log (2026-09-29)

### A · F24 — scenarios split (done, commit 44ef5838)
- Checked against the current Specs: all four bundles were still present.
- Decision: kept the original ids on the first situation and named the new scenarios
  `scenario.workflows.step-starts-command`, `step-waits-lock`, `step-retried` and `lost-finished`.
  Reason: short ids that name the second situation; no promise changed, only regrouped.
- Decision: `step-retried` GIVEN uses the key `validate` (the existing test's case) rather than
  `survey`, and states in the GIVEN that without `--retry` the failed outcome is returned, which the
  test sets up. `step-waits-lock` adds "once the lock is free, running the same command again
  starts the step's run", which the existing test already checks.
- Tests: the real detached `task-validation` test now verifies `step-starts-command`; the lock
  test verifies `step-waits-lock` and gains an assertion that nothing is recorded; the combined
  cached/retry test and the lost test were each split in two (new tests
  `test_retry_runs_a_failed_step_again`, `test_a_key_reported_lost_keeps_its_finished_run`, the
  latter also asserting no lost problem for the key). `step-starts` keeps the in-process test only.
- Verified: tests/concorde/workflows 39 passed; spec-validation success with no findings.

### B · F23 — Usage walkthrough and resume (done, commit 451841c7)
- Inserted after the launch example: a module.shop normal path (eight steps and their keys, the
  report `reports/1.json`/`.md`) and an interactive one-pause resume on `d.db-helper` with the
  relaunch arguments, the step `survey@<digest>` with `--answers` and `--input` = first survey run,
  and what it supersedes. The `binding_required` sentence moved up to the launch paragraph; the
  answers/retry/restart paragraph now follows the resume, unchanged.
- Decision: the example answer reuses Adoption's `d.db-helper` question and "a Module of its own"
  answer, so the examples across Modules agree. No existing statement was changed.

### C · F22 — brownfield procedure diagram (done, commit 451841c7)
- Added a `d2 illustrative` flow beside the step table: normal arrows the path, dashed arrows the
  stops to the report, labelled with each mode's condition as the table states it. Compiled with
  the d2 CLI. The "broken" stops (no answer from a step agent, a step still running) are left out
  of the picture, as the table leaves them out; they are stated in the script and prose.

### Environment note (non-ok, handled)
- The first `uv sync`/`npm ci`/build ran in background Bash and its writes to the worktree did not
  persist (`bwrap: Can't find source path .../.git/config.lock`); re-ran `uv sync` and the build in
  the foreground, which worked. `uvx ruff` needed `UV_TOOL_DIR` under `$TMPDIR` because
  `~/.local/share/uv/tools` is read-only in the sandbox.

### Validation and delivery
- `task-validation`: ok, ready, no blocking findings. `delivery`: ok, delivery commit
  699268c01ef3 with `.concorde/evidence/panel-larger-workflows/1.json`.

## Closed: merged, 2026-09-28T19:54:29Z

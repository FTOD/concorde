# Decision log: panel-larger-execution

Goal: Finish the 2026-09-28 panel review's larger items for Execution and Workers: rename the runner's numbered steps, add the runner activity and progress-file phase diagrams, and split Workers' bundled scenarios with their tests' @verifies

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

**module.execution**
- C · F17+F18: one diagram: runner activity, including the detached hand-off.
- D · F19: the runner's numbered "steps" collide with an Operation's steps. Choose a word for the runner's rows (not "phase", which clashes with the `phase` field of the run progress file). Touches the table and several requirements that reference "Steps 6 and 7" and similar. If the choice isn't obvious, escalate to the main agent with options and a recommendation before renaming.

**module.workers**
- A · F11: split `backend-configured` into default pi / configured resolution / `backend_missing`; split `configure-refused` into Save refusals / command admission refusals.
- C · F26: progress-file phase transitions diagram.

### Verdict text for each item (from the review's verification agents)

#### module.execution

##### F17 LARGER — runner activity view
Real, advisory. After F6/F7 settle, add a `d2 illustrative` activity diagram beside the runner table in runner.md. It shows parse and binding/records selection, then create the run directory and run progress file, then lock (bound only), admit, execute steps, compose/check, and write/release/print. Parse failures branch to "exit 2, no result"; refusals, a raised step and signals converge on steps 6–7. Launcher and runner lanes appear only for the detached handoff.

##### F18 LARGER — detached handoff diagram
Real but covered by F17's detached lanes. Recommend drawing it once as part of F17 rather than as a second diagram; the paragraph was also clarified by F6/F16.

##### F19 LARGER — "step" overloaded, "definition" undefined
Partly fixed. The runner.md intro now defines the run's definition: "The Operation or execution command a command line names is the run's definition: its steps, its arguments, whether it may run unbound and its output contract."

Renaming the runner's numbered rows needs a word choice and touches the table, "Steps 6 and 7", "steps 2 to 4" and several requirements. "Phase" collides with the run progress file's `phase` field, so the renaming is left open. Possible names are "stage" or "runner step" (the progress field `step` is the definition's step).



#### module.workers

##### F11 LARGER — scenarios that bundle several situations
Confirmed for scenario.workers.backend-configured (populated config vs "empty configuration"; both programs installed vs `pi` missing) and scenario.workers.configure-refused (Save refusals vs command-admission `invalid_request` refusals). Split backend-configured into (a) default pi backend with an empty configuration, (b) configured resolution across pi/Claude Code, (c) missing-backend refusal `backend_missing`. Split configure-refused into (a) Save validation refusal, (b) concurrent external change refusal, (c) admission refusals (`invalid_request`, exit 2). The new scenario ids need matching `verifies` declarations in tests/concorde/harness/workers/ (not owned here), so this has to be done together with the tests.

##### F26 LARGER — progress-file phases have no transition view
This is real, but the fix is a new `d2 illustrative` state view next to the Progress file table in launch.md: preparing -> worker -> audit -> checks -> worker (resume on failing checks or validation), and worker/audit/checks -> finished, each edge labelled (violation, invalid or non-ok result, checks pass, rounds used up, timeout, interrupted). The brief counts a new diagram as LARGER.



## Escalated to the main agent, 2026-09-28T19:43:54Z

- **task-session** task session (task panel-larger-execution): `runner_row_word`
  F19: the Runner table in specs/concorde/execution/runner.md numbers its rows as 'steps' (1-7), which collides with a definition's steps (row 5 'Execute the definition's steps', the progress file's 'step' field, host-error evidence 'naming the step'). References to the numbered rows exist only in runner.md itself ('Steps 6 and 7', 'steps 2 to 4', 'refused at step 3', 'as step 1 does'); no code, test or other Spec cites them. 'phase' is excluded (run progress file field). 'stage' is otherwise used only as Check execution's run_checks(stage='work'|'readiness') argument and for Git staging in Delivery and Views, neither about the runner.
  Not handled here (decision): The brief reserves a non-obvious word choice for the main agent; the new word becomes the name every Execution document and diagram uses for the runner's rows.
  Options: stage: column 'Stage', rows referenced as 'stages 6 and 7', each stage also given a short name (parse, binding check, lock, admission, execution, composition, finish) used by the runner activity diagram; runner step: keep 'step' with a qualifier; short references ('step 3') stay ambiguous with the definition's steps and the progress file's step field; no count noun: name the rows only (parse, binding check, lock, admission, execution, composition, finish) and cite them by name
  Recommendation: stage, numbered and named: it is distinct from 'step' and 'phase', its other uses are in unrelated contexts, and names make the activity diagram and cross-references readable

```json
{
  "level": "task-session",
  "actor": "task session (task panel-larger-execution)",
  "code": "runner_row_word",
  "detail": "F19: the Runner table in specs/concorde/execution/runner.md numbers its rows as 'steps' (1-7), which collides with a definition's steps (row 5 'Execute the definition's steps', the progress file's 'step' field, host-error evidence 'naming the step'). References to the numbered rows exist only in runner.md itself ('Steps 6 and 7', 'steps 2 to 4', 'refused at step 3', 'as step 1 does'); no code, test or other Spec cites them. 'phase' is excluded (run progress file field). 'stage' is otherwise used only as Check execution's run_checks(stage='work'|'readiness') argument and for Git staging in Delivery and Views, neither about the runner.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The brief reserves a non-obvious word choice for the main agent; the new word becomes the name every Execution document and diagram uses for the runner's rows."
  },
  "options": [
    "stage: column 'Stage', rows referenced as 'stages 6 and 7', each stage also given a short name (parse, binding check, lock, admission, execution, composition, finish) used by the runner activity diagram",
    "runner step: keep 'step' with a qualifier; short references ('step 3') stay ambiguous with the definition's steps and the progress file's step field",
    "no count noun: name the rows only (parse, binding check, lock, admission, execution, composition, finish) and cite them by name"
  ],
  "recommendation": "stage, numbered and named: it is distinct from 'step' and 'phase', its other uses are in unrelated contexts, and names make the activity diagram and cross-references readable",
  "causes": []
}
```

## 2026-09-29 — Main agent on escalation runner_row_word (F19)

- Not decided by the main agent: the handover asks for the developer when the word is not
  obvious, and "stage" (the session's recommendation) is already used inside Execution's subtree
  (Check execution's `run_checks(stage=...)`, the timing metadata's `stage` label, Delivery's Git
  staging). Brought to the developer with a recommendation for option 3 (named rows, cited by
  name) and "stage" as the alternative. The session continues the other items meanwhile.

## Task session log (2026-09-29)

- **F19 (runner row word)**: escalated as #1 (`runner_row_word`) with options stage / runner step /
  named rows only; the main agent took it to the developer and asked to leave the renaming open.
  Renaming not done until the answer arrives.
- **F11, `configure-refused` half: skipped.** The scenario no longer exists: commit f99b9dff
  removed the configure-workers command, its terminal editor and its scenarios (the worker
  configuration is now the Git-tracked `.concorde/workers.json`, edited directly). Nothing to split.
- **F11, `backend-configured` split (commit "Workers: split backend-configured …").** Decided
  without the developer: the original id `scenario.workers.backend-configured` keeps the configured
  resolution (reviewer on pi with the default's model, checker on Claude Code without the pi model),
  since its title "Workers run on pi unless their configuration chooses Claude Code" names exactly
  that; the new ids are `scenario.workers.backend-default` (empty configuration → pi) and
  `scenario.workers.backend-missing` (`backend_missing`, never falls back, the Claude Code worker
  still resolves). The existing test in tests/concorde/harness/workers/test_models.py (listed by
  module.workers) was split into three tests with one `@verifies` each; every assertion was kept.
  No statement of the old scenario was dropped.
- **F26 (commit "Workers: draw the progress file's phase transitions").** A `d2 illustrative`
  state diagram after the Progress file table in launch.md, checked against
  src/concorde/harness/workers.py: timeout, limits and process failures are detected after the
  `audit` phase is set, so their edges leave `audit`; `launch_failed` leaves `worker`; validation
  without checks can resume from `audit`. Interruption from any phase is said in prose rather than
  drawn as five edges.
- **F17+F18 (commit "Execution: draw the runner's activity …").** One `d2 illustrative` diagram
  before the Runner table in runner.md, with the detaching command and the runner as containers,
  nodes labelled by the row names the main agent suggested (parse, binding check, lock, admission,
  execution, composition, finish), which fit every option of escalation #1. The table itself is
  unchanged until F19 is decided.

## 2026-09-29 — Main agent: F19 deferred

- Decision (mine): the developer has not yet answered runner_row_word; the session delivers every
  other item now and F19's rename is carried out in a follow-up task once the developer decides,
  so the other items do not wait. The runner activity diagram labels its nodes by row names,
  which fit every option.
- **F19 left open.** The main agent asked me to deliver without it because the developer has not
  yet answered escalation #1. The runner table keeps its "Step" wording. The rename is left for a
  follow-up task once the developer decides.
- Verification before delivery: `build --check` clean, `spec-validation` 0 errors / 0 warnings,
  full suite 690 passed, 4 skipped.

## Review fixes from the main agent (2026-09-29)

- **(Blocking) launch.md progress diagram.** The last edge label was unquoted, so D2 cut it at the
  first `;` and drew "no rounds left" and "checks unavailable" as orphan nodes. I did not look at
  the rendered image before the first delivery; I should have. Fixed by quoting it and splitting it
  into two edges `checks -> finished`, one labelled status ok (checks pass, nothing to repair, or no
  rounds left for a repair) and one labelled status failed (a check still failing with no rounds
  left, or checks unavailable). Decided without the developer: a failed end is still drawn into
  `finished`, with the status in the label, not as a separate "failed" state. The progress file's
  `phase` has no failed value: `finished` carries `status`, and the code
  (harness/progress.py `finish`) sets `phase: finished` for every ending. Re-rendered and checked
  the image: no orphan nodes.
- **runner.md.** The detaching command's exit-2 edge now says "malformed, unknown or outside Git",
  as `detach()` calls `parse()` and `_worktree()` (runner.py:588-590).
- **runner.md, optional item taken.** The signal handlers are installed before the binding check
  and `Cancelled` is caught around the lock, checkout, admission and steps (runner.py:366-398). I
  stated this in the lead sentence rather than adding four edges, and removed "or a signal" from
  the execution edge.

## Closed: merged, 2026-09-28T20:43:46Z

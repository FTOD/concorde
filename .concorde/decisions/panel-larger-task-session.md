# Decision log: panel-larger-task-session

Goal: Finish the 2026-09-28 panel review's larger items for Task session and Main session: split their bundled scenarios with their tests' @verifies, and add the pi task session and pi run view state diagrams

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

**module.task-session**
- A · F27: split `start`, `pi-rounds`, `pi-stop` (append refusals); the version-1 clause of `pi-report-shape`.
- C · F12: the pi task session state diagram.

**module.main-session**
- A · F4: split `pi-run-view`, `project-terms`, `pi-model-picker`, `pi-task-worktree`, `pi-task-session-view`.
- C · F24: the pi run view lifecycle diagram.

### Verdict text for each item (from the review's verification agents)

#### module.task-session

##### F12 LARGER — No state view of a pi task session's lifecycle
To do: add an illustrative d2 state view next to the pi outcome table in Usage. States: no session, round running, round ended (delivered, escalated, failed, stopped). Transitions: start, `--answer` and `--stop`, with the refusals `session_busy`, `no_session` and `session_idle`. Alternatively, move the Design sequence diagram beside the pi normal path. The prose already has all the facts; only readability is at stake.

##### F27 LARGER — Scenarios combine several situations
This is real: start, pi-rounds and pi-stop append refusals, and pi-report-shape ends with an unrelated clause about persisted version 1 reports. Splitting them needs new scenario ids, and the tests (`tests/concorde/tasks/test_pi_session.py`, `test_session.py`) would have to re-declare `@verifies` for the moved cases. Those tests are outside my files, and a scenario with no verifying test would add coverage warnings.
To do:
- move pi-report-shape's version-1 clause into its own scenario (e.g. `scenario.task-session.pi-report-v1`), verified by test_persisted_v1_reports_are_not_revalidated_or_rewritten;
- optionally split the Claude `--answer`/`--stop` refusal out of `start` (test_a_claude_code_session_takes_no_answer_or_stop);
- optionally split the busy/idle refusals out of pi-rounds and pi-stop, updating their tests in the same change.


#### module.main-session

##### F4 LARGER — Runtime scenarios fold several situations into one
This is real: pi-run-view's GIVEN is a single Operation run, but its THEN steps assert outcomes for commands, unbound runs, finished runs and dead runners. project-terms, pi-model-picker, pi-task-worktree and pi-task-session-view have the same problem. Splitting them needs new scenario ids. The tests in tests/concorde/main_session/test_pi_run_view.py (lines 116, 138, 176, 245, 343, 453, 489) and test_pi_model_picker.py carry `@verifies` on the old ids and would have to move to the new ids. Those tests are outside my owned files, and new scenarios without tests would raise coverage warnings. Proposed split for pi-run-view: active worker display and attribution, execution-command display, unbound display, normal completion and wake message, lost runner. project-terms: readable glossary vs. no or unreadable glossary. pi-model-picker: named task vs. no task vs. missing worktree vs. RPC/headless. Keep the old id on the first part of each split and update the `@verifies` markers.

##### F24 LARGER — Dense run-view lifecycle paragraph needs a flow view
This is a real readability gap, but it needs a new diagram. Add a `d2 illustrative` flow beside the run-view paragraph: concorde_run → task worktree resolved (or refused) → detached `concorde` start → run progress file and worker progress read → FleetView entry → run ends → wake (steered into the current turn, or a new turn). Include a branch "already finished → answered in the tool result, no message".



## Task session log (2026-09-29)

### Items checked against the current Specs and code

- **module.task-session F27** — still real. Done: `start` keeps its id and its `session_failed`
  case (same action, same command); the Claude Code `--answer`/`--stop`/`--wait` refusal moved to
  `scenario.task-session.claude-no-rounds`; the busy refusals of `pi-rounds` to
  `scenario.task-session.pi-busy` (answer and a second start, both `session_busy`, as the contract
  already lists); the `no_session` answer to `scenario.task-session.pi-no-session`; `pi-stop`'s idle
  refusal to `scenario.task-session.pi-stop-idle`; `pi-report-shape`'s version 1 clause to
  `scenario.task-session.pi-report-v1`.
- **module.task-session F12** — done: an illustrative d2 state view after the pi refusals
  paragraph in Usage (no session → round running → round ended: delivered/escalated/failed/stopped,
  with `--answer`/start back to running and the refusals `no_session`, `session_busy`,
  `session_idle` as self-loops).
- **module.main-session F4** — still real, except `pi-model-picker`, which no longer exists in
  the Specs, code or tests (skipped for that reason). Done: `pi-run-view` keeps the worker display
  and attribution; new `pi-run-view-command`, `pi-run-view-unbound`, `pi-run-finished` (status,
  summary and wake message with or without an error chain), `pi-run-lost` (no run lock) and
  `pi-run-discovered` (runs started elsewhere, the old last two clauses). `project-terms` split
  off `project-terms-missing`; `pi-task-worktree` split off `pi-task-worktree-missing`;
  `pi-task-session-view` split off `pi-task-session-wake`.
- **module.main-session F24** — done: an illustrative d2 flow after the run view paragraph:
  `concorde_run` → task worktree (or refused) → detached `concorde` → answered in the tool result
  when already finished, otherwise followed (joined by runs found in the run store) → FleetView →
  run ends or runner lost → wake message steered into the current turn or starting the next.

### Decisions taken without the developer

- New scenario ids and titles as listed above (naming). Each new scenario only restates what the
  old bundled scenario, the Module's Usage prose or its contracts already said; no promise was
  narrowed or widened, except that two diagram labels were aligned with the contracts
  (`no_session` for `--answer`/`--wait`, not `--stop`, since the contract lists only those).
- `pi-wait` lost its clause "and for a Claude Code session with `invalid_input`": that refusal is
  now stated in `claude-no-rounds`, whose test actually checks it (the `pi-wait` test checked
  `--wait --stop` under pi instead). `pi-wait`'s own `no_session` refusal was left in place, since
  it was not in the handover list.
- Tests: where one test covered several new scenarios it was split (busy / no-session,
  finished / lost runner, command / unbound, task worktree found / missing); a stop-idle test was
  added that waits for round 1 to end and checks the record is unchanged; the busy test now also
  checks the refusal names the round and its supervisor process, as the new scenario says. The
  missing-worktree test checks `taskWorktree` returns null and that `pi_extension.ts` refuses,
  naming the task, before it spawns (a source check, as `OwnedWorkTests` already does, since the
  extension needs a live pi). `pi-task-session-view` and `pi-task-session-wake` share one test,
  which checks both.
- Diagrams render with ELK as the docsite does; the first task-session state draft was redrawn
  left-to-right because the top-down layout crossed most edges.
- No file outside the task's two Modules was changed (the tests are those Modules' files).

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review verdict MERGE-WITH-NOTES. Sent back before merging: N1 (pi-report-v1's GIVEN
  narrowed the version-1 clause to delivered reports; contracts.md:52 has escalated v1 reports
  without `commit`), plus two diagram accuracy points (FleetView drawn as required although the
  prose says the wake works without pi-subagents; the "elsewhere" node omits runs discovered at
  session start).
- Not decided, brought to the developer (N2, predates this task): pi_session.py stop() refuses
  `--stop` with `no_session` when the task has no pi session, while contracts.md lists
  `no_session` only for `--answer`/`--wait` and module.md says `--stop` with no round gives
  `session_idle`.

### Review fixes from the main agent (after delivery 1)

- N1 (required): `pi-report-v1`'s GIVEN said a version 1 report "has no `escalations` field", which
  held only for delivered version 1 reports (contracts.md: an escalated one lacked `commit`), so it
  narrowed the old clause. Reworded: version 1 reports have only the fields of their status, no
  `escalations` when delivered, no `commit` when escalated. `test_persisted_v1_reports_are_not_revalidated_or_rewritten`
  now records an escalated and a delivered version 1 report and checks both stay unchanged.
- Run view flow: FleetView is now a side branch labelled "with pi-subagents", and the wake
  follows directly from following the run, as the prose says the wake works without pi-subagents.
- Run view flow: the discovered-run node now also names runs still running when the session
  started, matching `pi-run-discovered`.
- N2 (`--stop` refused with `no_session` in code but not in the contract) left alone, as the main
  agent is taking it to the developer.

## Closed: merged, 2026-09-28T19:58:54Z

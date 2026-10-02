# Decision log: final-obvious-fixes

Goal: Resolve the last four open obvious-fix Issues: headless sessions see lobby runs, Operations check workers against the model map at admission, Harness runtime-path wording, Workflows' host_ended cause

## Brief (main agent, 2026-10-02)

The last four open Issues of the project, all obvious-fix, recorded by the round of fix tasks
merged today. Read each with `python3 scripts/concorde.py issues show <id>`, check it still
stands, and fix it alone:

- I-44783e3c34bb50f8aa91132201519140 (module.headless-sessions, medium): sessions.py run_folders
  misses the run store's lobby (`.concorde/lobby/<run-id>/`, from run-lock-before-records), so a
  headless session is not woken for a run it left queued with --wait.
- I-815328180f205b579a0af51869e10731 (module.operations, medium): fix-workers made Workers'
  check_mapped take the Operation (whole-configuration map check at admission, decided by the
  main agent for I-88e8ba4c); no Operation calls it yet. Call it at admission, before the first
  worker launches, refusing with one model_unmapped listing every gap. If the call site must be in
  Execution's runner rather than Operations, escalate instead.
- I-cdea0b0e8dc858abab58cec25d37c2f4 (module.harness, low): align the Harness's runtime-path
  wording with Workers' input (every read-only path beside the grant as the caller lists them).
- I-1cb80f6b196b5245b747245ff8b87315 (module.workflows, low): define step_lost's cause host_ended
  in Workflows' contracts.

Start with the full suite as a baseline (seven tasks merged today). Change only the bound
Modules; escalate anything else, all together at the end. Verify with build --check,
spec-validation and the full suite, then task-validation and delivery, and report.

## Task session decisions (2026-10-02)

- Baseline before any change: full suite 949 passed, 5 skipped.
- All four Issues still stood at the base commit (read with `issues show`).
- I-815328180f205b579a0af51869e10731: the call site stays in Operations, not Execution's runner.
  `src/concorde/operations/catalog.py` `provider()` (through which the runner loads every
  Operation) puts a first step `check_worker_models` (new `src/concorde/operations/admission.py`)
  before the provider's own steps of every Operation that has a task type. It calls
  `models.check_mapped(load(worktree), operation=<name>)` and stops `failed` with
  `worker_model_unavailable`, the configuration reader's refusal (one `model_unmapped` for the map)
  as its one cause. Reason: it runs once the run is admitted and before any worker launches,
  without changing Execution's code. As a result a configuration that cannot be read or is not valid
  now also stops at that first step instead of at the first worker step; `backend_missing` and
  `model_unresolved` are still met at each worker's launch, as Workers' entry leaves them.
  Spec: Operations workers.md ("Worker backend and model"), new
  req.operations.models-placed-first, new scenario.operations.worker-models-checked-at-admission,
  "and the run reaches the worker step" dropped from the config-invalid and unmapped scenarios.
  Operations had no test realization; added realization.operations.tests
  (`tests/concorde/operations/`) for the new test.
- I-44783e3c34bb50f8aa91132201519140: `sessions.run_folders` now adds `lobby/r-*`; the Headless
  sessions entry names the lobby; scenario.headless-sessions.unsettled and its test gain a run
  queued in the lobby.
- I-cdea0b0e8dc858abab58cec25d37c2f4: Harness module.md defines the runtime paths as the
  read-only material every tool may read, linking Workers' "Reading beside the grant".
- I-1cb80f6b196b5245b747245ff8b87315: Workflows contracts.md's `step_lost` row names its cause
  `host_ended` (actor, reason, detail).

## Escalated to the main agent, 2026-10-02T03:04:47Z

- **task-session** task session (task final-obvious-fixes): `out_of_scope_test_update`
  The fix of I-815328180f205b579a0af51869e10731 adds the step check_worker_models, which Operations' catalog puts first in every Operation that launches workers (committed f083183d). tests/concorde/execution/test_runner.py::RunnerTests::test_the_progress_file_follows_the_run (line ~720) asserts the run's steps are exactly ['worker_step'] and now sees ['check_worker_models', 'worker_step']. That file belongs to module.execution (realization.execution.runner), which this task does not bind. The fix is one line: expect ['check_worker_models', 'worker_step']. Every other runner test passes; full suite otherwise 949 passed.
  Not handled here (decision): the brief allows changes only in the bound Modules and asks to escalate anything else
  Options: allow this task to change that one assertion in module.execution's test; add module.execution to the task; have Operations' check not be a separate step (it would then run inside Execution's worker launch, which the brief said to escalate)
  Recommendation: allow the one-line test change in this task

```json
{
  "level": "task-session",
  "actor": "task session (task final-obvious-fixes)",
  "code": "out_of_scope_test_update",
  "detail": "The fix of I-815328180f205b579a0af51869e10731 adds the step check_worker_models, which Operations' catalog puts first in every Operation that launches workers (committed f083183d). tests/concorde/execution/test_runner.py::RunnerTests::test_the_progress_file_follows_the_run (line ~720) asserts the run's steps are exactly ['worker_step'] and now sees ['check_worker_models', 'worker_step']. That file belongs to module.execution (realization.execution.runner), which this task does not bind. The fix is one line: expect ['check_worker_models', 'worker_step']. Every other runner test passes; full suite otherwise 949 passed.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the brief allows changes only in the bound Modules and asks to escalate anything else"
  },
  "options": [
    "allow this task to change that one assertion in module.execution's test",
    "add module.execution to the task",
    "have Operations' check not be a separate step (it would then run inside Execution's worker launch, which the brief said to escalate)"
  ],
  "recommendation": "allow the one-line test change in this task",
  "causes": []
}
```

## Escalated to the main agent, 2026-10-02T03:04:54Z

- **task-session** task session (task final-obvious-fixes): `out_of_scope_e2e_update`
  The fix of I-44783e3c34bb50f8aa91132201519140 adds the lobby (.concorde/lobby/r-*) to scripts/e2e/sessions.py run_folders, as the Issue suggested. scripts/e2e/e2e.py watch() (module.e2e, realization.e2e.tool, lines ~428-434) already adds the lobby itself on top of sessions.run_folders, so a run in the lobby is now listed twice, and tests/concorde/e2e/test_e2e.py::E2ETests::test_watch_reads_run_progress_and_workflow_records fails. The fix is in module.e2e, which this task does not bind: delete watch's own lobby glob and iterate sessions.run_folders(project) alone (about 6 lines removed, docstring kept).
  Not handled here (decision): the brief allows changes only in the bound Modules and asks to escalate anything else
  Options: allow this task to remove watch's own lobby glob in scripts/e2e/e2e.py (module.e2e); add module.e2e to the task; keep sessions.run_folders without the lobby and add it only inside sessions' unsettled_runs, run_folder and wait_for
  Recommendation: allow the removal in this task: run_folders is then the one list of the run store's folders that both use

```json
{
  "level": "task-session",
  "actor": "task session (task final-obvious-fixes)",
  "code": "out_of_scope_e2e_update",
  "detail": "The fix of I-44783e3c34bb50f8aa91132201519140 adds the lobby (.concorde/lobby/r-*) to scripts/e2e/sessions.py run_folders, as the Issue suggested. scripts/e2e/e2e.py watch() (module.e2e, realization.e2e.tool, lines ~428-434) already adds the lobby itself on top of sessions.run_folders, so a run in the lobby is now listed twice, and tests/concorde/e2e/test_e2e.py::E2ETests::test_watch_reads_run_progress_and_workflow_records fails. The fix is in module.e2e, which this task does not bind: delete watch's own lobby glob and iterate sessions.run_folders(project) alone (about 6 lines removed, docstring kept).",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "the brief allows changes only in the bound Modules and asks to escalate anything else"
  },
  "options": [
    "allow this task to remove watch's own lobby glob in scripts/e2e/e2e.py (module.e2e)",
    "add module.e2e to the task",
    "keep sessions.run_folders without the lobby and add it only inside sessions' unsettled_runs, run_folder and wait_for"
  ],
  "recommendation": "allow the removal in this task: run_folders is then the one list of the run store's folders that both use",
  "causes": []
}
```

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T03:05:07Z

final-obvious-fixes: all four fixes are committed on the task branch (f083183d). Delivery waits on two escalations, each asking to change one file in a Module this task does not bind.

Done (build --check ok, spec-validation ok with 0 errors; the 2 warnings are in adoption and spec-mcp, not this task):
- I-815328180f205b579a0af51869e10731 (Operations): the call site is in Operations, not Execution. catalog.provider() puts a first step, check_worker_models (new src/concorde/operations/admission.py), before the provider's own steps of every Operation that has a task type. It calls models.check_mapped(load(worktree), operation=<name>) and stops failed with worker_model_unavailable, with one model_unmapped listing every gap as its cause. Side effect: a worker configuration that is invalid or missing now also stops at this first step, not at the first worker. backend_missing and model_unresolved are still caught at each worker's own launch. Spec changes: workers.md, new req.operations.models-placed-first, new scenario.operations.worker-models-checked-at-admission, and a new realization.operations.tests (tests/concorde/operations/), since Operations had no tests of its own.
- I-44783e3c34bb50f8aa91132201519140 (Headless sessions): run_folders includes lobby/r-*. The entry, scenario.headless-sessions.unsettled and its test now cover a run queued in the lobby.
- I-cdea0b0e8dc858abab58cec25d37c2f4 (Harness): runtime paths are now defined as read-only material that every tool may read, with a link to Workers' "Reading beside the grant".
- I-1cb80f6b196b5245b747245ff8b87315 (Workflows): the step_lost row now defines its cause, host_ended (actor, reason environment, detail).

Full suite: 949 passed, 5 skipped, 2 failed. Both failures are in files of Modules this task does not bind, so I escalated them:

Escalation 1:
- **task-session** task session (task final-obvious-fixes): `out_of_scope_test_update`
  tests/concorde/execution/test_runner.py::test_the_progress_file_follows_the_run (module.execution) expects the steps ['worker_step'] and now sees ['check_worker_models', 'worker_step']. The fix is one line.
  Options: allow the one-line change in this task; add module.execution to the task; make the check not a separate step (it would then live in Execution's worker launch).
  Recommendation: allow the one-line test change in this task.

Escalation 2:
- **task-session** task session (task final-obvious-fixes): `out_of_scope_e2e_update`
  scripts/e2e/e2e.py watch() (module.e2e) already adds the lobby on top of sessions.run_folders, so a lobby run is now listed twice and test_e2e.py::test_watch_reads_run_progress_and_workflow_records fails. The fix removes watch's own lobby glob (about 6 lines).
  Options: allow that removal in this task; add module.e2e to the task; keep run_folders without the lobby and add it only inside sessions' own readers.
  Recommendation: allow the removal in this task.

Once you answer both, I'll apply the changes, run the full suite, task-validation and delivery, and resolve the four Issues with task resolve.

It carries escalation(s) 1, 2.

## Answer to report(s) 1 of the task session, 2026-10-02T03:05:27Z

Escalations 1 and 2, decided by the main agent: allow both changes in this task, since no other task is open and each follows directly from this task's fixes. (1) Update the expected steps in tests/concorde/execution/test_runner.py::test_the_progress_file_follows_the_run (module.execution) to ['check_worker_models', 'worker_step']. (2) Remove watch()'s own lobby glob in scripts/e2e/e2e.py (module.e2e), now that sessions.run_folders includes the lobby. Then run the full suite, task-validation and delivery, resolve the four Issues and report.

- (task session) Applied the main agent's answer to report 1: test_runner.py expects
  ['check_worker_models', 'worker_step']; e2e.py watch() drops its own lobby glob. Full suite
  951 passed, 5 skipped; build --check clean.

## Report 2 to the main agent (spec-review quality criteria), 2026-10-02T03:11:09Z

final-obvious-fixes (report 2, answering your answer to report 1): delivered as e274e797 on concorde/final-obvious-fixes, ready to merge.

As you allowed: test_runner.py::test_the_progress_file_follows_the_run now expects ['check_worker_models', 'worker_step'], and e2e.py watch() no longer adds the lobby itself (f450add8). Results: full suite 951 passed, 5 skipped; build --check clean; spec-validation 0 errors (the 2 warnings are in adoption and spec-mcp, not this task); task-validation ready; delivery ok.

The task resolves (added with task resolve): I-44783e3c34bb50f8aa91132201519140, I-815328180f205b579a0af51869e10731, I-cdea0b0e8dc858abab58cec25d37c2f4, I-1cb80f6b196b5245b747245ff8b87315.

Decisions I made on my own, all in the decision log, as described in report 1:
- The map check is the first step of every Operation that has a task type, placed by Operations' catalog.
- A worker configuration that is missing or invalid now also fails at that step.
- Operations now has its own tests realization.

Nothing is open.

## Closed: merged, 2026-10-02T03:11:24Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit e274e797172ca1324455e2c40dbd347caee06145 into main and closed it as merged. Nobody answers a report after that.

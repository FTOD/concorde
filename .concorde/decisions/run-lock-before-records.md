# Decision log: run-lock-before-records

Goal: Take the workspace lock before a bound run writes into its workspace folder, revalidate the binding and lock after acquiring it, and keep waiting and refused runs' records outside the workspace folder so task close never races a run

## Brief (main agent, 2026-10-01)

Resolves Issue I-e896126f3c1e59a498fd925a4390be53 ("Pre-admission record writes are not
coordinated with workspace closure", severity high, tier decision-needed). Read the Issue with
`python3 scripts/concorde.py issues show I-e896126f3c1e59a498fd925a4390be53` first. The project
MCP server's Issue tools of the main session currently refuse every record with
`invalid_issue` (`severity: unknown field`), most likely a stale server process; use the
`issues` command of your worktree.

Direction (the developer asked why the runner does not take the workspace lock first; the main
agent proposed the design below and the developer did not object; the main agent decided to
carry it out):

- A bound run takes the workspace lock before it writes anything into the workspace folder: no
  run node folder, `trace.json` or run progress file in the workspace folder before the lock is
  held. The binding is still read first, since it selects the locks directory.
- After acquiring the lock the runner revalidates: the lock file it holds is still the one at the
  lock's path (close removes the workspace lock file, so a waiter can end up holding a deleted
  inode), and the binding still exists and names the same workspace. Otherwise the run is
  refused, with a new refusal code.
- A run waiting for the lock and a run refused before admission keep their state and result
  outside the workspace folder, for example beside the run lock under the locks directory, so
  that close moving the workspace folder never races them; the detached launcher's announcement
  waits on that, not on a progress file inside the workspace folder.
- Execution still never reads the task store: the hand-off goes through the binding, the locks
  and the workspace folder alone.

Left to the task session (record each choice here): the exact place and shape of the
pre-admission records and how a refused run's result is found afterwards (the announced result
location), how Tasks' close retires the binding while holding the lock, how Tracing's lock
table and the trace tree describe it, the refusal codes, and a concurrent-close scenario with
tests. module.workflows is also named by the Issue: escalate if it must change. Another task
that will move the unbound checkout into `.claude/worktrees/` waits for this one to merge, so
do not change the unbound checkout's location here.

## Task session: design decisions (2026-10-01)

- **Lobby.** A bound run's trace node starts in a new Tracing folder `.concorde/lobby/<run>/` of the
  binding's `concorde`, never in the workspace folder: the run lock, first `trace.json`, run progress
  file and a detached runner's `host.out` are written there. Reason: outside the folder close moves,
  in a folder of its own rather than under `locks/` (which holds locks and nothing else, and whose
  directory lock watchers observe). Unbound runs and runs whose binding is broken keep
  `unbound/<run>/` as today.
- **Entering the workspace.** Once the run holds the workspace lock and the revalidation passed,
  the runner renames its lobby folder to its node folder in the workspace folder (`runs/<run>/` or
  the `--trace-at` folder); an open `host.out` follows the rename. If the two folders lie on
  different file systems it copies, removes the lobby folder and points its own output at the
  moved `host.out`. A move that fails is refused with the new code `run_store_unwritable`.
- **Revalidation, code `workspace_retired`.** After taking the workspace lock the runner refuses
  with `workspace_retired` when the lock file it holds is no longer the file at the lock's path
  (Tracing's lock library gains a mode that reports a removed or replaced file instead of taking
  the new one), or when the binding re-read from the worktree is gone, unreadable or differs from
  the one read at the parse. Reason `environment`.
- **Refused before the lock.** A bound run refused in the binding check, the lock or the
  revalidation keeps its node, with `result.json`, in the lobby. The detached announcement keeps
  `trace`, `progress` and `result` as the node in the workspace folder (where an admitted run's
  result is) and gains `lobby`, the lobby folder (null for an unbound run), where a run refused
  before it held the lock keeps its result. Every reader by run identity (the run store's `find`,
  Tracing's `locate`, so `run_result`, `trace show`, `task wait --run`, workflow steps) also looks
  in the lobby. The launcher's announcement waits for the progress file in the lobby or in the
  workspace node.
- **Close.** Tasks' close already retires the binding (it removes the worktree, which holds it)
  and removes the workspace lock file while holding the lock. It now also: stops runs waiting in
  the lobby for its workspace (they are runs of the workspace), and, while holding the workspace
  lock and before moving the folder, moves every lobby run of the workspace that has ended into
  `runs/<run>/` of the workspace folder (through an Execution function), so the history keeps
  them. A run that still waits stays in the lobby and is refused `workspace_retired` there.
- **Retention.** An ended lobby run is removed after `unbound_days`, like an unbound run.
- `.concorde/lobby/` joins the folders Git ignores (Tracing's `IGNORED`, this checkout's
  `.gitignore`).
- **Revision of the Close point above.** Close does not move ended lobby runs into the workspace
  folder: `req.tasks.no-foreign-writes` forbids Tasks to write the run store, and the move would
  be such a write. Instead a run refused before it held the workspace lock never entered its
  workspace: it stays in the lobby, is found by its identity, and is removed by retention. The runs
  of a workspace (`task show`, the derived state) are those in its workspace folder plus the runs
  still waiting in the lobby for its lock. Close also stops (SIGTERM) the waiting runs of its
  workspace it can see, as it stops the running ones; it writes nothing of theirs.
- **Refusal codes.** `workspace_retired` (reason `environment`, cause actor `Execution (workspace
  binding)`) covers all three retirements: the lock file removed or replaced while the run waited,
  the binding gone or untrusted, the binding changed. `run_store_unwritable` (reason `environment`)
  when the lobby node cannot be moved into the workspace folder.
- **Contract version.** `contract.tracing.configuration` goes to version 3: `unbound_days` now also
  governs the runs of the lobby.
- **Outside the task's Modules (root Module).** Added `.concorde/lobby/` to this checkout's
  `.gitignore` (without it the lobby's files would be untracked changes of the primary worktree,
  which `task merge` audits) and one row for it to the "Where things live" table of
  `docs/using-concorde.md`. Installed projects get the `.gitignore` line from Tracing's `IGNORED`
  through the installer. Both are mechanical consequences of the layout change; flagged in the
  report.
- **Verification.** `build --check`, `spec-validation` (0 findings) and the execution, tasks,
  tracing, workflows and project MCP suites pass; new tests: runner `workspace_retired` (lock file
  removed, binding gone, binding changed), Tasks concurrent close with a detached waiting run,
  Tracing lobby lookup and retention.

## Escalated to the main agent, 2026-10-01T15:39:20Z

- **task-session** task session (task run-lock-before-records): `workflow_writes_before_workspace_lock`
  Issue I-e896126f3c1e59a498fd925a4390be53 also names module.workflows, and its part is not fixed by this task. A workflow step (src/concorde/workflows/step.py run_step, store.py) holds only the workflow lock, never the workspace lock, while it creates the step's folder (next_step_folder + mkdir(parents=True)), writes answers and records the step in the workspace folder, and _end_step_node writes there again after the run. Tasks' close holds the workspace lock, not the workflow lock, while it moves the workspace folder, and then removes the workflow lock file without holding it (store._move_to_history). So a step that runs during a close can recreate .concorde/tasks/<task>/workspace/workflow/... after the move (an orphan folder) or write a step record into a folder being moved, and a step waiting for the workflow lock retakes a fresh file after close removed it. The runner's own records are now safe: a step's run waits in the lobby and is refused workspace_retired. Fixing the rest changes Workflows code (outside this task's Modules) and Tasks' close.
  Not handled here (scope): module.workflows is not one of this task's Modules, and the brief says to escalate if Workflows must change; the fix also changes what Workflows promises about its locks.
  Options: Merge this task as delivered and open a separate task for module.workflows and module.tasks: close takes the workflow lock while it holds the workspace lock and removes the workflow lock file while holding it; a step takes the workflow lock without retaking a removed file (Tracing's retake=False) and checks its binding again after taking it, refusing the step when the workspace was retired; Extend this task to module.workflows and make the same change here before delivering again; Accept the Workflows race for now and record it as its own Issue against module.workflows
  Recommendation: The first: this task is delivered and complete for Execution, Tasks and Tracing, and another task waits for its merge; the Workflows change is self-contained and deserves its own review. I can file the Issue for module.workflows if you prefer that over opening the task at once.

```json
{
  "level": "task-session",
  "actor": "task session (task run-lock-before-records)",
  "code": "workflow_writes_before_workspace_lock",
  "detail": "Issue I-e896126f3c1e59a498fd925a4390be53 also names module.workflows, and its part is not fixed by this task. A workflow step (src/concorde/workflows/step.py run_step, store.py) holds only the workflow lock, never the workspace lock, while it creates the step's folder (next_step_folder + mkdir(parents=True)), writes answers and records the step in the workspace folder, and _end_step_node writes there again after the run. Tasks' close holds the workspace lock, not the workflow lock, while it moves the workspace folder, and then removes the workflow lock file without holding it (store._move_to_history). So a step that runs during a close can recreate .concorde/tasks/<task>/workspace/workflow/... after the move (an orphan folder) or write a step record into a folder being moved, and a step waiting for the workflow lock retakes a fresh file after close removed it. The runner's own records are now safe: a step's run waits in the lobby and is refused workspace_retired. Fixing the rest changes Workflows code (outside this task's Modules) and Tasks' close.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "scope",
    "explanation": "module.workflows is not one of this task's Modules, and the brief says to escalate if Workflows must change; the fix also changes what Workflows promises about its locks."
  },
  "options": [
    "Merge this task as delivered and open a separate task for module.workflows and module.tasks: close takes the workflow lock while it holds the workspace lock and removes the workflow lock file while holding it; a step takes the workflow lock without retaking a removed file (Tracing's retake=False) and checks its binding again after taking it, refusing the step when the workspace was retired",
    "Extend this task to module.workflows and make the same change here before delivering again",
    "Accept the Workflows race for now and record it as its own Issue against module.workflows"
  ],
  "recommendation": "The first: this task is delivered and complete for Execution, Tasks and Tracing, and another task waits for its merge; the Workflows change is self-contained and deserves its own review. I can file the Issue for module.workflows if you prefer that over opening the task at once.",
  "causes": []
}
```

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T15:51:57Z

Task run-lock-before-records delivered: delivery commit c55947a19679 (run r-20261001T154521-delivery-44c14d48, ok) on concorde/run-lock-before-records, on top of 36fbdf75. task-validation r-20261001T153909-task_validation-e8070059: ready. Full test suite: 879 passed, 4 skipped; build --check ok; spec-validation 0 findings. Resolves I-e896126f3c1e59a498fd925a4390be53 for Execution, Tasks and Tracing (already listed in the task's resolves); its Workflows part is escalation 1 below.

What changed:
- Lobby: a bound run's trace node starts in `.concorde/lobby/<run-id>/` of the binding's `.concorde`: its first trace.json, its run progress file while it waits and a detached runner's host.out. Nothing is written into the workspace folder before the run holds the workspace lock. Once it holds the lock it re-reads the binding and renames the lobby folder into `runs/<run-id>/` (or the --trace-at folder); host.out moves with it.
- Revalidation: new refusal `workspace_retired` (reason environment, actor `Execution (workspace binding)`) when the lock file was removed or replaced while the run waited (Tracing's lock library gains `retake=False` / LockGone, so the run never takes the new file), or when the binding is gone, untrusted or changed. New `run_store_unwritable` when the node cannot be moved.
- Refused runs: a run refused or cancelled before it entered its workspace keeps its node and result in the lobby. The detached announcement keeps trace/progress/result as the workspace node and gains `lobby`. Lookups by run identity (Store.find, Tracing's locate, so run_result, trace show, task wait --run and workflow steps) also search the lobby. A workspace's runs are its folder's runs plus the runs still waiting in the lobby. Retention removes ended lobby runs after unbound_days (contract.tracing.configuration v3).
- Tasks: close also SIGTERMs the runs waiting in the lobby for its workspace. It does not move lobby runs, because req.tasks.no-foreign-writes forbids Tasks to write the run store. A run it cannot see is refused workspace_retired once close releases the lock it removed.
- Specs: Execution runner/module/requirements/scenarios (new req.execution.lobby, req.execution.workspace-retired, scenario.execution.workspace-retired); Tasks module/requirements/contracts plus scenario.tasks.close-retires-waiting-run; Tracing layout, node kinds, lock table, retention, reader and scenarios; glossary "run store". Tests cover each, including a real concurrent close with a detached waiting run.

Decisions I made (all in the decision log): the folder name `lobby` instead of a place under `locks/`; one code workspace_retired for all three retirement causes; the shape of the announcement; close stops but never moves lobby runs.

Outside the task's Modules (root Module), flagged for you: I added `.concorde/lobby/` to this checkout's .gitignore. Without it, lobby files would be untracked changes of the primary worktree, which task merge audits. Installed projects get the line from Tracing's IGNORED. I also added one row to the "Where things live" table of docs/using-concorde.md.

New Issue: I-bf910bc0c2545086b07dc6c8f091d840 (module.distribution, obvious-fix, low). Update's active-run refusal finds a lobby run through its run lock but doesn't name its progress file.

Still open, escalation 1 (workflow_writes_before_workspace_lock), the decision I need:
A workflow step writes its step folder, answers and step record into the workspace folder holding only the workflow lock. Close moves that folder holding only the workspace lock, then removes the workflow lock file without holding it. A step running during a close can therefore recreate an orphan `tasks/<task>/workspace/...` or write into the folder being moved. The runner's own writes are now safe. Options: (1, recommended) merge this task and open a separate task for module.workflows and module.tasks: close takes the workflow lock and removes its file while holding it; a step takes the workflow lock with retake=False and re-checks its binding. (2) Extend this task to module.workflows. (3) Accept the race and record it as an Issue. Rendered chain:
- **task-session** task session (task run-lock-before-records): `workflow_writes_before_workspace_lock` — see the decision log, escalation 1, for the full detail, options and recommendation.

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-01T15:52:53Z

Escalation 1 (workflow_writes_before_workspace_lock): option 1, decided by the main agent (task split, ordinary scope). This task merges as delivered; a separate task for module.workflows and module.tasks will make close take the workflow lock and remove its file while holding it, and a step take the workflow lock with retake=False and re-check its binding. The .gitignore line and the docs/using-concorde.md row outside the task's Modules are accepted.

## Closed: merged, 2026-10-01T15:52:59Z

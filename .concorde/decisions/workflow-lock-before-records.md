# Decision log: workflow-lock-before-records

Goal: Make workflow steps safe against task close: close takes the workflow lock and removes its file while holding it, and a step takes the workflow lock without retaking a removed file and re-checks its binding before writing into the workspace folder

## Brief (main agent, 2026-10-01)

Resolves I-6943ae8b6ead514e88f10764ed734e39 (high, preferred-fix: workflow steps write into the
workspace folder while task close moves it) and I-cb5cbc676e2157899756e7541a95bbfd (low,
obvious-fix: Workflows says a step's run is the project MCP server's own child). Read both with
`python3 scripts/concorde.py issues show <id>` first.

Background: task run-lock-before-records (merged 676b274f) made the runner safe: a bound run
starts in `.concorde/lobby/<run-id>/`, takes the workspace lock before writing into the
workspace folder, and is refused `workspace_retired` when the lock file was removed or replaced
while it waited (Tracing's lock library `retake=False` / LockGone) or the binding is gone or
changed. Its session escalated the workflow layer (escalation 1,
workflow_writes_before_workspace_lock); the main agent chose its option 1, this task.

Direction (main agent, ordinary scope):
- Tasks' close takes the workflow lock as well and removes the workflow lock file while holding
  it, as it does the workspace lock.
- A workflow step takes the workflow lock with `retake=False` and re-checks its binding after
  acquiring it, before writing anything into the workspace folder; a retired workspace refuses
  the step the way the runner refuses a run (`workspace_retired`), with its error chain.
- Add a concurrent-close scenario for a workflow step and test it.
- Reword Workflows' "The run it starts is the server's own child" to match module.main-session's
  Current code section (per-call processes since mcp-fresh-code, merged a3d61208).

Left to the task session (record each choice here): the lock order between the workflow and
workspace locks (avoid deadlock with steps that hold the workflow lock while their run takes the
workspace lock), where a refused step's record goes, and the refusal shape. Do not touch Tasks'
`task open --path` (I-6adb5521ad3a5c55a39350c714193f22), which is a later task. Escalate any
change another Module would need.

## Decisions (task session, 2026-10-01)

- **Lock order: workspace lock, then merge lock, then workflow lock; the workflow lock is a leaf.**
  `task close` and `task merge` take the workflow lock inside `close_locked`, after the workspace
  and merge locks they already hold, and wait for it without a bound. A workflow step and report
  hold the workflow lock only for work that waits for no other lock: the step no longer waits for
  the workspace lock to be free while holding the workflow lock, but releases it, waits, and takes
  it again (looking the key up again). Reason: with the step waiting for the workspace lock under
  the workflow lock, a close holding the workspace lock and waiting for the workflow lock would
  stall until the step's `--wait` ended (forever without one). Taking the workflow lock inside
  `close_locked` puts it on both the close and the merge path without changing how the project MCP
  server's `task_merge` takes and hands on the workspace and merge locks (module.main-session),
  and closing and merging the same task exclude each other through the workspace lock first.
- **The step's workflow lock is taken with `retake=False` in `store.step_lock`, used by the step,
  the end of a step's node and the report alike**, and after acquiring it the binding is read again
  and compared with the one the command read: gone, untrusted or changed, or a lock file removed or
  replaced while waiting, refuses with `workspace_retired` (WorkflowError subclass
  `WorkspaceRetired`) before anything is written into the workspace folder.
- **A refused step's record goes nowhere**: its workspace folder is retired (in the history), so
  the step outcome, state `refused`, carries the workflow's `workspace_retired` link (reason
  `environment`) over a component link of the workflow lock naming what was found, and nothing is
  written. A step whose run had started and whose node could not be ended because the workspace
  was retired meanwhile is refused the same way, naming the run. `concorde workflow report` in a
  retired workspace prints the component link `workspace_retired` with reason `environment`.
- A lock file a late step creates afresh after the close (binding already gone) is left as an
  empty, free file; it is harmless and the next close of a task of that name removes it.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-01T16:09:50Z

Task workflow-lock-before-records delivered: delivery commit 3a1f7d603637dae02ef8175948c9d755ebd5b113 on concorde/workflow-lock-before-records (work commit 1f7c3173). task-validation ready; build --check and spec-validation clean; full suite 893 passed, 4 skipped.

Resolves I-6943ae8b6ead514e88f10764ed734e39 (preferred-fix, done with the chosen fix) and I-cb5cbc676e2157899756e7541a95bbfd (obvious-fix): both already in the task's resolves.

What changed:
- Tasks: close_locked (both task close and the close that ends task merge) takes the task's workflow lock after the workspace and merge locks, waits for it without a bound, holds it from before the worktree removal until it has moved the folder and removed the lock file.
- Workflows: step_lock takes the workflow lock with retake=False and re-reads the binding once held; a removed/replaced lock file or a binding gone, untrusted or changed refuses with workspace_retired (cause: Workflows (workflow lock) link lock_removed / binding_gone / binding_untrusted / binding_changed) before anything is written. Step, end of a step's node and report all go through it (report now builds and saves under the lock). A step no longer waits for the workspace lock while holding the workflow lock. Step outcome contract 4 -> 5. brownfield.js treats workspace_retired like step_rejected (outcome travels with the result).
- Reworded "The run it starts is the server's own child" to the per-call process of main-session's Current code.
- New scenarios with tests: scenario.workflows.step-retired (real task close while a step waits; binding-changed case) and scenario.tasks.close-takes-workflow-lock (close waits for a step holding the lock); new reqs req.workflows.workspace-retired and req.tasks.workflow-lock-last.

Decisions I took (in the decision log): lock order workspace -> merge -> workflow, with the workflow lock a leaf (nobody waits for another lock while holding it), so no deadlock and no change to how the MCP task_merge takes and hands on its locks (module.main-session untouched); a refused step is recorded nowhere, its outcome alone carries the chain; a lock file a late step creates afresh after the close is left as an empty free file.

Still open: Tracing's lock tables (contracts.md line 539, module.md line 215) still describe the workflow lock without the close holding it and without a waiting step being refused. Still true but incomplete, and outside this task's Modules: recorded as Issue I-69624b561d515152854b98adce317251 (module.tracing, obvious-fix, low). Nothing needs a decision.

## Closed: merged, 2026-10-01T16:10:19Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 3a1f7d603637dae02ef8175948c9d755ebd5b113 into main and closed it as merged. Nobody answers a report after that.

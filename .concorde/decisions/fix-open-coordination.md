# Decision log: fix-open-coordination

Goal: Fix the open Issues of the coordination part (Tasks, Task sessions, Main session)

## Brief (main agent, 2026-10-04)

### Context

The developer asked (2026-10-04) to try to resolve the project's open Issues, after the parts
refactor merged into `main` (decision logs of parts-*, fix-* and parts-review* in
`.concorde/decisions/`). Every open Issue was reviewed and classified then; none is high or
critical. Nine tasks run in parallel, one per part or group of parts: fix-open-spec,
fix-open-method, fix-open-execution, fix-open-coordination, fix-open-worker-harness,
fix-open-kernel, fix-open-workflows, fix-open-root-distribution, fix-open-issues-e2e.

### How to work

- Your Issues are listed below with severity and tier; read each with `concorde issues show`
  (the latest report is the verified one). Work on them most severe first.
- **obvious-fix and preferred-fix**: fix them (preferred-fix: record which fix you chose and why).
  **decision-needed**: the main agent's decisions are below; carry them out. **suggestion**: fix it
  when it is cheap and clearly improves the Spec or code; otherwise leave it open.
- After fixing an Issue, add it to this task with `concorde task resolve <task> <issue>`: the
  merge closes exactly the Issues the task resolves, so add none you did not fix. Close an Issue
  that does not hold yourself (`not-actionable`, with the reason) or as `duplicate`. If a fix needs
  a decision with major impact, or another group's files beyond a small edit, escalate it with any
  others together rather than deciding it.
- Work directly in the Specs, code and tests; no Operation or review is needed. Keep edits of files
  other groups may touch small (glossary, registry mirror, shared tests, guidance composition); on a
  merge conflict the main agent asks you to merge `main` in.
- Introduce no regression: every part still works installed with only its dependencies
  (`tests/concorde/acceptance/test_parts.py`), the part-dependency check passes, guidance reads
  correctly whichever parts are installed (`tests/concorde/distribution/test_guidance_parts.py`).
  Rapid-iteration rule: no shims or compatibility paths.
- Verify with `build --check`, `spec-validation` and the full suite, then `task-validation` and
  `delivery`, and report: resolved, closed as not holding, left open (and why).

### Decisions of the main agent for your decision-needed Issues

- I-99210f06 (merge of a head already in the primary branch): specify and keep the path: no merge commit is needed, the merge still runs its checks on the primary head, records that the head was already contained, and closes the task as merged with its decision log committed.
- I-4d868c47 (`task wait --until merging`): `merging` is a transient state held under the workspace lock, so it is no longer awaitable: refuse it in `task wait` and `register_wait` with a clear message, and update the guidance that lists awaitable states.

### Your 28 Issues

- I-688f53082ee45483bc3ab9e31f00ab85 (medium, preferred-fix, module.task-session): Task-session write hook allows Edit/Write through a final symlink pointing outside the task
- I-dbf1b166da435bbfb5f0942a996481a0 (medium, preferred-fix, module.task-session): A session launched but not recorded keeps running untracked
- I-fea062499256529c9f27cbb3164bdd56 (medium, preferred-fix, module.tasks): A failed closing trace write leaves the record closed, a misleading refusal and a retry that never ends the trace node
- I-a01870e921d9540abdf9b206937cdbf4 (medium, obvious-fix, module.tasks): merge --abort runs git merge --abort before checking the branch and head belong to the task's merge
- I-99210f068cce5a4fb6a75244657f1642 (low, decision-needed, module.tasks): task merge of a head already in the primary branch succeeds without the promised merge commit
- I-4d868c470a6e52cea85f65318d232eec (low, decision-needed, module.tasks): task wait --until merging can miss the merging state
- I-6ae6de44494d5e2ea1f8d30a6f941886 (low, preferred-fix, module.main-session): Short MCP writes wait on the per-task record lock although the no-wait promise names any lock
- I-a70d4bd8b8675e7c860e0a00ff50c6c4 (low, preferred-fix, module.main-session): run_result answers for any trace node, e.g. a task name, instead of unknown_run
- I-59b3f8bf0d5456d7a3ee23992f2b0cb5 (low, preferred-fix, module.tasks): report, answer and escalate append to the decision log after releasing the task lock, racing a close
- I-20595beb30e75982a761c616448ab945 (low, obvious-fix, module.task-session): Session cleanup warnings keep only the last 2000 characters of Claude Code's answer
- I-93777b64a6665976bdd47980313744e9 (low, obvious-fix, module.main-session): trace_show refusals differ in actor, options and node_unreadable explanation from `concorde trace show`
- I-70b1d803a7995b3589fae0fa30459f10 (low, obvious-fix, module.main-session): register_wait's immediate answers do not have the shape `concorde task wait` prints
- I-491abf1c236f508aab32ffd4c396b2ed (low, obvious-fix, module.main-session): Merge fallback requirement still names the workspace-lock wait
- I-f806f2c0b9d85caba734261c2f8764ac (low, obvious-fix, module.tasks): A timed-out merge or delivery check loses its captured output
- I-e2c864996633541da02fdb96f68e8ecc (low, obvious-fix, module.tasks): Closing seals the decision log's trace digest before appending the closing
- I-c753ff5069eb5667b766eb77280b541d (low, obvious-fix, module.tasks): close --completed/--failed stops the task's sessions and runs before it refuses merge_incomplete
- I-a4b0ed7d679c5bc8979bc120d2cca318 (low, obvious-fix, module.tasks): req.tasks.escalation-kept says escalations are kept in the task record, which has no such field
- I-472ba18cc6175fe291cc1faa8cf2361f (low, obvious-fix, module.tasks): Tasks promises the whole task folder is kept in the history, but close deletes runtime/
- I-9975f2d1d6e0594c99b253ab17e11706 (low, obvious-fix, module.tasks): scenario.tasks.old-record still expects schema_version 4 after the rebind
- I-2c901be9b7315c8fa49970995829f71a (low, obvious-fix, module.tasks): task open leaves branch, worktree and task folder behind when writing the record or log fails
- I-8cb9eeb6947b5fa7b79980d3e1bcceb7 (low, obvious-fix, module.tasks): Tasks promises a concurrent unlocked record change is never overwritten, which compare-then-rename cannot guarantee
- I-6552098a819b5c7db28d73ad411ddbef (low, obvious-fix, module.tasks): Tasks promises a concurrent record change is never overwritten, beyond what Kernel transactions guarantee
- I-18f7b9fd914f57a99153362879a5226d (low, obvious-fix, module.coordination): Coordination's agent table and rationale extend the task-session write boundary to the shell
- I-aa144f57342f5abb8a357d01596dcb17 (low, obvious-fix, module.coordination): Coordination says an unbound review 'changes nothing', omitting the Issues it may publish
- I-900476aaee025d7d8c00edaf050c5ad7 (low, obvious-fix, module.coordination): Core concepts omits the approved-small-change exception
- I-d807e712299f556b9ed70e6152f7e867 (low, obvious-fix, module.task-session): Task-session guidance does not say to leave the worktree untouched while any run of it runs
- I-096f3e21ab275f05af9abaa405f5105b (low, suggestion, module.task-session): MCP approval discovery: Spec says 'up to the filesystem root', code deliberately excludes the root
- I-3d97ae071991597cb899b0a52cdc4b40 (low, suggestion, module.main-session): run_result has no behavioural tests

## Task session decisions, 2026-10-04

Worked directly in Specs, code and tests, most severe first; no Operation was run.

- I-688f5308 (preferred-fix): chose to resolve the whole path, final link included, in the
  task-session write hook (Edit and Write write through a link, so a link is judged by its
  target), rather than stating the worker harness's "link judged by its own name" rule, which would
  have kept the gap. Spec (task-session module, contracts, scenario) and test updated.
- I-dbf1b166 (preferred-fix): a session `claude --bg` started whose record is refused is removed with
  `claude rm` (which kills it) before the refusal is returned; the refusal says so or names the
  manual `claude rm`. Chosen over recording first, since a session id exists only after the start.
- I-20595beb: `_said` keeps Claude Code's whole answer.
- I-fea06249 (preferred-fix) and I-e2c86499: a close now writes the record, then appends the closing
  and ends the trace node under the task lock (`_finish_ending`), so the node records the log's final
  digest. A refusal after the record update names the stored state and the command that finishes
  it: the same close, or for a merge `concorde task close <task> --merged` once the record is
  closed (merge --resume refuses a task no longer merging). The rerun of a close appends a missing
  closing and ends a node not yet ended. Not handled: a merge attempt node finished only by such a
  rerun stays `running` (its end belongs to the merge's before_move); left as is, an edge case of a
  trace write failure.
- I-59b3f8bf (preferred-fix): report, answer and escalate append to the decision log while still
  holding the task lock; escalate now refuses a task that ended (`task_closed`), as report and
  answer do, so nothing is appended after a closing.
- I-c753ff50: close refuses `merge_incomplete` (only with no live merge holder, as before) and
  `dirty_worktree` (without --force) before stopping any session or run; both are checked again
  under the locks.
- I-a01870e9: merge --abort checks branch, head and that MERGE_HEAD is the task's checked commit
  merged into the commit before the merge, before running `git merge --abort`.
- I-99210f06 (main agent's decision): an already-contained head makes no merge commit; the merge
  runs its checks on the primary head, answers `merge.contained: true`, ends its attempt node with
  outcome `contained` and closes the task as merged, the close committing the log alone. Recorded in
  the answer and node outcome rather than a new merge-trace field, to avoid a typed-value version
  change.
- I-4d868c47 (main agent's decision): `merging` removed from the awaitable states; `task wait` and
  `register_wait` refuse it with invalid_input explaining why and naming `--merge`. register_wait's
  `until` schema now accepts any state string so the wait's own message, not a schema error,
  explains the refusal. Guidance (prompts/main-session/skill.md) updated.
- I-2c901be9: a task open whose trace node, record or log write fails removes the worktree, branch
  and task folder it added and refuses with `record_unwritable` (saying what remains if removal
  failed); it also now checks the trace node's write, which it ignored before.
- I-6ae6de44 (preferred-fix): scoped req.main-session.project-mcp-no-wait to the workspace and merge
  locks; task-record locks are waited for briefly, as the issue's preferred fix proposes.
- I-a70d4bd8 (preferred-fix): run_result refuses `unknown_run` for a node that is not an Execution
  run (kind other than `run`, or no node and no progress or result file). I-3d97ae07: added a
  behavioural test (running, finished, lost, task name, unknown) with its scenario.
- I-93777b64: trace_show refuses with Tracing's own actor, explanation and options, distinguishing
  locate from read errors as `concorde trace show` does.
- I-70b1d803: register_wait's immediate answers carry `waited_seconds` 0 and, for a lock, the
  fields `wait_lock` prints (`lock, task, released, held_by`).
- Spec-only fixes: I-491abf1c, I-472ba18c, I-9975f2d1, I-a4b0ed7d, I-8cb9eeb6 and I-6552098a (one
  wording for both), I-18f7b9fd, I-aa144f57, I-900476aa, I-096f3e21 (Spec aligned with the code:
  the filesystem root is excluded).
- I-d807e712: added req.main-session.task-session-still-during-runs, the guidance sentence and a test.
- I-f806f2c0: a timed-out check's bytes output is decoded and kept.

## Task session decisions after merging main, 2026-10-04

- Merged `main` (with fix-open-kernel and fix-open-root-distribution) into the task branch as the
  main agent asked; no conflict.
- First task-validation (r-20261004T022636-task_validation-e7c0c5ec) was blocked by
  check.views.repository-regressions: esbuild reported `@esbuild/linux-x64` missing inside the check
  sandbox. The package is present; the same check run directly passed 259/259 and the rerun
  r-20261004T023532-task_validation-aaf38269 was ok. Treated as transient; not a defect of this task.
- I-265f20b9 (added by the main agent): `task deliver` answers `warnings` (new field) and `task merge`
  and `merge --abort` add to theirs each refused write of the attempt's or a check's trace node
  (Node.failures); a refusal names them in its detail. `checks.run` now also writes the check's log
  when the node's own write (which made the folder) failed, reporting a refused log write the same
  way; before, a refused node write crashed the delivery with `unexpected_error`.
- `task open` keeps refusing (record_unwritable, undone) when the task's own node cannot be
  written, rather than warning: that node holds the transitions and escalations later task
  commands read and change, so it is the task's state, not only its trace. Stated in the contract.

## Report 1 to the main agent (项目架构分离建议), 2026-10-04T02:54:25Z

fix-open-coordination delivered: delivery commit 80a659b933a27ea845fbd210342922e1423abca7 (delivery run r-20261004T024655-delivery-3dd00710, task-validation r-20261004T023532-task_validation-aaf38269 ok). main was merged in first as asked, without conflict. Full suite 1145 passed / 5 skipped; build --check and spec-validation clean (0 warnings).

Resolved, all 29 added with task resolve: the 28 of the brief plus I-265f20b9. None was closed as not holding; none is left open; nothing to escalate.

Decision-needed, carried out as you decided:
- I-99210f06: a head the primary branch already holds makes no merge commit. The merge runs its checks on the primary head, answers merge.contained true, ends its attempt node with outcome `contained`, and closes the task as merged, committing the log alone. Recorded in the answer and outcome instead of a new merge-trace field, to avoid a typed-value version bump.
- I-4d868c47: `merging` is no longer awaitable. task wait and register_wait refuse it with invalid_input, saying why and naming --merge. register_wait's `until` schema is now plain strings, so this message, not a schema error, explains the refusal. Guidance updated.

Preferred-fix choices:
- I-688f5308: the session hook resolves the whole path, final link included, so a link is judged by its target (Edit and Write write through links).
- I-dbf1b166: a session started but refused its record is removed with `claude rm`, and the refusal says so (or names the manual command).
- I-fea06249 and I-e2c86499: a close writes the record, then appends the closing and ends the trace node under the task lock, so the node keeps the log's final digest. A rerun of the close finishes a missing closing or node end. After the record is closed, a merge's refusal points to `task close --merged`, since --resume refuses a task no longer merging.
- I-59b3f8bf: report, answer and escalate append while holding the task lock. escalate now refuses an ended task with task_closed.
- I-6ae6de44: the no-wait promise now covers only the workspace and merge locks; task-record locks are waited for briefly.
- I-a70d4bd8: run_result refuses unknown_run for any node that is not an Execution run.

Other notable changes:
- close refuses merge_incomplete and dirty_worktree before stopping sessions or runs.
- merge --abort checks branch, head and MERGE_HEAD before aborting.
- task open removes its worktree, branch and folder when its node, record or log write fails, and refuses record_unwritable. It keeps refusing (not warning) for its own node, since that node holds the task's transitions and escalations.
- task deliver gains `warnings`, and merge, merge --abort and refusals report trace-write failures. This fixed a crash: a refused check-node write made deliver fail with unexpected_error, because the check log's folder was missing.
- New requirement req.main-session.task-session-still-during-runs, with guidance and a test (I-d807e712).

Left open:
- A merge attempt node finished only by a rerun `task close --merged` (after a trace write failure) stays `running`; this is an edge case.
- The first task-validation was blocked by check.views.repository-regressions: esbuild reported @esbuild/linux-x64 missing inside the check sandbox. The package is present, the check passed run directly (259/259), and the rerun was ok. I treated it as transient and reported no Issue; worth watching if it recurs.

Every decision is in the decision log.

## Closed: merged, 2026-10-04T02:54:46Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 80a659b933a27ea845fbd210342922e1423abca7 into main and closed it as merged. Nobody answers a report after that.

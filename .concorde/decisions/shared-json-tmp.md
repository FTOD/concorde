# Decision log: shared-json-tmp

Goal: Give each write of a worker progress file and of a run's status file its own temporary file, fsynced then renamed, as the Kernel's binding writes do since I-986b963e, so overlapping writers never publish a torn file or fail a rename (Issue I-63c45a9b)

## Task brief (main agent, 2026-10-29)

**Issue resolved.** I-63c45a9b36ed5caba43e8f817fcb51ce (module.execution, medium, preferred-fix).
`src/concorde/worker_harness/progress.py` (around line 74, module.workers) and
`src/concorde/execution/runner.py` (around line 990, module.execution) write their JSON through
one shared `<file>.json.tmp` path. Two overlapping writers of a worker's progress file or a run's
status file can then publish a torn or wrong file, or fail a rename.

**The fix to follow.** Task r4-kernel-tracing fixed the same pattern in the Kernel's binding writes
(I-986b963e, commit 61953d456 "kernel: each binding write has a temporary file of its own"):
- each write gets its own `mkstemp` file in the same directory;
- the file is fsynced, then renamed over the target;
- the temporary file is removed on failure.
Read that change and `.concorde/decisions/r4-kernel-tracing.md` (around lines 188 and 383).

**What the main agent adds (its own decisions).**
- Search both Modules for any other shared fixed temporary path written the same way, and fix those
  too. Record what you found.
- If both Modules can reasonably share one helper, prefer one, placed where the Module
  dependencies allow it. A Module must not start using a Module it does not already use. If no
  shared place fits, keep one small helper per Module. Record the choice.
- Readers must never see a partial file. Keep every existing promise about the progress file and
  the run progress file, such as their shapes and when they change. If a Spec states the shared
  `.tmp` path or the write mechanism, update it.
- Note for parallel work: task protocol-used-bound (module.spec, a Protocol change) runs at the
  same time. Touch no Protocol or Spec-core file.

**Verification.** Add a test that fails on the old code, with overlapping writers of each file, as
r4-kernel-tracing's overlap test does for the binding. Then run the full suite, `build --check`
and `spec-validation`. Then run `task-validation` and `delivery` from the task worktree.

**Environment notes.**
- uv, node/npm, pi, rg, fd and d2 are installed under `/home/scratch.zbai_gpu/opt`.
- Keep large files off `$HOME` (5 GB quota).

**Left to the session.** The mechanism details, the helper's place and the tests. Escalate together
anything that would change another Module's promises.

## Task session decisions, 2026-10-29

- **Search for other shared fixed temporary paths.** Searched every implementation file of
  module.execution (realization.execution.runner) and module.workers (realization.workers.*) for
  `.tmp`, `with_suffix`, `replace`/`rename`, `mkstemp` and direct `write_text`/`write_bytes`.
  Only the two reported sites write through a shared fixed temporary path:
  `worker_harness/progress.py` (`Progress._write`) and `execution/runner.py` (`_progress`). The
  runner's result writes already went through `_publish`, a temporary file of their own from
  `mkstemp`, but without fsync. Every other write in both Modules writes a file that only one
  writer creates in a fresh folder (grant, brief, settings, logs), with no temporary path; the
  lobby-to-workspace move is a directory rename, not a temporary file. Nothing else to fix.
- **Helper place: one small helper per Module.** The only Modules both use are Tracing and
  Distribution. Neither offers a general atomic file write in its library (Tracing's `node.write`
  writes only a checked `trace.json`), and adding one would change another Module's library,
  which this task may not. Execution never uses Workers nor the reverse. So Execution keeps its
  `_publish` in `runner.py`, now used by `_progress` too, and Workers gets the same `_publish` in
  `progress.py`.
- **Mechanism.** Each write: `mkstemp` beside the target (`.<stem>-XXXX.tmp`, as `_publish`
  already named it), write, flush, `fsync`, close, `os.replace`. On any failure, including a
  signal's exception, only that write's own temporary file is removed, a refused removal is
  suppressed so the original error travels on. After a successful rename nothing is unlinked, so
  a later writer that drew the same name never loses its file (the old `finally` of `_publish`
  could). fsync now also applies to `result.json`, which `_publish` writes: a stronger
  durability, no change of promise.
- **No Spec change.** Workers' launch.md ("The host rewrites it atomically") and Execution's
  runner.md ("The runner writes `status.json` atomically") already promise what the fix restores;
  neither names the `.tmp` path or the mechanism. Shapes and write times are unchanged.
- **Tests.** New `RunProgressWriteTests` (test_runner.py) and `ProgressFileTests`
  (test_workers.py): overlapping writers with the second write run whole between the first's
  write and its rename, the fsync before the rename, and a refused write leaving no temporary
  file. All six fail on the old code (the runner's first rename fails with FileNotFoundError, the
  worker's file ends with the other writer's state, no fsync, a leftover `status.json.tmp`) and
  pass with the fix. `test_a_result_that_cannot_be_saved_is_printed_and_the_run_is_lost` patched
  `_publish` to refuse every write; it now refuses only `result.json`, since the run progress file
  is published through the same helper and its first write must succeed, which keeps the test's
  meaning.
- **Verification.** Commit b9114216f. `build --check` clean; `spec-validation` success, 0 errors,
  5 warnings (the old sentence-length warnings in Spec tooling's scenarios; no Spec changed);
  full suite 1646 passed, 6 skipped. `task-validation` r-20261029T033452-task_validation-79c8f526
  `ok`, ready, 28 checks passed; its run folder holds a whole `finished` `status.json` and no
  temporary file.

## Report 1 to the main agent (项目中途停止状态检查), 2026-10-29T03:53:18Z

shared-json-tmp is delivered: delivery commit 26df7527b9b9d9bfbd8a4879c62d5d3d561aed3c on concorde/shared-json-tmp (run r-20261029T034404-delivery-105da429 ok). The fix is commit b9114216f, on base 61612950f. It resolves I-63c45a9b (preferred-fix, already in the task's resolves).

Fix: the worker progress file (worker_harness/progress.py Progress._write) and the run progress file (execution/runner.py _progress) no longer share status.json.tmp. Each write goes through a mkstemp file beside the target, which is flushed, fsynced, closed and then renamed. On failure, including a signal's exception, only that write's own file is removed, and a refused removal never hides the original error. The shapes and write times of both files are unchanged, and no Spec changed: launch.md and runner.md already promise atomic rewrites and name no .tmp path.

Decisions I made (all in the decision log):
1. Search: in every implementation file of both Modules, only the two reported sites used a shared fixed temporary path. The runner's result.json already had its own mkstemp file through _publish, but without fsync. Nothing else to fix.
2. Helper place: one small helper per Module. The only Modules both use are Tracing and Distribution. Neither offers a general atomic write, and adding one would change another Module's library. Execution's existing _publish now fsyncs, no longer unlinks after a successful rename, and is used by _progress. Workers gets the same _publish in progress.py.
3. Side effect: result.json writes are now fsynced too. That makes them more durable and changes no promise.
4. Tests: new RunProgressWriteTests in test_runner.py and ProgressFileTests in test_workers.py. They cover overlapping writers (the second write runs whole between the first's write and its rename), fsync before the rename, and a refused write leaving no temporary file. All six fail on the old code: the runner's rename fails with FileNotFoundError, the worker file ends up holding the other writer's state, there is no fsync, and status.json.tmp is left behind. All six pass with the fix. One existing test, test_a_result_that_cannot_be_saved_is_printed_and_the_run_is_lost, patched _publish to refuse every write. It now refuses only result.json, which keeps its meaning, because the run progress file now goes through the same helper.

Verification: build --check clean. spec-validation success with 0 errors and 5 old sentence-length warnings in Spec tooling's scenarios. Full suite 1646 passed, 6 skipped. task-validation r-20261029T033452-task_validation-79c8f526 ok, ready, 28 checks passed, and its run folder holds a whole finished status.json and no temporary file.

Open: nothing. No escalations. No Protocol or Spec file touched (parallel task protocol-used-bound unaffected).

## Closed: merged, 2026-10-29T03:53:47Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 26df7527b9b9d9bfbd8a4879c62d5d3d561aed3c into main and closed it as merged. Nobody answers a report after that.

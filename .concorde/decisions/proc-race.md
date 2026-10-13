# Decision log: proc-race

Goal: Execution's pid_alive and Workers' timeout test treat a process in state Z or X as ended, so they no longer race init's reaping

## Task brief (main agent, 2026-10-14)

Resolves I-069a8e8f (module.execution: pid_alive and the runner test) and I-4898cef0
(module.workers: the timeout test), both found by task flaky-and-wording: the same /proc race whose
cause it established for I-4bb624fc (a process being reaped by init shows state X, and reading
/proc a second time counted it as alive). Apply the same rule: a process in state Z or X is ended,
and an assertion uses one observation, not a second read. Check whether pid_alive's behaviour change
matters to its callers (run lock holders, detached runners) and state it in Execution's Spec if it
is a promise. Reproduce under load before and after (as flaky-and-wording did) and give the counts.
Deliver with task-validation then delivery; full suite twice.

## Task session (2026-10-14)

- **pid_alive is no promise; no Spec change.** No code in `src/` or `scripts/` calls
  `execution.runs.pid_alive`; only `tests/concorde/execution/test_runner.py` does. Execution's Spec
  never names it. It already says (runner.md, the `host_pid` row; scenario.execution.run-lock) that
  a recorded process identifier is never a sign that a run still runs: run lock holders and
  detached runners are told by the run lock (`runner_alive` → `locks.held`), which this change does
  not touch. So the behaviour change reaches no caller and needs no Spec text.
- **pid_alive's rule.** A process in state `Z` or `X`, or whose `/proc/<pid>/stat` is gone
  (`FileNotFoundError` or `ProcessLookupError`) after the signal found it, is ended. A
  `PermissionError` from the signal now falls through to the same stat read instead of answering
  True at once, so another user's zombie is ended too. An unreadable stat for another reason
  (`OSError`) or a malformed one still answers True, as before: the signal said the process lives.
  Shown deterministically before the fix: the old `pid_alive` answered True for `X` and for a
  vanished stat.
- **Tests judge one observation.** `test_a_run_lock_exists_only_while_its_runner_runs` and
  `test_a_cancelled_run_ends_its_worker` loop on `pid_alive` and assert the loop's last answer;
  the Workers test `test_a_round_past_its_deadline_is_killed` does the same with a local `alive()`
  helper (as `tests/concorde/project_mcp/test_server.py` has), since Workers does not depend on
  Execution. New `PidAliveTests` check `Z`, `X`, a vanished stat, a real zombie child and a reaped
  child as ended, and `R`, `S`, `D` and an unreadable stat as alive.
- **Reproduction before the fix.** 480 pytest processes of the three tests, 48 at once: 1440 of
  1440 passed (pytest drops repeated node ids, so repetition is by process). 960 processes, 96 at
  once, beside a busy loop on each of the 104 cores: 2878 passed, 2 failed, both in
  `test_a_run_lock_exists_only_while_its_runner_runs` at `holder_pids` returning `[pid, pid]`, a
  different race. The X/vanished race itself did not show in these counts; it is shown by the
  deterministic check above.
- **A second race, outside the task's Modules: recorded as Issue I-855b2ffd4b615171a1088f5e7ef0d48f
  (module.tracing, decision-needed, medium).** `kernel.tracing.locks.holder_pids` reads
  `/proc/locks`, which the kernel serves one page per `read()`; between calls the lock list can
  change, so a lock held throughout can be skipped or repeated. Measured: of 18675 reads of a
  churning table (up to 44691 bytes), a steadily held lock was missing from 2551 and repeated in
  3056. Its caller `stop_task` (task close) can therefore miss a run's runner. I left the Execution
  test's `assertEqual([host_pid], holder_pids(lock))` unchanged: it is right about the promise,
  and loosening it would hide the defect; it stays flaky under heavy load until that Issue is fixed.

## Report 1 to the main agent (Review流程), 2026-10-13T17:10:26Z

Report 1 (proc-race): delivered as 034db5102 (run r-20261013T170108-delivery-297fb6f9), on fix commit 388a76fe4. task-validation: ready, no blocking findings (r-20261013T165129-task_validation-acec053b). Full suite on the final input, twice: 1588 passed, 6 skipped each time. The task resolves I-069a8e8f and I-4898cef0; the merge closes them.

What changed: pid_alive now treats a process in state Z or X, or whose /proc stat vanished after the signal, as ended. A PermissionError from the signal now falls through to the same stat read. The runner tests (run lock, cancelled run) and the Workers timeout test assert the loop's last observation instead of reading /proc again. The Workers test uses a local alive() helper, since Workers does not depend on Execution. New PidAliveTests cover Z, X, a vanished stat, a real zombie child, a reaped child, and R/S/D as alive.

Decided on my own (details in the decision log):
- pid_alive is no promise, so I made no Spec change. Nothing in src/ or scripts/ calls it, only the runner test. Execution's Spec already says host_pid never shows that a run still runs. Run-lock holders and detached runners are told by the run lock (runner_alive -> locks.held), which this change leaves alone.

Reproduction counts:
- Before the fix: 480 pytest processes of the three tests, 48 at once: 1440/1440 passed. 960 processes, 96 at once, beside a busy loop on every core: 2878 passed, 2 failed.
- After the fix, same heavy load: 2879 passed, 1 failed.
- Every failure, before and after, was a different race (below). The X race never showed naturally in these counts. It is shown directly: the old pid_alive answered True for state X and for a vanished stat. Of 2000 processes reaped by init and watched, 43 showed state X.

New Issue, outside the task's Modules: I-855b2ffd4b615171a1088f5e7ef0d48f (module.tracing, decision-needed, medium). kernel.tracing.locks.holder_pids reads /proc/locks, which the kernel serves one page per read() call. Between calls the lock list can change, so a lock held throughout can be skipped or repeated. Measured: of 18675 reads of a churning table (up to 44691 bytes), a steadily held lock was missing from 2551 and repeated in 3056. Consequence: task close's stop_task can miss a run's runner, and the close may then fail with workspace_busy until retried.

I left the Execution test's assertEqual([host_pid], holder_pids(lock)) unchanged. Loosening it would hide the defect, and the test stays flaky only under heavy load until that Issue is fixed. The Issue lists the fix options; I recommend reading the table again until two reads agree, and removing repeated pids.

Still open: I-855b2ffd, for a task on module.tracing.

## Closed: merged, 2026-10-13T17:10:41Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 034db5102b5a2d4c74ddc00ce38070b74dfa2585 into main and closed it as merged. Nobody answers a report after that.

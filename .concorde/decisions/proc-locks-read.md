# Decision log: proc-locks-read

Goal: Tracing's holder_pids reads a consistent /proc/locks table: it reads again until two reads agree and removes repeated pids, so a lock held throughout is never missed or repeated

## Task brief (main agent, 2026-10-14)

Resolves I-855b2ffd (module.tracing, decision-needed, medium; read it with `concorde issues show`).
holder_pids reads /proc/locks, which the kernel serves a page per read(); a lock held throughout can
be skipped or repeated when the table changes between calls (task proc-race measured 2551 misses
and 3056 repeats in 18675 reads of a churning table). Consequence: task close's stop_task can miss a
runner.

Decided by the main agent: the Issue's recommended fix. Read the whole table again until two
consecutive complete reads agree (bounded attempts; when they never agree, say how the caller is
told: a refusal or an explicit "unsure" the callers handle, never a silently partial answer), and
remove repeated pids. State it in Tracing's Spec where locks are described, check the callers
(task close's stop_task, Execution's runner checks) still behave, and add a test that drives a
churning table. Reproduce with the proc-race method before and after and give the counts; the
Execution test assertEqual([host_pid], holder_pids(lock)) should then hold under load.
Deliver with task-validation then delivery; full suite twice.

## Task session decisions (2026-10-14)

- **What "two reads agree" compares: the whole table, not the holders of one file.** Measured
  first with a reproduction of the proc-race method (one process holds one flock; 24 processes take
  and release 40 flocks each in a loop; 30 s of reads; table up to 49 KB). Raw single reads: of
  18776, the held lock was missing from 2908 and repeated in 2037. Simulated on that read stream,
  "read until two consecutive reads give the same holder set" still answered wrong in 413 of 7698
  answers (5 %): a torn read misses the same lock again on the next read, since its place in the
  table hardly moves. Three, four and five agreeing reads gave 80, 19 and 3 wrong answers. Whole-table
  identity gave 0 wrong answers, so holder_pids takes the holders from two consecutive identical
  complete reads: a torn read can only equal the next read if the same changes hit the same page
  boundaries twice.
- **Bound and refusal.** The rereading is bounded by time, `SETTLE` = 1 s (a count would mean very
  different waits for small and large tables). When no two consecutive reads are identical by then,
  holder_pids raises `LockTableUnsettled` (a refusal, never a partial answer) carrying `seen`: every
  pid some read named as a holder, once each, and the read count. A torn read never invents a line,
  so each pid in `seen` held the lock at some moment of the reads.
- **Caller stop_task (module.tasks' store.py, two lines, as the brief asks the callers to handle
  the refusal).** On `LockTableUnsettled` it signals every pid in `seen`: only a run's runner holds
  its run lock, so each such pid is that runner. Tasks' Spec ("each run whose run lock a process of
  this machine holds") is kept, so no Tasks Spec change. No other src caller of holder_pids exists;
  Execution's runner checks (runner_alive, run_state) use `locks.held`, not the table, and are
  unchanged. The Execution test's `assertEqual([host_pid], holder_pids(lock))` is unchanged.
- **Cost accepted.** Under the extreme churn above, whole-table reads never settle: every call
  waits 1 s and refuses (30 of 30 calls; `seen` was exactly the holder in all 30). With a 1 ms pause
  in each churner's cycle: 32 calls, 29 refusals, 0 wrong. With 10 ms: 3585 calls, 0 refusals,
  0 wrong. Normal tables settle on the second read, so a call costs two reads.
- **Spec.** Tracing: contract paragraph "Reading the lock table" under Locks, requirement
  `req.tracing.lock-table-whole`, scenarios `scenario.tracing.lock-table-settled` and
  `scenario.tracing.lock-table-unsettled`.
- **Tests.** Deterministic: a table whose reads miss, repeat, then settle (answer once, 4 reads);
  a table that never settles (refused after ≥ 1 s, `seen` = the holder only). Real: 8 processes
  churning 40 flocks each for 2 s beside a held lock; it failed against the old holder_pids in 3 of 5
  runs (`[pid] != []`, `[pid] != [pid, pid, pid]`) and passed 10 of 10 with the fix.
- **proc-race load before the fix** (Execution test `test_a_run_lock_exists_only_while_its_runner_runs`,
  960 pytest processes, 96 at once, beside a busy loop on each of the 104 cores): 960 passed,
  0 failed; the flake did not show this time (proc-race saw 2 in 2880), so the churn reproduction
  above is the measurement that shows the defect.

## Report 1 to the main agent (Review流程), 2026-10-13T17:59:07Z

Report 1 (proc-locks-read): delivered as 5762f2f3d (run r-20261013T174941-delivery-2c0b0226), on fix commit f43670688. task-validation: ready, no blocking findings (r-20261013T174024-task_validation-733b8679). Full suite on the final input, twice: 1591 passed, 6 skipped each time. The task resolves I-855b2ffd4b615171a1088f5e7ef0d48f; the merge closes it.

What changed: holder_pids reads /proc/locks again until two consecutive complete reads are identical, takes the holders from that read and names each pid once. When no two consecutive reads are identical within SETTLE = 1 s, it raises LockTableUnsettled, carrying `seen` (every pid some read named as a holder, once each) and the read count. It never answers from a read that may be partial. Tracing Spec: a "Reading the lock table" paragraph under Locks in contracts.md, req.tracing.lock-table-whole, and scenarios lock-table-settled and lock-table-unsettled. Tests: two deterministic tables (one that settles after a miss and a repeat, one that never settles) and a real test that churns locks. The real test has 8 processes taking and releasing 40 flocks each beside a held lock. It failed against the old code in 3 of 5 runs ([pid] != [] and [pid] != [pid, pid, pid]) and passed 10 of 10 with the fix.

Decided on my own (details in the decision log):
- "Agree" compares the whole table, not the holder set of one file. Measured with the proc-race churn method (24 processes, 40 flocks each, tables up to 49 KB). Raw single reads missed the lock in 2908 of 18776 and repeated it in 2037. Requiring two reads to agree on the holder set still gave a wrong answer 413 times in 7698 (5%), because a torn read tends to miss the same lock on the next read. Requiring 3, 4 or 5 agreeing reads gave 80, 19 and 3 wrong answers. Comparing whole tables gave 0 wrong answers.
- The bound is time (1 s), not a count of reads. When it runs out, the caller gets a refusal, not a partial answer.
- Callers: stop_task (module.tasks' store.py) needed a two-line change because the brief asks callers to handle the refusal. On LockTableUnsettled it signals every pid in `seen`. Only a run's runner holds its run lock, and a torn read never invents a line, so each of those pids is that runner. Tasks' Spec promise is unchanged, so I made no Tasks Spec change. Execution's runner checks (runner_alive, run_state) use locks.held, not the table, so they are unaffected. I left Execution's assertEqual([host_pid], holder_pids(lock)) unchanged.
- Cost I accepted: under the extreme churn (no pause between cycles) the table never settles. Every call then waits 1 s and refuses: 30 of 30 calls, with `seen` exactly the holder each time and never wrong. With a 1 ms pause per churn cycle: 32 calls, 29 refusals, 0 wrong. With a 10 ms pause: 3585 calls, 0 refusals, 0 wrong. A normal table settles on the second read.

Load measurements on the Execution test test_a_run_lock_exists_only_while_its_runner_runs, using the proc-race method (960 pytest processes, 96 at once, beside a busy loop on each of 104 cores): before the fix 960 passed and 0 failed, so the flake did not show this time (proc-race saw 2 in 2880). After the fix, 960 passed and 0 failed. With 24 processes churning a 31 KB lock table, after the fix: 40 of 40 passed. The churn measurements above are what show the defect and its fix.

Still open: nothing. Pre-existing ruff lint findings in store.py and test_locks.py (import order, SIM117, ISC004) are untouched.

## Closed: merged, 2026-10-13T17:59:25Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 5762f2f3da99aa502bb7d84ff12af385dbfe16e5 into main and closed it as merged. Nobody answers a report after that.

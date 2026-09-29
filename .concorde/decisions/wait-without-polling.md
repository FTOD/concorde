# Decision log: wait-without-polling

Goal: Let waiting agents wait without polling: load Concorde's pi extension in the source checkout's pi sessions, add a blocking --wait to concorde task session for pi task session rounds, add --wait to runs so a busy workspace lock is waited for in-process instead of refused, and tell Claude Code main agents to run task merge in background Bash (or with a long timeout); update AGENTS.md, CLAUDE.md and the main-session guidance to forbid sleep polling.

## Decisions taken without the developer

- **Merged main into the task branch mid-task.** main gained `task-merge-safety` (merge and close
  take the task's workspace lock without waiting) while this task ran; merged before touching the
  same code, no conflicts.
- **`task merge` / `task close` wait for the workspace lock, taken before the merge lock.**
  Options: (a) keep the refusal and only change guidance; (b) wait for the workspace lock while
  holding the merge lock; (c) wait for the workspace lock first, then the merge lock, sharing one
  `--wait` budget. Chose (c): the refusal is exactly what made a pi main agent poll after
  `delivery`; (b) would stall every other task's merge while one task's delivery finishes. Only
  merge and close take both locks, always in the order workspace then merge, so no wait cycle.
  This reverses the "taken without waiting" wording that `task-merge-safety` had just introduced
  in Tasks' Spec (req.tasks.merge-workspace-locked); the invariant it protects (no run changes the
  task while it is merged or closed) is kept. `close` gained `--wait` (default 300) for symmetry.
- **Runs get `--wait <seconds>` with default 0.** Options: default waiting vs. default refusing.
  Kept refusing by default so an accidental overlap (e.g. delivery while implement still runs) is
  still reported; `--wait` queues explicitly. While waiting the run progress file shows step
  `workspace-lock` and a new `waiting_for` field, which the pi run view displays.
- **`concorde task session <task> --wait [<seconds>]` is its own action**, exclusive with
  `--answer`/`--stop`, never starting a round. Considered making `--wait` modify start/answer, but
  `--wait` alone would then be ambiguous (start a new session vs. wait for the running round) and
  could start a session by accident. Waits in-process by rereading the record every second;
  records a lost supervisor like `--answer`/`--stop`. Refused on Claude Code (`invalid_input`),
  whose sessions report through SendMessage.
- **Checkout pi sessions load the extension via a tracked `.pi/settings.json`** pointing at
  `../src/concorde/main_session/pi_extension.ts`, bound in the root Module's development
  environment and documented in `specs/concorde/development.md`. Workers run with
  `--no-extensions`; task sessions keep the run view off (`CONCORDE_TASK_SESSION`).
- **Did not edit the Commands Module's Spec** (outside this task's Modules): its text already says
  every execution command accepts the runner's options even where its usage lines leave them out.

## Non-ok results

- `uvx ruff check` reports 39 pre-existing ISC004/UP035 findings in untouched code; the project
  only requires `ruff format`, which passes. Left as is.
- First tasks/execution test run took 10 minutes: `test_merge_and_close_refuse_a_busy_workspace`
  now waited the default 300 s twice. Changed the test to `--wait 0.3` and added a test that the
  merge waits without holding the merge lock.
- Live check: `pi -p --approve` in the task worktree listed `concorde_run`,
  `concorde_task_session`, `concorde_configure_workers`, so the extension loads. The print-mode pi
  then did not exit (timeout 124), while the same extension in an empty directory exits 0: the
  extension tracks other sessions' running runs of the primary worktree (a task-validation and a
  delivery were running), and pi-subagents' background-work provider keeps print mode waiting for
  them. Pre-existing behaviour, not caused by this task; interactive sessions are unaffected and
  task sessions keep the run view off. Reported to the developer as a follow-up.
- Full suite: 1 failure, `tests/concorde/views/test_repository_checks.py::...test_real_registry_listing_roots_are_copied`,
  because the docsite repository check copies an explicit file list and the new realization
  entry `.pi/settings.json` was not in it. Added `.pi/settings.json` to `FILES` in
  `docsite/tests/repository/run-checks.py`, a file of the Views Module, which is outside this
  task's Modules; decided without the developer because the check itself demands every
  realization entry be copied and the change is one list entry.
- First `task merge` refused with `merge_conflict` in three Spec files (Tasks module.md and
  contracts.md, Execution module.md): main had meanwhile gained `tasks-verified-delivery`
  (delivery_unverified, evidence-bundle verification) and a note that a result on disk does not
  mean the workspace lock is free. Merged main into the task branch and kept both sides: main's
  new wording plus this task's lock order and `--wait`. Also rewrote Tasks' "taking the same lock
  without waiting" sentence in its uses-Execution passage. Build, spec-validation and the full
  suite (686 passed) pass; validating and delivering again.

## Closed: merged, 2026-09-28T17:55:56Z

# Decision log: tasks-atomicity

Goal: Developer-approved panel-review decisions for Tasks: (tasks F17) store.begin_round checks task_closed inside its transaction's change function (rechecked on retry), the Begin round contract row says so, Finish round stays allowed on a closed task; (tasks F14) close and escalate are not atomic: list their partial outcomes as exceptions in req.tasks.refusal-inert, and make the messages say what was done and that re-running the same close finishes it, and for escalate that the log append failed after the record was written. Spec and tests.

## Decisions taken without the developer (task session, 2026-09-29)

1. **F17: where the closed check lives.** `store.begin_round`'s change function refuses
   `task_closed` for a `closed` or `failed` task before looking at the session. `store.update`
   already calls the change function again on every retry, so the check is re-made on the record
   actually written; no new retry logic was needed. `finish_round` gets no state check (its
   docstring and the contract row now say it records a round's outcome whatever the task's state).
   Options were a separate pre-check (rejected: that is the race the finding names) or the check in
   the change function (taken). `req.tasks.closed-no-session` and the `task_closed` error row now
   also name beginning a round; new scenario `scenario.tasks.round-closed`.
2. **F14: how "re-running the same close finishes it" holds for every partial outcome.** A rerun
   already finishes a close whose worktree step or record update failed (it skips a worktree that
   is gone). For a close whose record was written and whose decision-log append failed, a rerun
   would have refused `invalid_transition`, contradicting the required message. Options: (a) append
   the log before writing the record (rejected: a record failure after the append makes the rerun
   append the closing twice); (b) tell the caller to append by hand (rejected: the goal asks that
   re-running the same close finishes it); (c) let the same close of a task already stored with that
   outcome, whose decision log has no line `## Closed: <outcome>, <closed.at>`, append the closing
   the record holds and return the record unchanged (taken). `invalid_transition` stays for every
   other close of an ended task, including a second rerun once the closing is logged.
3. **New error codes** (reason `environment`): `decision_log_failed` for the log append failing
   after the record was written (close and escalate) or a rerun that cannot read the log, and
   `record_unwritable`, raised by `store.update` when the file system refuses the record write
   (before, an OSError there escaped as an unexpected exception whose explanation said "nothing
   after it ran", which is wrong once `close` has removed the worktree). Both are in the contract's
   error table and reason list and in the CLI's HANDLING/OPTIONS.
4. **Close run by a merge.** `close_locked` takes an `again` text naming what finishes it;
   `task merge` passes `concorde task merge <task> --resume` because `close` is refused
   (`merge_incomplete`) while the task is `merging`. A `decision_log_failed` from a merge's close
   is reported as "merged, every check passed and closed as merged, but …", pointing to
   `close --merged` rather than `--resume` (the task is no longer `merging`).
5. **`worktree_removed` on a rerun** stays the existing meaning (this close's `git worktree
   remove` removed it), so a rerun after an earlier attempt removed the worktree records `false`;
   the contract now says so rather than changing the field's meaning.
6. **Escalate's log failure** does not try to re-append on a rerun (a rerun of `escalate` creates a
   new escalation). The refusal names the escalation number, the heading it would have had and
   carries the rendered chain so it can be appended by hand; new scenario
   `scenario.tasks.escalate-log-failed`, and `scenario.tasks.close-rerun` for the close cases.

## Results (task session)

- Full suite on the final input: 666 passed, 4 skipped. `build --check` and `spec-validation`
  clean. `task-validation` run r-20260928T172351-task_validation-d9d08396: ready, no blocking
  findings or warnings. Delivered by r-20260928T172440-delivery-8a90b0c5, delivery commit
  8b5819f7c2b445104fd119126f9b8467d5cbc91f.
- Non-`ok` result: `uvx ruff format` failed first with "Read-only file system" on uv's tool
  directory under the home directory (sandbox); rerun with `UV_TOOL_DIR` in the session's
  temporary directory, it formatted and a second pass changed nothing. `ruff check` reports
  ISC004/PLW1510 findings that already exist throughout the unchanged code; the project's
  verification rules require formatting only, so they were left.

## Closed: merged, 2026-09-28T17:26:12Z

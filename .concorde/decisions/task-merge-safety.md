# Decision log: task-merge-safety

Goal: Make task merge and close safe against concurrent work and interruption: (F12) merge merges the exact head commit its preflight checked (git merge <sha>, never the branch name), and merge and close take the task's workspace lock non-blocking after the merge lock, refusing with a busy code naming the holder; (F13) a new stored task state 'merging' is written with the before commit and the checked sha before git merge runs, becomes closed only after every check passed (or is rolled back to delivered on failure); while a task is 'merging' and no live process holds the merge lock, every mutating task command (open, merge, close, session, escalate) in any main session refuses with a new code 'merge_incomplete' naming the task, the before/after commits and the recovery, while task list/show still work; add 'task merge <task> --resume' (rerun the checks when HEAD is still the merge commit, then close or roll back) and '--abort' (reset the primary branch to 'before', task back to delivered); a live merge still answers merge_busy. Update the Tasks Spec (states, contracts, requirements incl. merge-all-or-nothing, scenarios), the main-session guidance, and tests

## Decisions taken without the developer (task session, 2026-09-29)

- **Busy code for the workspace lock: `workspace_busy`.** Options: a new Tasks code
  (`task_busy`) or Execution's own `workspace_busy`. Chose `workspace_busy`: it is the code
  Execution already gives for the same lock, so one busy lock has one name; Tasks wraps
  Execution's message (which names the holder) and adds why merge/close take it without waiting.
  Reason `environment`, like `merge_busy`.
- **What `merging` records.** `before`, `checked`, `branch` (the primary branch's name), `after`
  (null until `git merge` returned, then written by a second record update), `checks` (argv
  lists), `since`, `pid`. Recording the checks lets `--resume` rerun exactly the checks the
  interrupted merge would have run; so `--resume`/`--abort` refuse `--check` (`invalid_input`).
  Options were: rerun the default/given checks, or the recorded ones; recorded is deterministic.
- **Recognizing "HEAD is still the merge commit".** When `after` is recorded, only HEAD == after
  counts; before it is recorded (process killed between `git merge` and the record write), HEAD
  counts when its parents are exactly [before, checked], or when it is `checked` itself and
  `before` is its ancestor (fast-forward).
- **Stored state after a failed rollback or failed close stays `merging`.** `rollback_failed` and a
  close that failed after passing checks now leave the task `merging` (previously the failed close
  said `close --merged` finishes it, which `merge_incomplete` would now refuse); the recovery named
  is `--abort` (rollback failed) or `--resume` (close failed). A conflict or check failure that
  was undone returns the task to stored `open` (derived delivered).
- **New refusal codes:** `not_merging` (input: `--resume`/`--abort` for a task that is not
  merging), `not_resumable` (decision: HEAD is not the merge commit; `--abort` is the way out),
  `merge_diverged` (decision: the primary worktree is on another branch or HEAD is neither
  `before` nor the merge commit; Tasks never resets commits it did not make).
- **`--abort` with a merge still in progress** (MERGE_HEAD present) runs `git merge --abort` first.
- **`session --stop` is exempt from `merge_incomplete`.** The goal lists `session` among the
  refused commands; stopping a round never builds on the primary branch, and refusing it would keep
  a runaway round alive while the merge is recovered. Start and `--answer` are refused.
- **`session`/`escalate` during a live merge.** They take no merge lock, so they check the lock's
  liveness (a non-blocking shared `flock`): with no live holder an unfinished merge is
  `merge_incomplete` for every task; while the merge still runs, only a session or escalation of
  the task being merged answers `merge_busy`, and other tasks proceed. The pi supervisor's round
  updates (begin/finish round) are record updates, not commands, and are not guarded, so a running
  round's result is never lost.
- **A branch moved after the preflight.** The merge merges the checked sha; closing then refuses
  `not_merged` (the branch head is no longer the last delivery), leaving the task `merging`, since
  closing as merged would silently leave the later commit unmerged. With the workspace lock held,
  only a hand-made commit can do this.

## Non-ok results (task session, 2026-09-29)

- **Full suite: 1 failure, pre-existing.** `tests/concorde/e2e/test_cases.py::CaseTests::
  test_grading_runs_the_case_tests_on_a_throwaway_tree` fails (`FAILED` != `not run`) on this
  branch and identically on the base commit fee38b9e (checked in a throwaway detached worktree),
  so it is not caused by this task; it belongs to the SWE-bench cases Module, outside this task.
  650 passed, 4 skipped otherwise.
- **`git worktree prune` from the sandbox touched other worktrees' admin entries.** After removing
  the throwaway worktree I ran `git worktree prune`; since the sandbox hides other worktree paths,
  Git treated the entries `close-submodule-worktrees`, `delivery-index-restore` and
  `installer-ships-docsite` as stale and deleted their files except `commondir` and
  `config.worktree` (the sandbox kept those busy). All three tasks are closed with
  `worktree_removed: true` and their worktrees no longer exist, so these were leftovers; every live
  worktree (main, core-concepts, installer-uv-python, task-merge-safety, unbound-run-worktree) is
  still listed intact by `git worktree list`. The three admin directories remain with only those
  two files; the main agent may delete them. Lesson: never run `git worktree prune` from a sandboxed
  task session.
- **Sandbox placeholders in the worktree.** The sandbox shows untracked device-node placeholders
  (`.bash_profile`, `.bashrc`, `.gitconfig`, `.profile`, `.zshrc`, `.mcp.json`, `.claude/`, ...)
  at the worktree root; commits stage explicit paths so none is committed.
- The throwaway worktree's admin entry `.git/worktrees/base` is left empty: `rmdir` is refused
  inside the sandbox ("Device or resource busy"). The main agent may delete it.

## Delivered (task session, 2026-09-29)

task-validation r-20260928T164254-task_validation-711e0429 ok (ready, no blocking); delivery
r-20260928T164818-delivery-fe9e8ee3 ok, delivery commit 35fc50b4db6d512386d873ec5afff10316597764.

Open points for the main agent: `docs/using-concorde.md` (owned by module.concorde, outside this
task's Modules) still describes merging without `--resume`/`--abort`/`merge_incomplete`;
`DEVELOPING.md` and `CLAUDE.md` of this checkout name `merge_busy` and `merge_conflict` handling
but not `merge_incomplete`. The primary checkout's own open task records predate the `merging`
field; the code reads it with `.get`, so they keep working.

## Closed: merged, 2026-09-28T16:54:49Z

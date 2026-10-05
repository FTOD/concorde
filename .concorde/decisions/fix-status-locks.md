# Decision log: fix-status-locks

Goal: Make task-state readers run git status without optional locks so a concurrent task close or merge cannot fail, and fix the detached-run test's check order


## Task brief (main agent, 2026-10-05)

The developer decided on 2026-10-05 to fix both Issues this task resolves. The main agent's
investigation, recorded in each Issue's latest report, found both causes and gave both the tier
`obvious-fix`. Read both Issues first with `concorde issues show <id>`.

### I-d0e67ee6eaae595f9ee627a0a0b1b1b6 (module.tasks, high)

Any reader that computes `derived_state` runs plain `git status` in the task worktree, through
`store._changes` at about `src/concorde/coordination/tasks/store.py:1655`. Such readers include
`task show`, `task list`, `task wait` and the MCP `register_wait`. Plain `git status` refreshes the
index, so it writes `index.lock` and renames it over the index. A concurrent close or merge running
`git worktree remove` can then fail with `worktree_failed`. That leaves the worktree half removed
while the record stays open.

- Run read-only status with `git --no-optional-locks status`, as `worker_harness/audit.py:31`,
  `execution/idle.py:55` and other places already do. Apply it in `store._changes` and in
  `deliver.py` (about line 282). Look for any other read-only git call in Coordination that can
  write the index, and fix it the same way.
- Add a deterministic test: touch a tracked file, call the reader, and assert that the index inode
  and mtime are unchanged and that no `index.lock` appeared. It must fail before the fix and pass
  after it.
- In `tests/concorde/tasks/test_wait.py`, make the delayed close record its exception, and assert
  that the close succeeded before asserting the wait's code. The rebind test there has the same
  pattern.
- You may also harden `_changes` for a worktree that vanished between `exists()` and the subprocess
  (treat it as no changes), if it is simple. You decide, and you record the decision.
- If a Spec statement needs a precise word, such as the read-only promise of
  `req.tasks.wait-bounded` covering the index, add it. Otherwise this changes no Spec meaning.

### I-7f491393d6e85610886f47c0426cf37f (module.execution, low)

In `tests/concorde/execution/test_runner.py`, at about line 1305, check
`announced["lobby"]/status.json` first and `announced["progress"]` second. A run moves from the
lobby into its node and never back, and `runner.py:1197` checks in that same order. Change the test
only.

### Verification

Run the affected tests repeatedly under load, for example in a loop with `-n 16`, then the full
pytest, `spec-validation` and `build --check`. Deliver as usual. The merge closes both Issues.

## Task session decisions (2026-10-05)

- Read-only status now runs as `git --no-optional-locks status` in `store._changes` and
  `deliver._special`, following `issues/store.py`'s idiom (the global option, not the
  `GIT_OPTIONAL_LOCKS` environment). A search of every Git call in Coordination found no other
  read-only call that writes the index: the remaining calls are `rev-parse`, `rev-list`,
  `cat-file`, `check-ignore`, `merge-base`, `symbolic-ref` and `log`, which never write it, and
  the writers (`add`, `commit`, `merge`, `reset`, `checkout`, `worktree`, `branch`) run under the
  locks of the command that changes the worktree. The `git diff --diff-filter=U` after a failed
  merge runs in the primary worktree under the merge lock, so it races with no close.
- Hardened `_changes`: a worktree removed between its `exists()` check and the `git status`
  subprocess (the subprocess's missing cwd surfaces as `git_failed`) now counts as no changes,
  but only when the worktree is really gone; otherwise the error stands. Reason: simple, and a
  reader racing a close should see the closed task, not a `git_failed` refusal.
- Spec: added to `req.tasks.derived-state` that deriving the state changes no file, the Git index
  included, and a new `scenario.tasks.state-read-only`, verified by the new deterministic test
  `test_deriving_the_state_leaves_the_index_as_it_is` (index inode and mtime unchanged, no
  `index.lock`). The test failed before the fix (inode changed) and passes after it. Reason: the
  brief allowed a precise word, and the derived-state requirement had no read-only promise the
  new test could verify.
- `test_wait.py`: `later` now records what the delayed action raised; both the unreachable test
  and the rebind test join the close and assert it raised nothing before asserting the wait's
  code. The rebind test's `contextlib.suppress(store.TaskError)` was removed, since the close
  succeeds in this fixture and a suppressed failure hid exactly this defect.
- `test_runner.py`: the detached-run test checks the lobby's progress file before the node's.
- Verification: affected tests 30/30 passes under -n 16; full pytest 1255 passed, 5 skipped; spec-validation success; build --check no differences.

## Report 1 to the main agent (concorde-f8), 2026-10-05T04:47:20Z

fix-status-locks delivered: delivery commit 1e964799bcc03327c01349e2b81f4776bbdc998b on concorde/fix-status-locks (step 3fb78364).

Done:
- store._changes and deliver._special now run `git --no-optional-locks status`. I checked every other Git call in Coordination, and none is a read-only call that writes the index.
- _changes hardened: a worktree removed during the read counts as no changes, but only if it is really gone.
- Spec: req.tasks.derived-state now says that deriving the state changes no file, the Git index included. The new scenario.tasks.state-read-only is verified by test_deriving_the_state_leaves_the_index_as_it_is, which checks that the index inode and mtime are unchanged and that no index.lock exists. Without the fix the test fails because the inode changes. With it, the test passes.
- test_wait.py: the delayed close records what it raised. Both the unreachable test and the rebind test assert that the close raised nothing before they check the wait's code. The rebind test's suppress(TaskError) is removed.
- test_runner.py: the detached-run test now checks the lobby before the node.

Verification:
- Affected tests: 30 of 30 loops passed under -n 16.
- Full pytest: 1255 passed, 5 skipped.
- spec-validation: success. build --check: no differences.
- task-validation: ready.

Issues resolved by this task (closed by the merge): I-d0e67ee6eaae595f9ee627a0a0b1b1b6, I-7f491393d6e85610886f47c0426cf37f.

Decisions are in the decision log. Nothing is open. Please merge.

## Closed: merged, 2026-10-05T04:47:52Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 1e964799bcc03327c01349e2b81f4776bbdc998b into main and closed it as merged. Nobody answers a report after that.

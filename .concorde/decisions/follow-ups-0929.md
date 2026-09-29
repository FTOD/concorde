# Decision log: follow-ups-0929

Goal: Small follow-ups: (1) the main-session guidance (Claude Code and pi) tells the main agent to show the developer the names of the tasks it dispatched (opened tasks, started task sessions) with a one-line goal each, stated as a Main session requirement; (2) swe-bench grading disables colour in the graded pytest run so FORCE_COLOR in the caller's environment no longer makes every test read 'not run'; (3) docs/using-concorde.md, DEVELOPING.md and CLAUDE.md describe merge_incomplete, task merge --resume/--abort, merge_diverged and workspace_busy; (4) Concorde's own config links docsite/node_modules into unbound checkouts (workers.runtime)

## 2026-09-29 — main agent

- (1) Developer's request: the main-session guidance tells the main agent to name every dispatched
  task with a one-line goal and report by those names; new requirement
  req.main-session.dispatched-named. Also added to this checkout's CLAUDE.md.
- (2) Cause verified: Claude Code sessions set FORCE_COLOR=3, so the graded pytest wrapped its
  summary statuses in escapes and every test read `not run`. Grading now passes `--color=no`
  (pytest's own switch, which wins over FORCE_COLOR) instead of editing the environment; the cases
  Spec says so. The long-standing failure of test_grading_runs_the_case_tests_on_a_throwaway_tree
  is fixed (full suite 662 passed with FORCE_COLOR=3).
- (3) docs/using-concorde.md, DEVELOPING.md and CLAUDE.md describe workspace_busy,
  merge_incomplete with --resume/--abort, and merge_diverged, as task-merge-safety introduced them.
- (4) Decision (mine): `.concorde/config.json` sets workers.runtime to `.venv`, `node_modules` and
  `docsite/node_modules`, so an unbound checkout links the docsite's dependencies too; this also
  makes `docsite/node_modules` readable to workers as a runtime path, which docsite checks need.
- Verification: spec-validation 0/0, build --check clean, prettier clean, pytest 662 passed.

## Closed: merged, 2026-09-28T17:02:49Z

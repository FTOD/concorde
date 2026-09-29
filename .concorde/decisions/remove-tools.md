# Decision log: remove-tools

Goal: Remove the Tools group and the Tool concept; Check execution becomes an ordinary service Module directly under Execution, and level 5 of the levels of work is the workers alone

## Main-agent decisions (working the task directly)

The developer agreed that the Tools group adds nothing and that Check execution cannot itself be a command, since runs call it in-process while they hold the workspace lock. Decisions taken without asking:

- Check execution moves to `specs/concorde/execution/checks/` as a direct child of Execution; Module id `module.checks` and all its anchors are kept, so no link target changed except paths.
- The vocabulary's Tool concept (`concept.concorde.tool`) is removed rather than redefined. Prose that said "Tool" now says "service" (a program a run's step calls in-process, like Spec core) or names Check execution directly. "Service" is deliberately not registered as a new term, to avoid rebuilding the removed category under another name.
- Level 5 of the levels of work is the workers alone, in the root Spec, README and user docs; Check execution is described as no level.
- No `concorde check` execution command is added: `task-validation` already runs and records checks, and no caller needs a separate run.
- Code keeps "Tool" in `src/concorde/distribution/cli.py`, `spec/model.py` and `views/docsite_scaffold.py`: there it means the Spec tooling command envelope (`ToolResult`, the `tool` field), not the removed Concorde Tool concept.

## Closed: merged, 2026-09-27T17:32:04Z

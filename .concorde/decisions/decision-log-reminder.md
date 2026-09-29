# Decision log: decision-log-reminder

Goal: Make the decision log hard to miss: task open prints its path, task merge warns when it has no entry beyond the heading and goal, CLAUDE.md imports DEVELOPING.md, and the host step lists include recording decisions

## Main-agent decisions (working the task directly)

The developer asked for both a `@DEVELOPING.md` import and a deterministic reminder. Decisions taken without asking:

- pi does not expand `@path` in context files: the installed pi (`dist/core/resource-loader.js`, `system-prompt.js`) inserts `AGENTS.md` verbatim inside `<project_instructions>`, and `@path` works only in pi's first CLI prompt. So only `CLAUDE.md` imports `DEVELOPING.md`; `AGENTS.md` keeps the instruction to read it and now says why.
- The import alone would not have prevented the missed log (the file had been read in full); the effective fixes are an explicit decision-log step in the Claude Code and pi step lists and in DEVELOPING.md, and the merge warning.
- The reminder lives in `task merge`, not `delivery`: Delivery is Execution and knows no task or decision log. It is a warning in a new `warnings` output field, never a refusal, since Tasks cannot tell whether a task needed decisions. It fires when the log is missing or equals exactly what `open` wrote, read before the close appends its entry.
- `task open` now prints `{"record", "decision_log"}` instead of the bare record, matching `show` and `escalate`, which already name the log. Callers in `scripts/e2e/` and the e2e test fake were updated; no compatibility shim, per the rapid-iteration rule.
- The dogfooding test that required "Read [DEVELOPING.md] in full" in both files now requires that sentence in `AGENTS.md` and the `@DEVELOPING.md` import line in `CLAUDE.md`.

## Closed: merged, 2026-09-27T17:38:21Z

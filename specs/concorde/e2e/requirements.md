# End-to-end testing requirements

The Module-wide obligations of [End-to-end testing](module.md). The
[scenarios](scenarios.md) show them in concrete situations.

## Test projects

### req.e2e.swe-bench-projects — Test projects come from SWE-bench

The tool SHALL prepare only repositories SWE-bench's harness names, unless the developer passes `--any`.

### req.e2e.fresh-project — A test project is prepared into a new directory

`prepare` SHALL refuse a project directory that already exists.

### req.e2e.user-setup — A test project is set up as a user's

The tool SHALL set up a [test project](../glossary.json#concept.test-project) only through this checkout's installer and `concorde` command, the same steps a user takes, never writing the project's Specs or configuration itself.

### req.e2e.never-installed — End-to-end testing reaches no user

No file of this [Module](../glossary.json#concept.module) SHALL be installed into a project or
rendered into the [main-session guidance](../glossary.json#concept.main-session-guidance).

## Running

### req.e2e.headless-waits — A headless run lasts as long as its workflow

A [headless run](../glossary.json#concept.headless-run) SHALL start its `claude -p` session with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`.

### req.e2e.headless-granted — A headless run needs no trust

A headless run SHALL grant the workflow and its `concorde workflow step` and `report` commands with `--allowedTools`.

### req.e2e.driver-real-steps — A driver run runs the real step commands

A [driver run](../glossary.json#concept.driver-run) SHALL execute every step and the report of the
workflow's script with the real `concorde workflow step` and `concorde workflow report` commands
of the task's worktree.

### req.e2e.trust-explicit — Trust changes only on request

The tool SHALL change Claude Code's configuration only through `trust`.

### req.e2e.trust-backup — Trust backs the configuration up

`trust` SHALL back Claude Code's configuration file up before its first change of it.

### req.e2e.trust-preserves — Trust keeps every other setting

`trust` SHALL leave every setting of Claude Code's configuration other than the trust markings it
adds as it was.

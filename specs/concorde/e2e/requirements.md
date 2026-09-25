# End-to-end testing requirements

The Module-wide obligations of [End-to-end testing](module.md). The
[scenarios](scenarios.md) show them in concrete situations.

## Test projects

### req.e2e.swe-bench-projects — Test projects come from SWE-bench

The tool SHALL prepare only repositories SWE-bench's harness names, unless the developer passes `--any`.

### req.e2e.user-setup — A test project is set up as a user's

The tool SHALL set up a test project only through this checkout's installer and `concorde` command, the same steps a user takes, never writing the project's Specs or configuration itself.

### req.e2e.never-installed — End-to-end testing reaches no user

No file of this Module SHALL be installed into a project or rendered into the main-session guidance.

### req.e2e.case-graded-apart — A case's tests stay outside the project

The tool SHALL grade a case in a throwaway worktree of the project, applying the case's test patch only there and removing the worktree afterwards.

## Running

### req.e2e.headless-waits — A headless run lasts as long as its workflow

A headless run SHALL start its `claude -p` session with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`.

### req.e2e.headless-granted — A headless run needs no trust

A headless run SHALL grant the workflow and its `concorde workflow step` and `report` commands with `--allowedTools`.

### req.e2e.trust-explicit — Trust changes only on request

The tool SHALL change Claude Code's configuration only through `trust`, backing the file up before its first change and leaving every other setting as it was.

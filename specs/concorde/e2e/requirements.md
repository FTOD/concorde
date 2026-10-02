# End-to-end testing requirements

The Module-wide obligations of [End-to-end testing](module.md). The
[scenarios](scenarios.md) show them in concrete situations.

## Test projects

### req.e2e.swe-bench-projects — Test projects come from SWE-bench

The tool SHALL prepare only repositories SWE-bench's harness names, unless the developer passes `--any`.

### req.e2e.root-outside-checkout — No test project lies inside the checkout

The tool SHALL refuse an end-to-end root, the default or `CONCORDE_E2E_ROOT`, whose real path is this checkout or lies inside it.

### req.e2e.fresh-project — A test project is prepared into a new directory

`prepare` SHALL refuse a project directory that already exists.

### req.e2e.user-setup — A test project is set up as a user's

The tool SHALL set up a [test project](../glossary.json#concept.test-project) only through this checkout's installer and `concorde` command, the same steps a user takes, never writing the project's Specs or configuration itself except its [worker configuration](../glossary.json#concept.worker-configuration), which a user writes by hand since no command writes it.

### req.e2e.never-installed — End-to-end testing reaches no user

No file of this [Module](../glossary.json#concept.module) SHALL be installed into a project or
rendered into the [main-session guidance](../glossary.json#concept.main-session-guidance).

## Running

### req.e2e.headless-waits — A headless run lasts as long as its workflow

A headless run SHALL start its `claude -p` session with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`.

### req.e2e.headless-granted — A headless run needs no trust

A headless run SHALL grant the workflow, the [project MCP server](../glossary.json#concept.project-mcp-server)'s `workflow_step` and the `concorde workflow report` command with `--allowedTools`, and give the session the project MCP server with `--mcp-config`.

### req.e2e.driver-real-steps — A driver run runs the real step commands

A driver run SHALL execute every step and the report of the
workflow's script with the real `concorde workflow step` and `concorde workflow report` commands
of the task's worktree.

### req.e2e.own-result — A run prints only its own workflow result

`run` SHALL print only a [workflow result](../glossary.json#concept.workflow-result) saved in the
[workflow record](../glossary.json#concept.workflow-record) after the run started.

### req.e2e.trust-explicit — Trust changes only on request

The tool SHALL change Claude Code's configuration only through `trust`.

### req.e2e.trust-backup — Trust backs the configuration up

`trust` SHALL back Claude Code's configuration file up before its first change of it.

### req.e2e.trust-preserves — Trust keeps every other setting

`trust` SHALL leave every setting of Claude Code's configuration other than the trust markings it
adds as it was.

## The owners case

### req.e2e.owners-case — The owners case fails whenever a run wakes a session it does not own

The owners case SHALL end `failed`, naming each problem, when the owner of a run it played was not
woken when the run ended, when any other live session began a turn or received a notification
while the run ended, or when a session that does not own the run could not see it ended.

It prompts no session in the time it judges, so every turn and notification there is a wake.

### req.e2e.owners-deadline — An owner's missing wake is a verdict, not an error

The owners case SHALL judge a phase at the latest `--wake` and `--grace` seconds after its run
wrote its result, whether or not the run's owner has been woken by then.

An owner not woken by then is therefore a problem of the `failed` verdict that
[req.e2e.owners-case](#req.e2e.owners-case) requires, never an error of the case.

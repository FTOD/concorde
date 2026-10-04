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

The tool SHALL set up a [test project](../glossary.json#concept.test-project) only through Git, which fetches the revision, checks it out on a branch and commits, and this checkout's installer and `concorde` command, the same steps a user takes, never writing the project's Concorde [Specs](../glossary.json#concept.spec) or configuration itself, except its [worker configuration](../glossary.json#concept.worker-configuration), which a user writes by hand since no command writes it.

The interpreter `--python` names therefore reaches the project configuration only as an argument of `concorde init`.

### req.e2e.never-installed — End-to-end testing reaches no user

No file of this [Module](../glossary.json#concept.module) SHALL be installed into a project or
rendered into the [main-session guidance](../glossary.json#concept.main-session-guidance).

## Running

### req.e2e.headless-waits — A headless run lasts as long as its workflow

A headless run SHALL start its `claude -p` session with `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` set to `0`.

### req.e2e.headless-granted — A headless run's tools need no trust

A headless run SHALL grant the workflow, the [project MCP server](../glossary.json#concept.project-mcp-server)'s `workflow_step` and the `concorde workflow report` command with `--allowedTools`.

### req.e2e.headless-mcp — A headless run's MCP server needs no approval

A headless run SHALL give its session the [project MCP server](../glossary.json#concept.project-mcp-server) with `--mcp-config`, started as the installer registers it.

### req.e2e.driver-real-steps — A driver run runs the real step commands

A driver run SHALL execute every step and the report of the
workflow's script with the real `concorde workflow step` and `concorde workflow report` commands
of the task's worktree.

### req.e2e.own-result — A run prints only its own workflow result

`run` SHALL print only a [workflow result](../glossary.json#concept.workflow-result) saved in the
[workflow record](../glossary.json#concept.workflow-record) after the run started.

A saved result names no run, so this makes the printed result the run's own only under the
prerequisite that a test project is driven by one `run` at a time and that nobody else reports a
workflow in it while the run runs ([Running a workflow](module.md#running-a-workflow)).

### req.e2e.trust-explicit — Trust changes only on request

The tool SHALL change Claude Code's configuration only through `trust`.

### req.e2e.trust-backup — Trust backs the configuration up

`trust` SHALL back Claude Code's configuration file up before its first change of it.

### req.e2e.trust-preserves — Trust keeps every other setting

`trust` SHALL leave every setting of Claude Code's configuration other than the trust markings it
adds as it was.

## The owners case

### req.e2e.owners-case — The owners case fails unless only a run's owner is woken and every other session sees it

The owners case SHALL end `failed`, naming each problem, when, in the interval it judges a phase
over, the owner of the run it played began no turn and received no notification, or any other live
session began a turn or received a notification, or when afterwards a session that does not own the
run did not find it with the status of its result.

The interval runs from the end of the owner's launching turn, or from the start of the phase for a
run nobody owns, to the end of the observation window that
[req.e2e.owners-deadline](#req.e2e.owners-deadline) bounds. The case prompts no session in it, so
every turn and notification there is a wake.

### req.e2e.owners-deadline — An owner's missing wake is a verdict, not an error

The owners case SHALL judge a phase at the latest `--wake` and `--grace` seconds after its run
wrote its result, whether or not the run's owner has been woken by then.

An owner not woken by then is therefore a problem of the `failed` verdict that
[req.e2e.owners-case](#req.e2e.owners-case) requires, never an error of the case.

### req.e2e.owners-queue — The owners case's run outwaits the case's hold

The owners case SHALL launch a phase's run with a `--wait` longer than its limit, the longest it
holds the task's [workspace lock](../glossary.json#concept.workspace-lock) after the launch.

A run of the phase is therefore never refused for the lock the case itself holds.

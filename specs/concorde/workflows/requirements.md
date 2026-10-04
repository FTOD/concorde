# Workflows requirements

The Module-wide obligations of [Workflows](module.md). The shapes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Steps

### req.workflows.bound-only — A workflow runs only in a bound workspace

The workflow commands SHALL refuse to run a step or build a report in a worktree whose [workspace binding](../glossary.json#concept.workspace-binding) is absent or refused, starting and recording nothing.

### req.workflows.steps-are-runs — Every step is an ordinary run

A [workflow step](../glossary.json#concept.workflow-step) SHALL start its run only as `concorde run <operation> --detach` or `concorde <command> --detach` of the workspace's own `concorde`, in the workspace the step runs in.

The workflow leaves worker launches and service calls inside the run. What
[step agents](../glossary.json#concept.step-agent) may do is stated in
[req.workflows.step-agent-relays](#req.workflows.step-agent-relays) and
[req.workflows.step-agent-no-change](#req.workflows.step-agent-no-change).

### req.workflows.one-at-a-time — One run at a time

`concorde workflow step` SHALL start a step's run only after it has found the [workspace lock](../glossary.json#concept.workspace-lock) of its workspace free.

The runner writes a run's result before it releases the lock, so a step's run always finds the
results of the earlier steps written; a step's result on disk, though, does not mean the lock is
free yet, so the next step waits for the lock rather than for the result. When another process
takes the lock between that check and the start, the detached
runner cannot take the workspace lock and ends the run refused with `workspace_busy`; that run is an
ordinary finished step whose result carries the refusal.

### req.workflows.key-idempotent — A step key runs once

`concorde workflow step` SHALL start a run only for a [step key](../glossary.json#concept.step-key) with no current step in the workspace's [workflow record](../glossary.json#concept.workflow-record), with `--retry` for a key whose current step did not end `ok`, or for a key whose current step is still starting with no run in its node while no run of the workspace runs, reporting the current step's run otherwise.

A step is recorded as starting, with its node and no run, before its run is launched, and its run is
written into it once announced. A call that finds a step still starting, because the command that
launched its run ended first, adopts the run whose node lies in the step's node. While no run lies
there but a run of the workspace holds the
[workspace lock](../glossary.json#concept.workspace-lock) or waits in the lobby for it, the call
waits as it waits for that lock, since that run may be the step's. Otherwise the step's run never
started: the call ends the step's node lost and starts the run anew under the same key, superseding
the starting step. So repeating a call or relaunching the workflow never starts a run twice.

### req.workflows.restart-generation — A restart runs a step once more

A step given a restart label SHALL add it to the step key after `#`, so that it starts one new run for that label and finds that run on every later call with the same label while that step is current.

A step that a rerun of an earlier step superseded is never found again, even under the label it
was restarted with: asking for that label again starts a new run under the same key.

### req.workflows.step-lock — A step is looked up, started and recorded at once

`concorde workflow step` SHALL look a key up, start its run and record it while holding the workspace's workflow lock.

### req.workflows.workflow-lock-leaf — The workflow lock is a leaf

The step and report commands SHALL NOT wait for any other lock while holding the workflow lock.

A step that finds the workspace busy releases the workflow lock while it waits for the workspace
lock, and looks the key up again once it holds the workflow lock again, so that whoever retires the
workspace while holding its workspace lock always gets the workflow lock.

### req.workflows.workspace-retired — Nothing is written into a retired workspace

The step and report commands SHALL NOT create or write any file or folder in the workspace folder
before they hold the workflow lock and the binding read again matches the binding read when the
command started.

They take the workflow lock without ever taking a lock file that was removed or replaced while they
waited for it, and refuse with `workspace_retired`, starting and recording nothing, when it was or
when the binding is now absent, untrusted or different. Whoever retires the workspace removes the
binding, moves the workspace folder and removes the workflow lock file while holding that lock, so a
step never writes into a folder that has moved or recreates one that is gone.

### req.workflows.supersede — A rerun supersedes what came after it

Starting a new run for a base key that already has a current step SHALL supersede that step and every step recorded after it.

A superseded step is never found again, so nothing validated or delivered before a retried or
answered step is taken as current.

### req.workflows.refused-recorded — A step that could not start is recorded

A step whose command line the runner rejected, or whose detached runner did not start, SHALL be recorded without a run and with its error link.

A runner that did not start includes a launcher that could not be run at all, such as a
workspace's `concorde` that cannot be executed, and one that gave no answer within 90 seconds. A
step refused because its workspace was retired is the exception: it is recorded nowhere, and its
outcome alone carries the `workspace_retired` link.

### req.workflows.bounded-wait — A step call waits a bounded time

`concorde workflow step` SHALL return within its `--wait` seconds, plus at most 90 seconds for the announcement of a run it starts, exiting with status 3 when the run has not finished.

It waits for the workflow lock, as for the workspace lock, only within the bound: when another step
or report command still holds it as the bound ends, the call starts and records nothing and prints
the outcome `running` with no run. The launch of a run is the one wait not cut short at the bound,
for a launcher ended halfway could leave a run its step cannot name: Execution waits at most 60
seconds for a detached runner's announcement and ends a runner that stayed silent, and the step
command ends a launcher that gave no answer within 90 seconds, recording the step refused.

### req.workflows.answers-new-key — Answers make a new step

A step given answers SHALL add to its step key `@` and the first eight hexadecimal digits of the SHA-256 of the answers list in canonical JSON.

Canonical JSON has its keys sorted and no whitespace, so the same answers always name the same step.

### req.workflows.answers-passed — Answers reach the run

A step given answers SHALL pass them to its run with `--answers`, written next to the workflow record.

### req.workflows.answers-input — An answered step admits the run that asked

A step given answers SHALL admit with `--input` the latest `ok` run of the same base key, even when a rerun superseded that run, and admit no `--input` when the base key has no `ok` run.

The answers refer to that run's questions. Answers without an `ok` run to refer to are outside the
ordinary flow: a step that did not end `ok` has no pending decision point in the workflow result,
which gives its failure precedence, so the caller retries it rather than answering it.

### req.workflows.one-workflow-per-workspace — A workspace runs one workflow

`concorde workflow step` SHALL refuse a step naming a workflow other than the one already recorded for the workspace, starting and recording nothing.

### req.workflows.key-one-name — A step key names one Operation or command

`concorde workflow step` SHALL refuse a key already recorded for another [Operation](../glossary.json#concept.operation) or command, starting and recording nothing.

### req.workflows.no-operation-knowledge — Workflows reads only the step output convention

The step and report commands SHALL read of a run's output only its `workflow` object under the [step output convention](contracts.md#contract.workflows.step-output), passing its `data` to the script unchanged and uninterpreted.

So no Operation or command is known to Workflows by name: a run declares its decision points,
decisions, deviations, notes, whether it blocks the procedure, and the values its script reads, and a
run whose output carries no `workflow` object declares none of them.

### req.workflows.no-task — Workflows knows no task

No part of Workflows SHALL open, merge, close or escalate a task, or read or write a [task record](../glossary.json#concept.task-record) or a [decision log](../glossary.json#concept.decision-log).

## Modes

### req.workflows.interactive-stops — Interactive runs stop at decision points

A workflow in interactive mode SHALL end right after a step that did not end `ok` or whose output has [decision points](../glossary.json#concept.decision-point) its answers did not settle, before starting another step.

### req.workflows.answers-any-settler — An answer settles its point whoever gave it

A step's answers SHALL settle the [decision points](../glossary.json#concept.decision-point) they name, whoever gave them.

### req.workflows.settler-open — The result leaves who settles a point to the level above

The workflow result SHALL NOT assign a pending decision point to the developer or to anyone else, leaving that to whoever started the workflow.

In Concorde the [main agent](../glossary.json#concept.main-agent) settles the points its authority covers and puts the rest to the developer.

### req.workflows.no-ask-continues — No-ask runs never stop for a decision

A workflow in no-ask mode SHALL NOT end at a decision point.

### req.workflows.no-ask-describe-continues — A step the procedure goes past does not end a no-ask run

A workflow in no-ask mode SHALL NOT end at a step that did not end `ok` when its procedure goes past such a step.

Which steps a procedure goes past is the procedure's: the
[brownfield workflow](../glossary.json#concept.brownfield-workflow), for instance, goes past a
`code_to_spec` step of one [Module](../glossary.json#concept.module) that did not end `ok`, and lets task validation decide whether the
workspace can still be delivered. The step is still reported as a problem with its error chain.

## Results

### req.workflows.report-from-records — The result is built from what the runs recorded

`concorde workflow report` SHALL build the [workflow result](../glossary.json#concept.workflow-result) only from the workspace's workflow record and the saved [run results](../glossary.json#concept.run-result), never from values a step agent returned.

### req.workflows.complete-report — Nothing is left out of the report

The workflow result SHALL list every recorded step, every decision, decision point, deviation and note every finished current step declared under the step output convention, as its run declared it, and every current step that did not end `ok` as a problem with its [error chain](../glossary.json#concept.error-chain) unchanged.

### req.workflows.last-step — Only the last step makes a workflow ok

A workflow result SHALL have status `ok` only when the last step its workflow names ended `ok`.

The part that owns a procedure names its last step when it registers the workflow, and the build
renders the same name into the script as its `LAST_STEP` constant; Workflows knows no step by name otherwise.

### req.workflows.chain-on-top — The workflow adds its own link

A workflow result whose status is not `ok` SHALL carry an error link of level `workflow` stating why the workflow stopped and why it cannot handle that itself, with the errors of the steps that stopped it as unchanged causes.

### req.workflows.lost-step — A step that vanished is named

A workflow result SHALL report as lost, with a `workflow` link naming the step key and what was observed, every current step whose run has no result and no running runner or never started, and every key the script reported with `--lost` whose base key has no current step.

The record wins over the script: a reported key with a current step keeps what its run shows,
finished, still running or lost. A step still starting whose run never started is one recorded as
starting with no run in its node while no run of the workspace runs.

### req.workflows.lost-first — A first step lost before any record is reported

`concorde workflow report` given `--workflow` and a `--lost` key SHALL build and save a `failed` workflow result naming that workflow for a workspace that has no workflow record.

Step agents that returned nothing for the first step, such as three that mistyped its request,
leave no record: the script still knows its workflow and mode
and passes them, so the workspace gets a saved result with the lost key, and the workflow's node
created for it names that workflow, as a first step would have. Without `--workflow` such a report
is refused with `no_workflow`.

### req.workflows.report-saved — Reports are kept beside the record

`concorde workflow report` SHALL save every workflow result it prints, with its Markdown rendering, beside the workspace's workflow record.

A report is written into no decision log: what to copy from it into a task's log is the task
level's decision.

### req.workflows.report-listed — Saved reports are listed in the record

`concorde workflow report` SHALL list every report it saves in the workspace's workflow record.

## Scripts

### req.workflows.one-source — One procedure, rendered for Claude Code

Each workflow's procedure SHALL be written once, apart from the step adapter, and rendered by the build into a Claude Code workflow without change to its steps, run arguments, branches, admitted inputs or decision points.

The adapter decides only how a step is invoked and awaited and how the report is requested: through
relay subagents, which call the `workflow_step` tool that runs for them the step command a
developer could run, and run the report command, with the report assembled from the recorded runs.

### req.workflows.steps-through-server — Claude Code steps start from the project MCP server

The Claude Code step function SHALL start and await every step through the `workflow_step` tool the workflow part registers with the [project MCP server](../glossary.json#concept.project-mcp-server), never through a Bash command.

A step may outlast many relays, and a run anchored in a relaying agent's Bash call dies with it
([Steps in Claude Code](module.md#steps-in-claude-code)).

### req.workflows.own-tools — The workflow part registers its own tools

The workflow part SHALL register its tools `workflow_step` and `workflow_report` with the project MCP server through its [part registration](../glossary.json#concept.part-registration), as the only part that provides them.

Where the workflow part is not installed, neither tool exists.

### req.workflows.tool-step-command — `workflow_step` runs the worktree's own step command

`workflow_step` SHALL run `concorde workflow step --json <request> --wait <wait>` with the `concorde` of the session's worktree, from that worktree's root, as a process the project MCP server started, and answer with the step outcome it printed.

The command is a process of the server's, so the
[detached run](../glossary.json#concept.detached-run) it starts depends on neither the relaying
agent's turn nor one of the session's background commands, and lives until its run ends
([contracts](contracts.md#starting-a-workflow-step)).

### req.workflows.tool-bound-only — `workflow_step` works only in a bound workspace

`workflow_step` SHALL refuse with `unbound_worktree`, running nothing, when the session's worktree has no usable [workspace binding](../glossary.json#concept.workspace-binding).

### req.workflows.tool-threads — A waiting step holds up no other call

`workflow_step` SHALL be answered on a thread of its own, so that the project MCP server answers the session's other calls while a step call waits.

### req.workflows.script-repeats — The script, not a model, waits for a run

The Claude Code step function SHALL ask for a step again while its outcome says the run is still running, each call waiting at most 100 seconds, for at most 200 calls of that step, after which it resolves to the last outcome that said the run was running.

The cap, about five and a half hours of waiting, is a guard against a run that never ends, not a
limit of the run: the run goes on, the procedure ends as it does at any outcome still `running`, the
report says `running`, and starting the workflow again later finds the run under its key.

### req.workflows.retry-once — A retry asks for one new run

The Claude Code step function SHALL leave `retry` out of every call for a step after an outcome that names a run.

That run is the retried one, or the earlier one when it ended `ok` and nothing was retried; a rerun
that failed between two calls is then reported, not started once more. A call that started nothing,
because it waited for the workspace lock, names no run, so the next call still carries `retry`.

### req.workflows.relay-checked — An outcome for another step is no answer

The Claude Code step function SHALL treat a relayed outcome as no answer unless it names the step key asked for and a step outcome's state, and names a well-formed run identity or, only when refused or running, none.

The step key asked for is the base key with the restart label after `#` and, for an answered step,
`@` followed by eight hexadecimal digits, the digest the script checks by its shape alone. A step
without a run is either refused, or running while it waits to start; a finished or lost one always
has its run.

### req.workflows.relay-asked-again — A relay that is no answer is asked again

The Claude Code step function SHALL ask its step agent again after an outcome that is no answer until three outcomes in a row have been no answer or the step's 200 calls are spent.

### req.workflows.relay-exhausted — A step without an answer is reported lost

The Claude Code step function SHALL report a step lost after three outcomes in a row that are no answer, with the last relayed outcome attached to the script's result as `relayed`.

### req.workflows.step-agent-relays — Step agents only relay

A step agent SHALL call nothing but the `workflow_step` tool, or run nothing but `concorde workflow report`.

It does not perform the worker's job or bypass the run's grant, audit and result handling.

### req.workflows.step-agent-no-change — Step agents change no file

A step agent SHALL change no file.

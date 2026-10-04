# Workflows requirements

The Module-wide obligations of [Workflows](module.md). The shapes are in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete
situations.

## Steps

### req.workflows.bound-only — A workflow runs only in a bound workspace

When a worktree's [workspace binding](../glossary.json#concept.workspace-binding) is absent or refused, the workflow commands SHALL refuse to run a step or build a report, starting and recording nothing.

### req.workflows.steps-are-runs — Every step is an ordinary run

In the workspace it runs in, a [workflow step](../glossary.json#concept.workflow-step) SHALL start its run only as `concorde run <operation> --detach` or `concorde <command> --detach` of that workspace's own `concorde`.

The workflow leaves worker launches and service calls inside the run. What
[step agents](../glossary.json#concept.step-agent) may do is stated in
[req.workflows.step-agent-relays](#req.workflows.step-agent-relays) and
[req.workflows.step-agent-no-change](#req.workflows.step-agent-no-change).

### req.workflows.one-at-a-time — One run at a time

`concorde workflow step` SHALL start a step's run only after it has found the [workspace lock](../glossary.json#concept.workspace-lock) of its workspace free.

The runner writes a run's result before it releases the lock. So a step's run always finds the
results of the earlier steps written. A step's result on disk, though, does not mean the lock is
free yet. So the next step waits for the lock rather than for the result. When another process
takes the lock between that check and the start, the detached runner cannot take the workspace
lock. The detached runner then ends the run refused with `workspace_busy`. That run is an ordinary
finished step whose result carries the refusal.

### req.workflows.key-idempotent — A step key runs once

`concorde workflow step` SHALL start a run only in these cases, reporting the current step's run otherwise:

- The [step key](../glossary.json#concept.step-key) has no current step in the workspace's [workflow record](../glossary.json#concept.workflow-record).
- The call uses `--retry` for a key whose current step did not end `ok`.
- The key's current step is still starting with no run in its node while no run of the workspace runs.

Before its run is launched, a step is recorded as starting, with its node and no run. Once the
run is announced, the run is written into the step. A call may find a step still starting because
the command that launched its run ended first. In that case, the call adopts the run whose node
lies in the step's node. While no run lies there, the call waits as it waits for the lock in either
of these cases:

- A run of the workspace holds the [workspace lock](../glossary.json#concept.workspace-lock).
- A run of the workspace waits in the lobby for that lock.

The call waits because that run may be the step's. Otherwise the step's run never started. In
that case, the call ends the step's node lost. The call starts the run anew under the same key,
superseding the starting step. So repeating a call or relaunching the workflow never starts a run
twice.

### req.workflows.restart-generation — A restart runs a step once more

When given a restart label, a step SHALL add it to the step key after `#`, so that:

- The step starts one new run for that label.
- While that step is current, the step finds that run on every later call with the same label.

A step that a rerun of an earlier step superseded is never found again, even under the label it
was restarted with. Asking for that label again starts a new run under the same key.

### req.workflows.step-lock — A step is looked up, started and recorded at once

`concorde workflow step` SHALL hold the workspace's workflow lock throughout these actions:

- Look a key up.
- Start its run.
- Record it.

### req.workflows.workflow-lock-leaf — The workflow lock is a leaf

While holding the workflow lock, the step and report commands SHALL NOT wait for any other lock.

When a step finds the workspace busy, it releases the workflow lock while it waits for the
workspace lock. Once the step holds the workflow lock again, it looks the key up again. This
ensures that whoever retires the workspace while holding its workspace lock always gets the
workflow lock.

### req.workflows.workspace-retired — Nothing is written into a retired workspace

The step and report commands SHALL NOT create or write any file or folder in the workspace folder before both conditions hold:

- They hold the workflow lock.
- The binding read again matches the binding read when the command started.

The commands take the workflow lock without ever taking a lock file that was removed or replaced
while they waited for it. In any of these cases, the commands refuse with `workspace_retired`,
starting and recording nothing:

- The lock file was removed or replaced while they waited for it.
- The binding is now absent.
- The binding is now untrusted.
- The binding is now different.

While holding the workflow lock, whoever retires the workspace performs these actions:

- Removes the binding.
- Moves the workspace folder.
- Removes the workflow lock file.

So a step never writes into a folder that has moved or recreates one that is gone.

### req.workflows.supersede — A rerun supersedes what came after it

Starting a new run for a base key that already has a current step SHALL supersede that step and every step recorded after it.

A superseded step is never found again. So nothing validated or delivered before a retried or
answered step is taken as current.

### req.workflows.refused-recorded — A step that could not start is recorded

When the runner rejected a step's command line or its detached runner did not start, the step SHALL be recorded without a run and with its error link.

A runner that did not start includes a launcher that could not be run at all, such as a
workspace's `concorde` that cannot be executed. It also includes a launcher that gave no answer
within 90 seconds. A step refused because its workspace was retired is the exception. That step
is recorded nowhere. Its outcome alone carries the `workspace_retired` link.

### req.workflows.bounded-wait — A step call waits a bounded time

`concorde workflow step` SHALL return within the following bound, exiting with status 3 when the run has not finished:

- Its `--wait` seconds.
- Plus at most 90 seconds for the announcement of a run it starts.

It waits for the workflow lock, as for the workspace lock, only within the bound. When another
step or report command still holds the workflow lock as the bound ends, the call does the
following:

- Starts nothing.
- Records nothing.
- Prints the outcome `running` with no run.

The launch of a run is the one wait not cut short at the bound. This is because a launcher ended
halfway could leave a run its step cannot name. Execution waits at most 60 seconds for a detached
runner's announcement. Execution ends a runner that stayed silent. When a launcher gives no answer
within 90 seconds, the step command ends the launcher, recording the step refused.

### req.workflows.answers-new-key — Answers make a new step

When given answers, a step SHALL add to its step key `@` and the first eight hexadecimal digits of the SHA-256 of the answers list in canonical JSON.

Canonical JSON has its keys sorted and no whitespace, so the same answers always name the same step.

### req.workflows.answers-passed — Answers reach the run

When given answers, a step SHALL pass them to its run with `--answers`, written next to the workflow record.

### req.workflows.answers-input — An answered step admits the run that asked

When given answers, a step SHALL admit input as follows:

- When the base key has an `ok` run, admit with `--input` the latest `ok` run of the same base key, even when a rerun superseded that run.
- When the base key has no `ok` run, admit no `--input`.

The answers refer to that run's questions. Answers without an `ok` run to refer to are outside the
ordinary flow. This is because a step that did not end `ok` has no pending decision point in the
workflow result. The workflow result therefore gives the step's failure precedence, so the caller
retries the step rather than answering it.

### req.workflows.one-workflow-per-workspace — A workspace runs one workflow

When a step names a workflow other than the one already recorded for the workspace, `concorde workflow step` SHALL refuse it, starting and recording nothing.

### req.workflows.key-one-name — A step key names one Operation or command

When a key is already recorded for another [Operation](../glossary.json#concept.operation) or command, `concorde workflow step` SHALL refuse it, starting and recording nothing.

### req.workflows.no-operation-knowledge — Workflows reads only the step output convention

Under the [step output convention](contracts.md#contract.workflows.step-output), the step and report commands SHALL read only the `workflow` object from a run's output, passing its `data` to the script unchanged and uninterpreted.

So no Operation or command is known to Workflows by name. A run declares the following:

- Its decision points.
- Its decisions.
- Its deviations.
- Its notes.
- Whether it blocks the procedure.
- The values its script reads.

When a run's output carries no `workflow` object, the run declares none of them.

### req.workflows.no-task — Workflows knows no task

No part of Workflows SHALL do any of the following:

- Open a task.
- Merge a task.
- Close a task.
- Escalate a task.
- Read or write a [task record](../glossary.json#concept.task-record).
- Read or write a [decision log](../glossary.json#concept.decision-log).

## Modes

### req.workflows.interactive-stops — Interactive runs stop at decision points

A workflow in interactive mode SHALL end right after a step in either case below, before starting another step:

- The step did not end `ok`.
- The step's output has [decision points](../glossary.json#concept.decision-point) its answers did not settle.

### req.workflows.answers-any-settler — An answer settles its point whoever gave it

A step's answers SHALL settle the [decision points](../glossary.json#concept.decision-point) they name, whoever gave them.

### req.workflows.settler-open — The result leaves who settles a point to the level above

The workflow result SHALL NOT assign a pending decision point to the developer or to anyone else, leaving that to whoever started the workflow.

In Concorde the [main agent](../glossary.json#concept.main-agent) settles the points its authority covers.
The main agent puts the rest to the developer.

### req.workflows.no-ask-continues — No-ask runs never stop for a decision

A workflow in no-ask mode SHALL NOT end at a decision point.
### req.workflows.no-ask-describe-continues — A step the procedure goes past does not end a no-ask run

When its procedure goes past a step that did not end `ok`, a workflow in no-ask mode SHALL NOT end at that step.

The procedure decides which steps it goes past. For instance, the
[brownfield workflow](../glossary.json#concept.brownfield-workflow) goes past a
`code_to_spec` step of one [Module](../glossary.json#concept.module) that did not end `ok`.
The brownfield workflow lets task validation decide whether the workspace can still be delivered.
The step is still reported as a problem with its error chain.

## Results

### req.workflows.report-from-records — The result is built from what the runs recorded

`concorde workflow report` SHALL build the [workflow result](../glossary.json#concept.workflow-result) only from the following sources, never from values a step agent returned:

- The workspace's workflow record.
- The saved [run results](../glossary.json#concept.run-result).

### req.workflows.complete-report — Nothing is left out of the report

The workflow result SHALL list all of the following:

- Every recorded step.
- Every item of these kinds that a finished current step declared under the step output convention,
  as its run declared it:
  - decisions
  - decision points
  - deviations
  - notes
- Every current step that did not end `ok`, as a problem with its [error chain](../glossary.json#concept.error-chain) unchanged.

### req.workflows.last-step — Only the last step makes a workflow ok

A workflow result SHALL have status `ok` only when the last step its workflow names ended `ok`.

When the part that owns a procedure registers the workflow, it names the procedure's last step.
The build renders the same name into the script as its `LAST_STEP` constant.
Workflows knows no step by name otherwise.

### req.workflows.chain-on-top — The workflow adds its own link

When its status is not `ok`, a workflow result SHALL carry an error link with these details:

- Its level is `workflow`.
- It states why the workflow stopped and why the workflow cannot handle that itself.
- Its causes are the unchanged errors of the steps that stopped the workflow.

### req.workflows.lost-step — A step that vanished is named

A workflow result SHALL report the following as lost, with a `workflow` link naming the step key and what was observed:

- Every current step whose run has no result and no running runner or never started.
- Every key the script reported with `--lost` whose base key has no current step.

The record wins over the script. A reported key with a current step keeps what its run shows:

- Finished.
- Still running.
- Lost.

A step still starting whose run never started is one with all these characteristics:

- It is recorded as starting.
- It has no run in its node.
- No run of the workspace runs.

### req.workflows.lost-first — A first step lost before any record is reported

For a workspace with no workflow record, `concorde workflow report` SHALL do the following when given `--workflow` and a `--lost` key:

- Build a `failed` workflow result naming that workflow.
- Save that result.

Step agents that returned nothing for the first step, such as three that mistyped its request,
leave no record. The script still knows its workflow and mode and passes them.
Because the script passes them, the workspace gets a saved result with the lost key.
The workflow's node created for it names that workflow, as a first step would have.
Without `--workflow`, such a report is refused with `no_workflow`.

### req.workflows.report-saved — Reports are kept beside the record

`concorde workflow report` SHALL save every workflow result it prints, with its Markdown rendering, beside the workspace's workflow record.

A report is written into no decision log. The task level decides what to copy from the report
into a task's log.

### req.workflows.report-listed — Saved reports are listed in the record

`concorde workflow report` SHALL list every report it saves in the workspace's workflow record.

## Scripts

### req.workflows.one-source — One procedure, rendered for Claude Code

Each workflow's procedure SHALL be written once, apart from the step adapter, and rendered by the build into a Claude Code workflow without changes to:

- Its steps.
- Its run arguments.
- Its branches.
- Its admitted inputs.
- Its decision points.

The adapter decides only the following:

- How a step is invoked through relay subagents.
- How a step is awaited through relay subagents.
- How the report is requested through relay subagents.

The relay subagents call the `workflow_step` tool and run the report command.
The tool runs for them the step command a developer could run.
The report is assembled from the recorded runs.

### req.workflows.steps-through-server — Claude Code steps start from the project MCP server

The Claude Code step function SHALL start and await every step through the `workflow_step` tool the workflow part registers with the [project MCP server](../glossary.json#concept.project-mcp-server), never through a Bash command.

A step may outlast many relays. A run anchored in a relaying agent's Bash call dies with that agent
([Steps in Claude Code](module.md#steps-in-claude-code)).

### req.workflows.own-tools — The workflow part registers its own tools

The workflow part SHALL register its tools `workflow_step` and `workflow_report` with the project MCP server through its [part registration](../glossary.json#concept.part-registration), as the only part that provides them.

Where the workflow part is not installed, neither tool exists.

### req.workflows.tool-step-command — `workflow_step` runs the worktree's own step command

`workflow_step` SHALL run `concorde workflow step --json <request> --wait <wait>` and answer with the step outcome the command printed, with these execution details:

- The command uses the `concorde` of the session's worktree.
- The command runs from that worktree's root.
- The command runs as a process the project MCP server started.

The command is a process of the server's. Because of this, the
[detached run](../glossary.json#concept.detached-run) it starts depends on neither the relaying
agent's turn nor one of the session's background commands.
For the same reason, the detached run lives until its run ends
([contracts](contracts.md#starting-a-workflow-step)).

### req.workflows.tool-bound-only — `workflow_step` works only in a bound workspace

When the session's worktree has no usable [workspace binding](../glossary.json#concept.workspace-binding), `workflow_step` SHALL refuse with `unbound_worktree`, running nothing.

### req.workflows.tool-threads — A waiting step holds up no other call

`workflow_step` SHALL be answered on a thread of its own, so that the project MCP server answers the session's other calls while a step call waits.

### req.workflows.script-repeats — The script, not a model, waits for a run

While a step's outcome says the run is still running, the Claude Code step function SHALL ask for that step again with these limits:

- Each call waits at most 100 seconds.
- The function makes at most 200 calls of that step.
- After those calls, the function resolves to the last outcome that said the run was running.

The cap is about five and a half hours of waiting.
It is a guard against a run that never ends, not a limit of the run.
At the cap, the following happens:

- The run goes on.
- The procedure ends as it does at any outcome still `running`.
- The report says `running`.
- Starting the workflow again later finds the run under its key.

### req.workflows.retry-once — A retry asks for one new run

After an outcome that names a run, the Claude Code step function SHALL leave `retry` out of every call for that step.

That run is the retried one, or the earlier one when it ended `ok` and nothing was retried.
A rerun that failed between two calls is then reported, not started once more.
A call that started nothing because it waited for the workspace lock names no run.
Because that call names no run, the next call still carries `retry`.

### req.workflows.relay-checked — An outcome for another step is no answer

The Claude Code step function SHALL treat a relayed outcome as no answer unless all these conditions hold:

- The outcome names the step key asked for.
- The outcome names a step outcome's state.
- The outcome names a well-formed run identity or, only when refused or running, none.

The step key asked for is the base key with the restart label after `#`.
For an answered step, the key also has `@` followed by eight hexadecimal digits.
Those digits are the digest the script checks by its shape alone.
A step without a run is either refused, or running while it waits to start.
A finished or lost step always has its run.

### req.workflows.relay-asked-again — A relay that is no answer is asked again

After an outcome that is no answer, the Claude Code step function SHALL ask its step agent again until either limit is reached:

- Three outcomes in a row have been no answer.
- The step's 200 calls are spent.

### req.workflows.relay-exhausted — A step without an answer is reported lost

After three outcomes in a row that are no answer, the Claude Code step function SHALL report the step lost with the last relayed outcome attached to the script's result as `relayed`.

### req.workflows.step-agent-relays — Step agents only relay

A step agent SHALL call nothing but the `workflow_step` tool, or run nothing but `concorde workflow report`.

It does not perform the worker's job. It does not bypass any of the following:

- The run's grant.
- The run's audit.
- The run's result handling.

### req.workflows.step-agent-no-change — Step agents change no file

A step agent SHALL change no file.

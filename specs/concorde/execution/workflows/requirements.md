# Workflows requirements

The Module-wide obligations of [Workflows](module.md). The shapes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Steps

### req.workflows.bound-only — A workflow runs only in a bound workspace

The workflow commands SHALL refuse to run a step or build a report in a worktree whose [workspace binding](../../glossary.json#concept.workspace-binding) is absent or refused, starting and recording nothing.

### req.workflows.steps-are-runs — Every step is an ordinary run

A [workflow step](../../glossary.json#concept.workflow-step) SHALL start its run only as `concorde run <operation> --detach` or `concorde <command> --detach` of the workspace's own `concorde`, in the workspace the step runs in.

The workflow leaves worker launches and service calls inside the run. What client
[step agents](../../glossary.json#concept.step-agent) may do is stated in
[req.workflows.step-agent-relays](#req.workflows.step-agent-relays) and
[req.workflows.step-agent-no-change](#req.workflows.step-agent-no-change).

### req.workflows.one-at-a-time — One run at a time

`concorde workflow step` SHALL start a step's run only after it has found the [workspace lock](../../glossary.json#concept.workspace-lock) of its workspace free.

The runner writes a run's result before it releases the lock, so a step's run always finds the
results of the earlier steps written; a step's result on disk, though, does not mean the lock is
free yet, so the next step waits for the lock rather than for the result. When another process
takes the lock between that check and the start, the detached
runner cannot take the workspace lock and ends the run refused with `workspace_busy`; that run is an
ordinary finished step whose result carries the refusal.

### req.workflows.key-idempotent — A step key runs once

`concorde workflow step` SHALL start a run only for a [step key](../../glossary.json#concept.step-key) with no current step in the workspace's [workflow record](../../glossary.json#concept.workflow-record), or with `--retry` for a key whose current step did not end `ok`, reporting the current step's run otherwise.

### req.workflows.restart-generation — A restart runs a step once more

A step given a restart label SHALL add it to the step key after `#`, so that it starts one new run for that label and finds that run on every later call with the same label while that step is current.

A step that a rerun of an earlier step superseded is never found again, even under the label it
was restarted with: asking for that label again starts a new run under the same key.

### req.workflows.step-lock — A step is looked up, started and recorded at once

`concorde workflow step` SHALL look a key up, start its run and record it while holding the workspace's workflow lock.

### req.workflows.supersede — A rerun supersedes what came after it

Starting a new run for a base key that already has a current step SHALL supersede that step and every step recorded after it.

A superseded step is never found again, so nothing validated or delivered before a retried or
answered step is taken as current.

### req.workflows.refused-recorded — A step that could not start is recorded

A step whose command line the runner rejected, or whose detached runner did not start, SHALL be recorded without a run and with its error link.

### req.workflows.bounded-wait — A step call waits a bounded time

`concorde workflow step` without `--stdin` SHALL return within its `--wait` seconds, exiting with status 3 when the run has not finished.

### req.workflows.answers-new-key — Answers make a new step

A step given answers SHALL add to its step key `@` and the first eight hexadecimal digits of the SHA-256 of the answers list in canonical JSON.

Canonical JSON has its keys sorted and no whitespace, so the same answers always name the same step.

### req.workflows.answers-passed — Answers reach the run

A step given answers SHALL pass them to its run with `--answers`, written next to the workflow record.

### req.workflows.answers-input — An answered step admits the run that asked

A step given answers SHALL admit with `--input` the latest `ok` run of the same base key, even when a rerun superseded that run.

The answers refer to that run's questions.

### req.workflows.one-workflow-per-workspace — A workspace runs one workflow

`concorde workflow step` SHALL refuse a step naming a workflow other than the one already recorded for the workspace, starting and recording nothing.

### req.workflows.key-one-name — A step key names one Operation or command

`concorde workflow step` SHALL refuse a key already recorded for another [Operation](../../glossary.json#concept.operation) or command, starting and recording nothing.

### req.workflows.no-task — Workflows knows no task

No part of Workflows SHALL open, merge, close or escalate a task, or read or write a [task record](../../glossary.json#concept.task-record) or a [decision log](../../glossary.json#concept.decision-log).

## Modes

### req.workflows.interactive-stops — Interactive runs stop at decision points

A workflow in interactive mode SHALL end right after a step that did not end `ok` or whose output has [decision points](../../glossary.json#concept.decision-point) its answers did not settle, before starting another step.

### req.workflows.no-ask-continues — No-ask runs never stop for a decision

A workflow in no-ask mode SHALL NOT end at a decision point.

### req.workflows.no-ask-describe-continues — A failed description does not end a no-ask brownfield run

A [brownfield workflow](../../glossary.json#concept.brownfield-workflow) in no-ask mode SHALL NOT end at a `code_to_spec` step that did not end `ok`.

Task validation then decides whether the workspace can still be delivered.

## Results

### req.workflows.report-from-records — The result is built from what the runs recorded

`concorde workflow report` SHALL build the [workflow result](../../glossary.json#concept.workflow-result) only from the workspace's workflow record and the saved [run results](../../glossary.json#concept.run-result), never from values a step agent returned.

### req.workflows.complete-report — Nothing is left out of the report

The workflow result SHALL list every recorded step, every decision, [open question](../../glossary.json#concept.open-question) and deviation of every finished current step as its run reported it, every Spec review's verdict and findings, every check the survey proposed, and every current step that did not end `ok` as a problem with its [error chain](../../glossary.json#concept.error-chain) unchanged.

### req.workflows.chain-on-top — The workflow adds its own link

A workflow result whose status is not `ok` SHALL carry an error link of level `workflow` stating why the workflow stopped and why it cannot handle that itself, with the errors of the steps that stopped it as unchanged causes.

### req.workflows.lost-step — A step that vanished is named

A workflow result SHALL report as lost, with a `workflow` link naming the step key and what was observed, every current step whose run has no result and no running runner, and every key the script reported with `--lost` whose base key has no current step.

The record wins over the script: a reported key with a current step keeps what its run shows,
finished, still running or lost.

### req.workflows.report-saved — Reports are kept beside the record

`concorde workflow report` SHALL save every workflow result it prints, with its Markdown rendering, beside the workspace's workflow record.

A report is written into no decision log: what to copy from it into a task's log is the task
level's decision.

### req.workflows.report-listed — Saved reports are listed in the record

`concorde workflow report` SHALL list every report it saves in the workspace's workflow record.

## Scripts

### req.workflows.one-source — One procedure for both clients

Each workflow's procedure SHALL be written once and rendered by the build for Claude Code and for pi without change to its steps, run arguments, branches, admitted inputs or decision points.

Adapters may differ in command transport and waiting: Claude Code uses a relay subagent and pi a
command-runner agent. Both execute the same procedure against the same run command lines and
assemble the report from the recorded runs.

### req.workflows.script-repeats — The script, not a model, waits for a run

The Claude Code step function SHALL ask for a step again while its outcome says the run is still running, each call waiting at most 100 seconds.

### req.workflows.relay-checked — An outcome for another step is no answer

The Claude Code step function SHALL treat a relayed outcome as no answer when it names another step or a run identity that is not a run's.

### req.workflows.relay-asked-again — A relay that is no answer is asked again

The Claude Code step function SHALL ask its step agent again after an outcome that is no answer until three outcomes in a row have been no answer.

### req.workflows.relay-exhausted — A step without an answer is reported lost

The Claude Code step function SHALL report a step lost after three outcomes in a row that are no answer, with the last relayed outcome attached to the script's result as `relayed`.

### req.workflows.step-agent-relays — Step agents only relay

A step agent SHALL run nothing but `concorde workflow step` or `concorde workflow report`.

It does not perform the worker's job or bypass the run's grant, audit and result handling.

### req.workflows.step-agent-no-change — Step agents change no file

A step agent SHALL change no file.

# Workflows requirements

The Module-wide obligations of [Workflows](module.md). The shapes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete situations.

## Steps

### req.workflows.bound-only — A workflow runs only in a bound workspace

The workflow commands SHALL refuse to run a step or build a report in a worktree whose workspace binding is absent or refused, starting and recording nothing.

### req.workflows.steps-are-runs — Every step is an ordinary run

A workflow step SHALL start its run only as `concorde run <operation> --detach` or `concorde <command> --detach` of the workspace's own `concorde`, in the workspace the step runs in.

The workflow leaves worker launches and service calls inside the run. Client step agents only
relay the workflow commands; they do not perform the worker's job or bypass the run's grant, audit
and result handling.

### req.workflows.one-at-a-time — One run at a time

A workflow SHALL NOT start a step while another process holds the workspace lock of its workspace.

`concorde workflow step` waits for a running run of the workspace before starting its own, and the
runner writes a run's result before it releases the lock, so a finished step always leaves the
workspace free.

### req.workflows.key-idempotent — A step key runs once

`concorde workflow step` SHALL start a run only for a step key with no current step in the workspace's workflow record, or with `--retry` for a key whose current step did not end `ok`, reporting the current step's run otherwise.

### req.workflows.restart-generation — A restart runs a step once more

A step given a restart label SHALL add it to the step key after `#`, so that it starts one new run for that label and finds that run on every later call with the same label.

### req.workflows.step-lock — A step is looked up, started and recorded at once

`concorde workflow step` SHALL look a key up, start its run and record it while holding the workspace's step lock.

### req.workflows.supersede — A rerun supersedes what came after it

Starting a new run for a base key that already has a current step SHALL supersede that step and every step recorded after it.

A superseded step is never found again, so nothing validated or delivered before a retried or
answered step is taken as current.

### req.workflows.refused-recorded — A step that could not start is recorded

A step whose command line the runner rejected, or whose detached runner did not start, SHALL be recorded without a run and with its error link.

### req.workflows.bounded-wait — A step call waits a bounded time

`concorde workflow step` without `--stdin` SHALL return within its `--wait` seconds, exiting with status 3 when the run has not finished.

### req.workflows.answers-new-key — Answers make a new step

A step given answers SHALL pass them to its run with `--answers`, add their digest to the step key and admit with `--input` the latest `ok` run of the same base key.

The digest is taken over the answers list in canonical JSON, so the same answers always name the same
step.

### req.workflows.one-workflow-per-workspace — A workspace runs one workflow

`concorde workflow step` SHALL refuse a step naming a workflow other than the one already recorded for the workspace, and a key already recorded for another Operation or command.

### req.workflows.no-task — Workflows knows no task

No part of Workflows SHALL open, merge, close or escalate a task, or read or write a task record or a decision log.

## Modes

### req.workflows.interactive-stops — Interactive runs stop at decision points

A workflow in interactive mode SHALL end right after a step that did not end `ok` or whose output has decision points its answers did not settle, before starting another step.

### req.workflows.no-ask-continues — No-ask runs never stop for a decision

A workflow in no-ask mode SHALL NOT end at a decision point, nor at a `code_to_spec` step of the brownfield procedure that did not end `ok`.

## Results

### req.workflows.report-from-records — The result is built from what the runs recorded

`concorde workflow report` SHALL build the workflow result only from the workspace's workflow record and the saved run results, never from values a step agent returned.

### req.workflows.complete-report — Nothing is left out of the report

The workflow result SHALL list every recorded step, every decision, open question and deviation of every finished current step as its run reported it, every Spec review's verdict and findings, every check the survey proposed, and every current step that did not end `ok` as a problem with its error chain unchanged.

### req.workflows.chain-on-top — The workflow adds its own link

A workflow result whose status is not `ok` SHALL carry an error link of level `workflow` stating why the workflow stopped and why it cannot handle that itself, with the errors of the steps that stopped it as unchanged causes.

### req.workflows.lost-step — A step that vanished is named

A workflow result SHALL report as lost, with a `workflow` link naming the step key and what was observed, every current step whose run has no result and no running runner, and every key the script reported with `--lost` that has no finished current step.

The record wins over the script: a key with a finished run keeps that run's outcome.

### req.workflows.report-saved — Reports are kept beside the record

`concorde workflow report` SHALL save every workflow result it prints, with its Markdown rendering, beside the workspace's workflow record and list it in that record.

A report is written into no decision log: what to copy from it into a task's log is the task
level's decision.

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

The Claude Code step function SHALL ask its step agent again after an outcome that is no answer, at most three times in a row, and then report the step lost with the last relayed outcome attached to its result as `relayed`.

### req.workflows.step-agent-relays — Step agents only relay

A step agent SHALL run nothing but `concorde workflow step` or `concorde workflow report`, changing no file.

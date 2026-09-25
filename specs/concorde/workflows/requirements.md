# Workflows requirements

The Module-wide obligations of [Workflows](module.md). The shapes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete situations.

## Steps

### req.workflows.steps-are-runs — Every step is an ordinary Operation run

A workflow step SHALL start its Operation only through `concorde run --detach` of the task worktree's own `concorde`, for the workflow's task.

### req.workflows.one-at-a-time — One Operation at a time

A workflow SHALL NOT start a step while an Operation of its task is running.

### req.workflows.key-idempotent — A step key runs once

`concorde workflow step` SHALL start a run only for a step key not yet recorded in the task, or with `--retry` for a key whose recorded run did not end `ok`, reporting the recorded run otherwise.

### req.workflows.bounded-wait — A step call waits a bounded time

`concorde workflow step` without `--stdin` SHALL return within its `--wait` seconds, exiting with status 3 when the run has not finished.

### req.workflows.answers-new-key — Answers make a new step

A step given answers SHALL pass them to its run with `--answers` and add their digest to the step key.

### req.workflows.one-workflow-per-task — A task runs one workflow

`concorde workflow step` SHALL refuse a step naming a workflow other than the one already recorded for the task, and a key already recorded for another Operation.

### req.workflows.task-bounds — Workflows leave task life to the main agent

A workflow SHALL NOT open, merge, close or escalate a task.

## Modes

### req.workflows.interactive-stops — Interactive runs stop at decision points

A workflow in interactive mode SHALL end right after a step whose output has decision points that the step was not given answers for, and before starting another step.

### req.workflows.no-ask-continues — No-ask runs never stop for a decision

A workflow in no-ask mode SHALL NOT end at a decision point, nor at a `code_to_spec` step of the brownfield procedure that did not end `ok`.

## Results

### req.workflows.report-from-records — The result is built from what the hosts recorded

`concorde workflow report` SHALL build the workflow result only from the task record and the saved Operation results, never from values a step agent returned.

### req.workflows.complete-report — Nothing is left out of the report

The workflow result SHALL list every recorded step, every decision, open question and deviation of every finished step, and every step that did not end `ok` as a problem with its error chain unchanged.

### req.workflows.chain-on-top — The workflow adds its own link

A workflow result whose status is not `ok` SHALL carry an error link of level `workflow` stating why the workflow stopped and why it cannot handle that itself, with the errors of the steps that stopped it as unchanged causes.

### req.workflows.lost-step — A step that vanished is named

A workflow result SHALL report as lost, with a `workflow` link naming the step key and what was observed, every step whose run has no result and no running host, and every step the script reported with `--lost`.

### req.workflows.logged — Reports reach the decision log

`concorde workflow report` SHALL append the result's decisions, open questions, deviations and problems to the task's decision log and save the result at `.concorde/tasks/<task-id>.workflow.json`.

## Scripts

### req.workflows.one-source — One procedure for both clients

Each workflow's procedure SHALL be written once and rendered by the build for Claude Code and for pi without change to its steps.

### req.workflows.step-agent-relays — Step agents only relay

A step agent SHALL run nothing but `concorde workflow step` or `concorde workflow report`, changing no file.

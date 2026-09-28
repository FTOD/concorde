# Workflows scenarios

Concrete situations that show the [requirements](requirements.md) of [Workflows](module.md). The
shapes are in the [contracts](contracts.md).

## Steps

### scenario.workflows.step-starts — A step starts and records a run

- GIVEN a task worktree whose binding names the workspace `adopt` and the [Module](../../glossary.json#concept.module) `module.shop`, with no workflow recorded
- WHEN `concorde workflow step --workflow brownfield --mode no-ask --key survey -- survey --modules module.shop` is run there
- THEN it starts `concorde run survey --modules module.shop --detach` with the workspace's own `concorde`
- AND the workspace's [workflow record](../../glossary.json#concept.workflow-record) names the workflow `brownfield` and the key `survey` with the run
- AND once the run has finished it prints the step outcome with state `finished`, the workspace `adopt` and the result's status, and exits with status 0
- AND a step naming the [execution command](../../glossary.json#concept.execution-command) `task-validation` starts `concorde task-validation --detach`, and its outcome carries the readiness's `ready`

### scenario.workflows.unbound-refused — No workflow runs in an unbound worktree

- GIVEN a worktree without a [workspace binding](../../glossary.json#concept.workspace-binding), such as the primary worktree
- WHEN `concorde workflow step` or `concorde workflow report` is run there
- THEN it prints a `component` link `binding_required` naming the worktree and exits with status 1
- AND nothing is started or recorded

### scenario.workflows.step-waits — A long run is awaited by repeated calls

- GIVEN a step whose run takes longer than the step's `--wait`
- WHEN the step command is run
- THEN it prints the step outcome with state `running` and exits with status 3 after at most `--wait` seconds
- AND running the same command again starts no second run and waits for the recorded one
- AND a step whose [workspace lock](../../glossary.json#concept.workspace-lock) another run still holds waits for that run to end before starting its own, within the same bound
- AND when the bound ends while the lock is still held, it prints the step outcome with state `running` and no run and exits with status 3, having started and recorded nothing

### scenario.workflows.step-cached — A finished step returns at once

- GIVEN a workspace whose step `survey` has finished `ok`
- WHEN the same step is asked for again
- THEN no run starts and the recorded outcome is printed at once
- BUT with `--retry` a step whose run ended `failed` starts a new run under the same key

### scenario.workflows.step-refused — A step that does not belong

- GIVEN a workspace whose recorded workflow is `brownfield`, with the key `survey` recorded for the `survey` [Operation](../../glossary.json#concept.operation)
- WHEN a step names another workflow, or the key `survey` for `task-validation`
- THEN the command exits with status 1 and prints the outcome with state `refused` and a `step_rejected` link whose cause, `workflow_conflict` or `step_conflict`, names the recorded workflow or Operation
- AND nothing is started or recorded

## Modes

### scenario.workflows.interactive-pause — An interactive run ends at a survey decision

- GIVEN the [brownfield workflow](../../glossary.json#concept.brownfield-workflow) started in interactive mode in the workspace `adopt`
- WHEN the survey ends `ok` with the decision `d.db-helper`
- THEN no scaffold runs
- AND the [workflow result](../../glossary.json#concept.workflow-result) has status `awaiting_decision`, lists `d.db-helper` as pending with its options, and its `workflow` link gives `decision` as the reason

### scenario.workflows.interactive-resume — The answered workflow goes on

- GIVEN that paused interactive workflow and the developer's answer to `d.db-helper`
- WHEN the workflow is started again with the answer keyed by `survey`
- THEN the first survey is not run again
- AND a new survey step with the answers' digest in its key runs with `--answers` and with `--input` naming the first survey run
- AND its step outcome counts no [decision point](../../glossary.json#concept.decision-point) for the answered `d.db-helper`
- AND the scaffold then admits that new survey run

### scenario.workflows.no-ask-complete — A no-ask run reports everything at the end

- GIVEN the brownfield workflow started in no-ask mode in the workspace `adopt` bound to `module.shop`
- AND the survey proposes `module.checkout` and `module.inventory`, the `code_to_spec` of `module.inventory` ends `blocked`, and the one of `module.checkout` reports an [open question](../../glossary.json#concept.open-question)
- AND task validation finds the workspace ready
- WHEN the workflow runs to its end
- THEN it runs survey, scaffold, the three code_to_spec steps, spec_review, task-validation and `delivery --adoption`, one after another
- AND the workflow result lists the survey's decisions, the open question and the blocked description as a problem with its chain unchanged
- AND the result is saved with its Markdown rendering beside the workspace's workflow record and listed there
- BUT no [decision log](../../glossary.json#concept.decision-log) changes

## Results

### scenario.workflows.failed-chain — A failed step stops the procedure with a whole chain

- GIVEN a no-ask brownfield workflow whose scaffold ends `blocked` with `stale_proposal`
- WHEN the workflow reports
- THEN no code_to_spec step runs
- AND the workflow result has status `blocked` and its error is a `workflow` link whose cause is the scaffold's `command` link, unchanged, down to its own causes

### scenario.workflows.lost — A step whose runner died

- GIVEN a step `describe:module.checkout` whose run has no result and whose runner process has ended
- WHEN the step command is run for that key again
- THEN it prints the step outcome with state `lost` and a `workflow` link naming the key, the run and the dead runner, with the end of the runner's output, and exits with status 1
- AND `concorde workflow report --lost describe:module.checkout` lists the step as a lost problem and has status `failed`
- BUT a key named with `--lost` whose current step has a finished run keeps that run's outcome

### scenario.workflows.relay-refused — A step agent mistypes the step command

- GIVEN a Claude Code workflow run whose [step agent](../../glossary.json#concept.step-agent) for `delivery` drops a field while retyping the step command, so that the command refuses the request with `invalid_request`
- WHEN the step function receives that refusal, which names no step
- THEN it asks a step agent again with the same command, and goes on with the procedure once an outcome for `delivery` comes back
- AND after three refusals in a row it reports `delivery` lost, and the script's result carries the last refusal under `relayed`, with the key and the number of attempts

### scenario.workflows.superseded — A retried step supersedes later steps

- GIVEN a workspace whose steps `survey`, `scaffold`, `describe:module.checkout`, `validate` and `delivery` are recorded, the describe step `failed`
- WHEN the describe step is asked for again with `--retry`
- THEN a new run starts for it, and `validate` and `delivery` are superseded
- AND asking for `validate` again starts a new task-validation run instead of returning the earlier one
- AND the workflow result lists the superseded steps apart and takes nothing else from them

### scenario.workflows.restarted — An ok step is run again under a restart label

- GIVEN a workspace whose steps `survey`, `scaffold` and `validate` are recorded and `ok`
- WHEN the scaffold step is asked for with the restart label `2`
- THEN a new run starts under the key `scaffold#2`, and the earlier scaffold and `validate` are superseded
- AND asking for it again with the label `2` starts nothing and finds that run

### scenario.workflows.refused-step — A step whose run cannot start

- GIVEN a workspace running the brownfield workflow
- WHEN a step names an argument that the runner rejects, such as `task-validation --bogus`
- THEN the step is recorded without a run and with a `step_refused` link carrying the runner's message, the step outcome has state `refused`, and the command exits with status 1
- AND the workflow result lists it as a problem and has status `failed`

### scenario.workflows.reviews-reported — Spec review findings reach the result

- GIVEN a no-ask brownfield workflow whose `spec_review` step ends `ok` with verdict `changes_required` and two blocking findings
- WHEN the workflow reports
- THEN the workflow result lists that review's verdict and both findings with their step and run
- AND the checks the survey proposed are listed for the developer to configure

### scenario.workflows.report-ignores-relay — The report reads the recorded results

- GIVEN a finished workflow whose step agent returned a summary that differs from the saved [run result](../../glossary.json#concept.run-result)
- WHEN `concorde workflow report` runs
- THEN the workflow result states the saved result's status, summary and error

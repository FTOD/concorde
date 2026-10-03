# Workflows scenarios

Concrete situations that show the [requirements](requirements.md) of [Workflows](module.md). The
shapes are in the [contracts](contracts.md).

## Steps

### scenario.workflows.step-starts — A step starts and records a run

- GIVEN a task worktree whose binding names the workspace `adopt` and the [Module](../glossary.json#concept.module) `module.shop`, with no workflow recorded
- WHEN `concorde workflow step --workflow brownfield --mode no-ask --key survey -- survey --modules module.shop` is run there
- THEN it starts `concorde run survey --modules module.shop --detach` with the workspace's own `concorde`
- AND the workspace's [workflow record](../glossary.json#concept.workflow-record) names the workflow `brownfield` and the key `survey` with the run
- AND the run's [trace node](../glossary.json#concept.trace-node) lies in `run/` of the step's node `workflow/steps/1-survey/` of the workspace folder, whose `trace.json` names the key and the run
- AND once the run has finished it prints the step outcome with state `finished`, the workspace `adopt` and the result's status, and exits with status 0

### scenario.workflows.step-starts-command — A step starts an execution command

- GIVEN the task worktree of the workspace `adopt`, running the brownfield workflow
- WHEN `concorde workflow step --workflow brownfield --mode no-ask --key validate -- task-validation` is run there
- THEN it starts the [execution command](../glossary.json#concept.execution-command) as `concorde task-validation --detach` with the workspace's own `concorde`, not through `concorde run`
- AND once the run has finished its step outcome names `task-validation` and carries, unchanged in its `data`, what the run handed the script, such as the readiness's `ready`

### scenario.workflows.unbound-refused — No workflow runs in an unbound worktree

- GIVEN a worktree without a [workspace binding](../glossary.json#concept.workspace-binding), such as the primary worktree
- WHEN `concorde workflow step` or `concorde workflow report` is run there
- THEN it prints a `component` link `binding_required` naming the worktree and exits with status 1
- AND nothing is started or recorded

### scenario.workflows.step-waits — A long run is awaited by repeated calls

- GIVEN a step whose run takes longer than the step's `--wait`
- WHEN the step command is run
- THEN it prints the step outcome with state `running` and exits with status 3 after at most `--wait` seconds
- AND running the same command again starts no second run and waits for the recorded one

### scenario.workflows.step-outlives-call — A step's run outlives the call that started it

- GIVEN a Claude Code workflow run in a [task session](../glossary.json#concept.task-session), whose step agents each relay one short turn
- WHEN the step function asks for a step whose run takes longer than one call
- THEN its step agent calls the `workflow_step` tool the workflow part registers with the [project MCP server](../glossary.json#concept.project-mcp-server), with the step request as an object, and runs no Bash command
- AND the server starts the step's run as a process of its own, so the run lives on after that call and after every later one, until it ends and saves its result, even when the session has ended meanwhile

### scenario.workflows.step-waits-lock — A step waits for the workspace lock before it starts

- GIVEN a workspace whose [workspace lock](../glossary.json#concept.workspace-lock) another run holds, and no step `survey` recorded
- WHEN the step command is run for `survey`
- THEN it starts no run while the lock is held, waiting within its `--wait` for that run to end
- AND when the bound ends while the lock is still held, it prints the step outcome with state `running` and no run and exits with status 3, having started and recorded nothing
- AND once the lock is free, running the same command again starts the step's run

### scenario.workflows.step-retired — A step waiting while its task is closed

- GIVEN a task worktree of the workspace `adopt` whose workflow lock the close of its task holds, and the step command run there for `survey`, waiting for that lock
- WHEN the close removes the worktree with its binding, moves the workspace folder to the history and removes the workflow lock file while still holding it, then releases it
- THEN the step prints an outcome with state `refused`, no run and a `workspace_retired` link whose cause, a `Workflows (workflow lock)` link `lock_removed`, names the removed lock file, and exits with status 1
- AND it started no run, the history the close moved holds nothing of the step, and no workspace folder is created again where the moved one was
- AND a step that takes the workflow lock after the close, finding the binding gone or changed, is refused with `workspace_retired` the same way, its cause `binding_gone` or `binding_changed`
- AND `concorde workflow report` there is refused with a `component` link `workspace_retired` of reason `environment`

### scenario.workflows.step-cached — A finished step returns at once

- GIVEN a workspace whose step `survey` has finished `ok`
- WHEN the same step is asked for again
- THEN no run starts and the recorded outcome is printed at once

### scenario.workflows.step-retried — A failed step runs again with `--retry`

- GIVEN a workspace whose step `validate` has finished `failed`, so that asking for it again prints that outcome and starts nothing
- WHEN the step is asked for again with `--retry`
- THEN a new run starts under the same key `validate`
- AND the step outcome names the new run instead of the failed one

### scenario.workflows.step-refused — A step that does not belong

- GIVEN a workspace whose recorded workflow is `brownfield`, with the key `survey` recorded for the `survey` [Operation](../glossary.json#concept.operation)
- WHEN a step names another workflow, or the key `survey` for `task-validation`
- THEN the command exits with status 1 and prints the outcome with state `refused` and a `step_rejected` link whose cause, `workflow_conflict` or `step_conflict`, names the recorded workflow or Operation
- AND nothing is started or recorded

## Modes

### scenario.workflows.interactive-pause — An interactive run ends at a survey decision

- GIVEN the [brownfield workflow](../glossary.json#concept.brownfield-workflow) started in interactive mode in the workspace `adopt`
- WHEN the survey ends `ok`, its output declaring the decision `d.db-helper` as a decision point under the step output convention
- THEN no scaffold runs
- AND the [workflow result](../glossary.json#concept.workflow-result) has status `awaiting_decision`, lists `d.db-helper` as pending with its options, and its `workflow` link gives `decision` as the reason

### scenario.workflows.interactive-resume — The answered workflow goes on

- GIVEN that paused interactive workflow and an answer to `d.db-helper`, given by the [main agent](../glossary.json#concept.main-agent) or by the developer
- WHEN the workflow is started again with the answer keyed by `survey`
- THEN the first survey is not run again
- AND a new survey step with the answers' digest in its key runs with `--answers` and with `--input` naming the first survey run
- AND its step outcome counts no [decision point](../glossary.json#concept.decision-point) for the answered `d.db-helper`
- AND the workflow result lists `d.db-helper` as decided by whoever gave the answer, `main-agent` or `developer`
- AND the scaffold then admits that new survey run

### scenario.workflows.no-ask-complete — A no-ask run reports everything at the end

- GIVEN the brownfield workflow started in no-ask mode in the workspace `adopt` bound to `module.shop`
- AND the survey proposes `module.checkout` and `module.inventory`, the `code_to_spec` of `module.inventory` ends `blocked`, and the one of `module.checkout` reports an [open question](../glossary.json#concept.open-question)
- AND task validation finds the workspace ready
- WHEN the workflow runs to its end
- THEN it runs survey, scaffold, the three code_to_spec steps, spec_review, task-validation and `delivery --adoption`, one after another
- AND the workflow result lists the survey's decisions, the open question and the blocked description as a problem with its chain unchanged
- AND the result is saved with its Markdown rendering in the workflow's trace node and listed in the workflow record
- BUT no [decision log](../glossary.json#concept.decision-log) changes

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

### scenario.workflows.lost-finished — A key reported lost keeps its finished run

- GIVEN a workspace whose step `survey` has finished `ok`
- WHEN `concorde workflow report --lost survey` runs, because a step agent returned nothing for that step
- THEN the workflow result lists `survey` with its run's status `ok`
- AND lists no lost problem for it, since the record wins over what the step agents relayed

### scenario.workflows.relay-refused — A step agent mistypes the step request

- GIVEN a Claude Code workflow run whose [step agent](../glossary.json#concept.step-agent) for `delivery` drops a field while copying the step request, so that the step command refuses it with `invalid_request`
- WHEN the step function receives that refusal, which names no step
- THEN it asks a step agent again with the same request, and goes on with the procedure once an outcome for `delivery` comes back
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

### scenario.workflows.reviews-reported — The notes of the runs reach the result

- GIVEN a no-ask brownfield workflow whose `spec_review` step ends `ok` and declares in its output a review note with the verdict `changes_required` and one Module's outcome with a count of two blocking findings, and whose survey declared a note for each check it proposes
- WHEN the workflow reports
- THEN the workflow result lists that review note unchanged, with its step and run
- AND lists the survey's notes with the proposed checks, for the developer to configure

### scenario.workflows.report-ignores-relay — The report reads the recorded results

- GIVEN a finished workflow whose step agent returned a summary that differs from the saved [run result](../glossary.json#concept.run-result)
- WHEN `concorde workflow report` runs
- THEN the workflow result states the saved result's status, summary and error

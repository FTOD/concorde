# Workflows scenarios

Concrete situations that show the [requirements](requirements.md) of [Workflows](module.md). The
shapes are in the [contracts](contracts.md).

## Steps

### scenario.workflows.step-starts — A step starts and records a run

- GIVEN an open task `adopt` bound to `module.shop` with no workflow recorded
- WHEN `concorde workflow step --task adopt --workflow brownfield --mode no-ask --key survey -- survey --modules module.shop` is run
- THEN it starts `concorde run survey --task adopt --modules module.shop --detach` with the task worktree's `concorde`
- AND the task record names the workflow `brownfield` and the key `survey` with the run
- AND once the run has finished it prints the step outcome with state `finished` and the result's status and exits with status 0

### scenario.workflows.step-waits — A long run is awaited by repeated calls

- GIVEN a step whose run takes longer than the step's `--wait`
- WHEN the step command is run
- THEN it prints the step outcome with state `running` and exits with status 3 after at most `--wait` seconds
- AND running the same command again starts no second run and waits for the recorded one

### scenario.workflows.step-cached — A finished step returns at once

- GIVEN a task whose step `survey` has finished `ok`
- WHEN the same step is asked for again
- THEN no run starts and the recorded outcome is printed at once
- BUT with `--retry` a step whose run ended `failed` starts a new run under the same key

### scenario.workflows.step-refused — A step that does not belong

- GIVEN a task whose recorded workflow is `brownfield`, or whose key `survey` is recorded for the `survey` Operation
- WHEN a step names another workflow, or the key `survey` for `validate`
- THEN the command exits with status 1 and prints an error link naming the recorded workflow or Operation
- AND nothing is started or recorded

## Modes

### scenario.workflows.interactive-pause — An interactive run ends at a survey decision

- GIVEN the brownfield workflow started in interactive mode for task `adopt`
- WHEN the survey ends `ok` with the decision `d.db-helper`
- THEN no scaffold runs
- AND the workflow result has status `awaiting_decision`, lists `d.db-helper` as pending with its options, and its `workflow` link gives `decision` as the reason

### scenario.workflows.interactive-resume — The answered workflow goes on

- GIVEN that paused interactive workflow and the developer's answer to `d.db-helper`
- WHEN the main agent starts the workflow again with the answer keyed by `survey`
- THEN the first survey is not run again
- AND a new survey step with the answers' digest in its key runs and follows the answer
- AND the scaffold then admits that new survey run

### scenario.workflows.no-ask-complete — A no-ask run reports everything at the end

- GIVEN the brownfield workflow started in no-ask mode for task `adopt` bound to `module.shop`
- AND the survey proposes `module.checkout` and `module.inventory`, the `code_to_spec` of `module.inventory` ends `blocked`, and the one of `module.checkout` reports an open question
- WHEN the workflow runs to its end
- THEN it runs survey, scaffold, the three code_to_spec steps, spec_review, validate and, when validation is ready, delivery, one after another
- AND the workflow result lists the survey's decisions, the open question and the blocked description as a problem with its chain unchanged
- AND the decision log of the task holds the same decisions, questions and problem

## Results

### scenario.workflows.failed-chain — A failed step stops the procedure with a whole chain

- GIVEN a no-ask brownfield workflow whose scaffold ends `blocked` with `stale_proposal`
- WHEN the workflow reports
- THEN no code_to_spec step runs
- AND the workflow result has status `blocked` and its error is a `workflow` link whose cause is the scaffold's Operation link, unchanged, down to its own causes

### scenario.workflows.lost — A step agent that returned nothing

- GIVEN a Claude Code step agent that ended without output while its run was still recorded as running and then its host died
- WHEN the script runs `concorde workflow report --task adopt --lost describe:module.checkout`
- THEN the workflow result lists the step as lost with a `workflow` link naming the key and the run
- AND the result has status `failed`

### scenario.workflows.report-ignores-relay — The report reads the hosts' results

- GIVEN a finished workflow whose step agent returned a summary that differs from the saved Operation result
- WHEN `concorde workflow report` runs
- THEN the workflow result states the saved result's status, summary and error

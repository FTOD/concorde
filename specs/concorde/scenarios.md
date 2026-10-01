# Framework scenarios

These scenarios describe whole flows that cross several Modules, seen from the developer, the
[main agent](glossary.json#concept.main-agent) and its [task sessions](glossary.json#concept.task-session). The precise behaviour of every step belongs to the
[Module](glossary.json#concept.module) that performs it; a scenario here promises only what the
Modules achieve together.

## Adopting Concorde

### scenario.concorde.adopt-initialize — Installing and initializing a new project

- GIVEN a project in which Concorde has never been installed
- WHEN the developer runs the installer
- AND initialization proposes a first [Spec](glossary.json#concept.spec) and then applies that exact proposal
- THEN the project's configuration binds the [Protocol copy](glossary.json#concept.protocol-copy) the installer placed under `.concorde/protocol/`
- AND the project validates without errors
- AND its root Module entry states that the project's purpose and behaviour are not yet specified

### scenario.concorde.adopt-brownfield — Describing an existing codebase in no-ask mode

- GIVEN an initialized project whose code came before its Specs, with the root Module binding every existing file
- WHEN the main agent opens a task bound to the root Module
- AND the task's task session runs the [brownfield workflow](glossary.json#concept.brownfield-workflow) in its worktree in no-ask [mode](glossary.json#concept.workflow-mode)
- AND the survey proposes child Modules, every `code_to_spec` run ends `ok` and `task-validation` finds the workspace ready
- THEN the workflow runs `survey`, `scaffold`, one `code_to_spec` per described Module, `spec_review`, `task-validation` and `delivery` in the task's worktree, one run at a time
- AND the delivered task branch holds child Modules whose entries describe the code they bind
- AND no implementation file changed except existing tests, which gained only the `verifies` declarations and helper that [Adoption](execution/operations/adoption/requirements.md#req.adoption.test-edits-limited) adds
- AND the [workflow result](glossary.json#concept.workflow-result) lists every decision the workflow took and every [open question](glossary.json#concept.open-question) about intent it did not write as a promise
- AND the main agent can merge the task branch into the primary branch

A no-ask run in which a `code_to_spec` run did not end `ok` goes on as well, and may deliver a
Module whose entry is still a stub or a partial description; its workflow result names that step's
problem ([Workflows](execution/workflows/requirements.md#req.workflows.no-ask-describe-continues)).

## Working on a task

### scenario.concorde.task-to-merge — A task from opening to merge

- GIVEN an initialized project whose Specs validate and whose [configured checks](glossary.json#concept.configured-check) pass
- AND a Module whose Spec states every promise the change needs
- AND no change reaches the primary branch while the task runs
- WHEN the main agent opens a task for that Module
- AND the task's task session runs `implement` for that Module in the task worktree, which ends `ok`
- AND runs `task-validation`, which finds the workspace ready, and then `delivery` there
- THEN the task branch holds one [delivery commit](glossary.json#concept.delivery-commit) with the change
- AND every one of these runs took its workspace from the worktree's [workspace binding](glossary.json#concept.workspace-binding), without being given the task
- AND `concorde task show` reports the task delivered, derived from that commit and the runs the [run store](glossary.json#concept.run-store) holds, while its [task record](glossary.json#concept.task-record) was never written by a run
- AND the main agent can merge the task branch into the primary branch
- AND the primary worktree was never written by a worker

### scenario.concorde.worker-escalates — A worker that needs more than its grant

- GIVEN a task whose worker, with a write its harness did not refuse, changes a file outside its grant that Git does not ignore, and the change persists in the task worktree
- WHEN the [Operation](glossary.json#concept.operation) runs
- THEN the Operation's audit finds the change and the run ends `failed`
- AND the [run result](glossary.json#concept.run-result) carries an [error chain](glossary.json#concept.error-chain) whose top link, the Operation's, names the file and gives `permission` as the reason it cannot handle the error
- AND the link below it is Workers', with the audit as evidence
- BUT the Operation does not retry the worker with a wider grant

A write to a Git-ignored path, or one that lands on a throw-away filesystem and never reaches the
worktree, is not seen by the audit ([Harness](harness/module.md#known-limits-of-v1)).

### scenario.concorde.parallel-tasks — Two tasks in parallel

- GIVEN two tasks whose Modules and the files those Modules bind do not overlap, each in its own worktree
- WHEN their task sessions run `implement` in both worktrees at the same time, each run ending `ok`
- AND each task session then runs `task-validation`, which finds its workspace ready, and `delivery` in its own worktree
- THEN each worker's grant comes from its own task's worktree
- AND neither task's changes appear in the other's worktree
- AND both tasks are delivered
- AND the main agent can merge both task branches into the primary branch

## Errors

### scenario.concorde.error-chain-to-developer — An error the main agent cannot decide reaches the developer whole

- GIVEN a task whose `implement` worker finds that the Spec does not state a promise it needs
- WHEN the worker ends `blocked` with its detailed error and the reason it cannot handle it
- AND the Operation returns its run result
- AND the task's task session escalates that run to the main agent with `concorde task escalate --by task-session`
- AND the main agent, which may not decide it either, escalates the task session's escalation to the developer with `concorde task escalate`
- THEN the main agent's escalation is one chain: the main agent's link, then the task session's, then the Operation's, then Workers', then the worker's own
- AND every link gives its level, its actor, a detailed description and the reason that level could not handle the error
- AND the worker's description, evidence and options arrive unchanged
- AND each escalation is recorded in the task's [trace node](glossary.json#concept.trace-node) and the [decision log](glossary.json#concept.decision-log) and printed rendered for its receiver

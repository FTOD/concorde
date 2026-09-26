# Framework scenarios

These scenarios describe whole flows that cross several Modules, seen from the developer and the
main agent. The precise behaviour of every step belongs to the Module that performs it; a scenario
here promises only what the Modules achieve together. They are verified by end-to-end acceptance
tests that drive the installer and the `concorde` command with a fake worker; what Claude Code
itself enforces is verified by the live worker test of Workers.

## Adopting Concorde

### scenario.concorde.adopt-initialize — Installing and initializing a new project

- GIVEN a project in which Concorde has never been installed
- WHEN the developer runs the installer
- AND initialization proposes a first Spec and then applies that exact proposal
- THEN the project's configuration binds the Protocol copy the installer placed under `.concorde/protocol/`
- AND the project validates without errors
- AND its root Module entry states that the project's purpose and behaviour are not yet specified

### scenario.concorde.adopt-brownfield — Describing an existing codebase in no-ask mode

- GIVEN an initialized project whose code came before its Specs, with the root Module binding every existing file
- WHEN the main agent opens a task bound to the root Module
- AND runs the `brownfield` workflow in it in no-ask mode
- THEN the workflow runs `survey`, `scaffold`, one `code_to_spec` per described Module, `spec_review`, `validate` and `delivery` in that task, one Operation at a time
- AND the delivered task branch holds child Modules whose entries describe the code they bind
- AND no implementation file changed
- AND the workflow result lists every decision the workflow took and every open question about intent it did not write as a promise
- AND the main agent can merge the task branch into the primary branch

## Working on a task

### scenario.concorde.task-to-merge — A task from opening to merge

- GIVEN an initialized project whose Specs validate
- WHEN the main agent opens a task for one Module
- AND runs `implement` for that Module in the task worktree
- AND runs `validate` and then `delivery` for the task
- THEN the task branch holds one delivery commit with the change and its evidence
- AND the main agent can merge the task branch into the primary branch
- AND the primary worktree was never written by a worker

### scenario.concorde.worker-escalates — A worker that needs more than its grant

- GIVEN a task whose worker needs to change a file outside its grant
- WHEN the Operation runs
- THEN the write does not stand: the worker's settings refuse it, and a write that slips through fails the host's audit
- AND the Operation result carries an error chain whose top link, the Operation's, names the file and gives `permission` as the reason it cannot handle the error
- AND the link below it is Workers', with the audit as evidence
- BUT the Operation does not retry the worker with a wider grant

### scenario.concorde.parallel-tasks — Two tasks in parallel

- GIVEN two tasks for different Modules, each in its own worktree
- WHEN the main agent runs Operations in both at the same time
- THEN each worker's grant comes from its own task's worktree
- AND neither task's changes appear in the other's worktree
- AND both tasks can be delivered and merged

## Errors

### scenario.concorde.error-chain-to-developer — An error the main agent cannot decide reaches the developer whole

- GIVEN a task whose `implement` worker finds that the Spec does not state a promise it needs
- WHEN the worker ends `blocked` with its detailed error and the reason it cannot handle it
- AND the Operation returns its result
- AND the main agent escalates the result to the developer with `concorde task escalate`
- THEN the escalation is one chain: the main agent's link, then the Operation's, then Workers', then the worker's own
- AND every link gives its level, its actor, a detailed description and the reason that level could not handle the error
- AND the worker's description, evidence and options arrive unchanged
- AND the chain is recorded in the task record and the decision log and printed rendered for the developer

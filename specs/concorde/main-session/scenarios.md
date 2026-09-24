# Main session scenarios

Situations the [main-session guidance](module.md) prepares the main agent for. The tests that will
check the rendered guidance against them are pending.

## Working method

### scenario.main-session.pi-run-view — pi shows every run and its worker's progress

- GIVEN a pi main session with the run view and an Operation run whose worker is in its second round
- WHEN the run view reads the progress files
- THEN it shows the run with its task, Operation, step, the worker's round and latest tool call
- AND a worker of another host process or an earlier run is not attributed to it
- AND a finished run shows `completed`, `stopped` or `failed` for `ok`, `blocked` or `failed` with the result's summary
- AND a run whose host process ended without finishing shows `failed`

### scenario.main-session.change-through-task — The guidance routes an agreed change through a task

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to carry out a change agreed with the developer
- THEN it is told to open a task with its own branch and worktree for the Modules involved
- AND to run the Operations the change needs in that worktree in background Bash
- BUT it is told never to edit Specs or code in the primary worktree itself

### scenario.main-session.parallel-tasks — The guidance allows parallel work only between worktrees

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to plan several changes
- THEN it is told to run tasks in parallel only in separate worktrees whose Modules and shared files do not overlap
- BUT to run tasks that write the same Module or shared file one after another

### scenario.main-session.merge-delivered — The guidance merges delivered work without asking

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do after `delivery` committed a task's change with its evidence
- THEN it is told to merge the task branch into the primary branch without asking the developer
- AND to close the task as merged and report the merge

## Escalation

### scenario.main-session.ordinary-decision — The guidance decides ordinary questions and reports them

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle an Operation result blocked on a choice of ordinary scope, such as a name or an internal structure
- THEN it is told to decide, to record the decision and its reason in the task's decision log and to report it at the end
- BUT not to stop and ask the developer

### scenario.main-session.major-decision — The guidance escalates major decisions with their evidence

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a result whose options would change what a Module promises to its users
- THEN it is told to ask the developer before acting
- AND to escalate with `concorde task escalate`, adding its own link on top of the error chain instead of replacing it with a summary

### scenario.main-session.read-error-chain — The guidance reads the whole error chain

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a result that is not `ok`
- THEN it is told that the result carries an error chain in `error`, what each link holds, and to read the whole chain before deciding

## Issues

### scenario.main-session.solve-issue — The guidance solves Issues through tasks

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to solve an open Issue owned by a Module
- THEN it is told to open a task for that Module and run the Operations that fix the problem
- AND to close the Issue on the task branch with the evidence, so the closure is merged with the fix

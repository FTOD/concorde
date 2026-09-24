# Main session scenarios

Situations the [main-session guidance](module.md) prepares the main agent for. The tests that will
check the rendered guidance against them are pending.

## Working method

### scenario.main-session.change-through-task — The guidance routes an agreed change through a task

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to carry out a change agreed with the developer
- THEN it is told to open a task with its own branch and worktree for the Modules involved
- AND to enter that worktree and make the change there, directly or with Operations run in background Bash
- AND to run every `concorde` command for the task with the worktree's own copy
- BUT it is told never to change Specs or code in the primary worktree

### scenario.main-session.parallel-tasks — The guidance allows parallel work only between worktrees

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to plan several changes
- THEN it is told to run tasks in parallel only in separate worktrees whose Modules and shared files do not overlap
- BUT to run tasks that write the same Module or shared file one after another

### scenario.main-session.split-into-sessions — The guidance hands split work to task sessions

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to carry out work it split into several tasks
- THEN it is told to start one task session per task with `concorde task session`, naming its own session
- AND to stay in the primary worktree while they run, being inside at most one task at a time itself
- AND to answer a task session's escalation or pass it to the developer with its own link on top

### scenario.main-session.task-session-role — The task-session guidance keeps a session within its task

- GIVEN the rendered task-session guidance
- WHEN a task session reads how to work
- THEN it is told to work only inside its task worktree with the worktree's own `concorde`
- AND to escalate beyond its task's goal or Modules with `concorde task escalate --by task-session` and SendMessage
- AND to report to the main agent when the task is delivered or cannot go further
- BUT never to merge the task branch or close the task

### scenario.main-session.merge-delivered — The guidance merges delivered work without asking

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do after `delivery` committed a task's change with its evidence
- THEN it is told to leave the task worktree and merge the task branch into the primary branch without asking the developer
- AND to validate the primary branch, close the task as merged and report the merge

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

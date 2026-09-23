# Main session scenarios

Situations the [main-session guidance](module.md) prepares the main agent for. The tests that will
check the rendered guidance against them are pending.

## Working method

### scenario.main-session.change-through-task — A requested change runs as a task

- GIVEN a developer who has agreed a change to one Module with the main agent
- WHEN the main agent carries it out
- THEN it opens a task with its own branch and worktree for that Module
- AND runs the Operations the change needs in that worktree in background Bash
- BUT it does not edit the Module's Specs or code itself

### scenario.main-session.parallel-tasks — Independent work runs in parallel

- GIVEN two agreed changes whose Modules and shared files do not overlap
- WHEN the main agent plans them
- THEN it opens one task for each and runs their Operations at the same time
- BUT two changes that write the same Module run one after another

### scenario.main-session.merge-delivered — A delivered task is merged without asking

- GIVEN a task whose `delivery` committed the change and its evidence on the task branch
- WHEN the main agent reads that result
- THEN it merges the task branch into the primary branch without asking the developer
- AND records the merge and reports it in its summary

## Escalation

### scenario.main-session.ordinary-decision — An ordinary uncertainty is decided and reported

- GIVEN an Operation result that is `blocked` on a choice of ordinary scope, such as a name or an internal structure
- WHEN the main agent handles it
- THEN it decides, records the decision and its reason in the task's decision log and re-runs the Operation
- AND reports the decision in its final summary
- BUT it does not stop to ask the developer

### scenario.main-session.major-decision — A major decision is escalated

- GIVEN an Operation result whose options would change what a Module promises to its users
- WHEN the main agent handles it
- THEN it records the escalation in the task's decision log
- AND asks the developer with the problem, the evidence and the options before acting

## Issues

### scenario.main-session.solve-issue — An Issue is solved through a task

- GIVEN an open Issue owned by a Module
- WHEN the developer asks the main agent to solve it
- THEN the main agent opens a task for that Module and runs the Operations that fix the problem
- AND closes the Issue on the task branch with the evidence before merging it

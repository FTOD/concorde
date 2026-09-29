# Tracing scenarios

Concrete situations that show the [requirements](requirements.md) at work. The record, the layout
and the command are defined in the [contracts](contracts.md).

## Reading

### scenario.tracing.show-task — A task's trace with its cost rolled up

- GIVEN a current task whose workspace ran an [Operation](../glossary.json#concept.operation) with one worker run of two rounds, each round recording its tokens and cost, and then `delivery`
- WHEN the [main agent](../glossary.json#concept.main-agent) runs `concorde trace show <task>`
- THEN it prints the task's node with its workspace, the two runs below it, the worker run below the Operation's run and the rounds below the worker run
- AND each node's `rolled_up` sums the tokens, cost and turns of its whole subtree, the task's being the sum of the two rounds
- AND each node's own `usage` is as its `trace.json` records it
- BUT nothing is written

### scenario.tracing.show-by-identity — A run is found by its identity

- GIVEN a run started by a [workflow step](../glossary.json#concept.workflow-step), whose folder lies in the step's folder, and an [unbound run](../glossary.json#concept.unbound-run) of the primary worktree
- WHEN `concorde trace show` is given either run's identity
- THEN it finds and shows that run's node, the unbound run as a node of its own
- AND for an identity it finds nowhere it refuses with `unknown_node`, naming the directories it searched

### scenario.tracing.lost-run — A run whose runner died is lost

- GIVEN a run whose `trace.json` says `running` and whose worker run says `running`, and no process holding its [run lock](../glossary.json#concept.run-lock)
- WHEN `concorde trace show` shows it
- THEN the run and its worker run are shown `lost`

### scenario.tracing.list — Current tasks, history and unbound runs are listed

- GIVEN two current tasks, one closed task in the history and one unbound run
- WHEN `concorde trace list --history --unbound` runs
- THEN it lists the four nodes with their status and rolled-up usage and without their children

### scenario.tracing.history-reads-alike — A moved task reads the same

- GIVEN a task's folder with its nodes, moved unchanged from `tasks/<task>/` to `history/<task>/`
- WHEN `concorde trace show <task>` runs
- THEN it prints the same nodes, statuses and usage as before the move, with the new folder as `path`

## Removing

### scenario.tracing.prune — Retention removes only what has ended long enough ago

- GIVEN an unbound run that ended 8 days ago, one that ended yesterday, one still running and a history folder closed a year ago, without a Tracing configuration
- WHEN `concorde trace prune` runs
- THEN it removes only the unbound run that ended 8 days ago and prints it
- AND with `--dry-run` it prints the same and removes nothing
- AND with a configuration whose `history_days` is 30 it also removes the history folder

## Locks

### scenario.tracing.run-lock-lifetime — A run lock exists only while its runner runs

- GIVEN a run started with `--detach`
- WHEN an observer looks while the run runs and again after it ended
- THEN `.concorde/locks/runs/<run>.lock` exists and is held while the run runs
- AND the file no longer exists once the runner exited
- AND no lock file lies inside the run's folder

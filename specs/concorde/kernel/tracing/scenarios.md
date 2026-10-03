# Tracing scenarios

Concrete situations that show the [requirements](requirements.md) at work. The record, the layout
and the command are defined in the [contracts](contracts.md).

## Reading

### scenario.tracing.show-task — A task's trace with its cost rolled up

- GIVEN a current task whose workspace ran an [Operation](../../glossary.json#concept.operation) with one worker run of two rounds, each round recording its tokens and cost, and then `delivery`
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `concorde trace show <task>`
- THEN it prints the task's node with its workspace, the two runs below it, the worker run below the Operation's run and the rounds below the worker run
- AND each node's `rolled_up` sums the tokens, cost and turns of its whole subtree, the task's being the sum of the two rounds
- AND each node's own `usage` is as its `trace.json` records it
- BUT nothing is written

### scenario.tracing.show-by-identity — A run is found by its identity

- GIVEN a run started by a [workflow step](../../glossary.json#concept.workflow-step), whose folder lies in the step's folder, an [unbound run](../../glossary.json#concept.unbound-run) of the primary worktree and a bound run refused in the lobby before it held its workspace's lock
- WHEN `concorde trace show` is given any of these runs' identities
- THEN it finds and shows that run's node, the unbound run and the run of the lobby as nodes of their own
- AND for an identity it finds nowhere it refuses with `unknown_node`, naming the directories it searched

### scenario.tracing.lost-run — A run whose runner died is lost

- GIVEN a run whose `trace.json` says `running` and whose worker run says `running`, and no process holding its [run lock](../../glossary.json#concept.run-lock)
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

## Recording

### scenario.tracing.created-or-found — A node tells what it created from what it found

- GIVEN a run that created a commit, and a later run that found that commit at the branch head and reported it instead of creating one
- WHEN each run's node records its references
- THEN the first node references the commit with `commit`
- AND the later node references the same commit with `found_commit`, and not with `commit`
- AND both nodes satisfy the node contract, which refuses a reference of any other relation

### scenario.tracing.kind-registered — A node is checked against the registration of its kind

- GIVEN the node kinds the installed parts registered, such as Check execution's `check` with its content type and the metadata `check` and `module`
- WHEN a producer writes a node of a kind no installed part registered, a `check` node listing the metadata `workspace`, or a `check` node whose content is of another type
- THEN each write is refused, the first two with `node_invalid` and the last with `content_invalid`, and no `trace.json` is written
- AND a `check` node with its own metadata and content is written

## Removing

### scenario.tracing.prune — Retention removes only what has ended long enough ago

- GIVEN an unbound run that ended 8 days ago, one that ended yesterday, one still running, a run refused in the lobby 8 days ago, a history folder closed a year ago whose [task sessions](../../glossary.json#concept.task-session) and worker runs kept their transcripts, and one closed two days ago with a transcript, without a Tracing configuration
- WHEN `concorde trace prune` runs
- THEN it removes the unbound run that ended 8 days ago, the run of the lobby and the conversation records of the folder closed a year ago, and prints each
- AND the year-old folder keeps its [decision log](../../glossary.json#concept.decision-log) and [trace nodes](../../glossary.json#concept.trace-node), and the folder closed two days ago keeps its transcript
- AND with `--dry-run` it prints the same and removes nothing
- AND with a configuration whose `history_days` is 30 it also removes the year-old history folder

## Locks

### scenario.tracing.run-lock-lifetime — A run lock exists only while its runner runs

- GIVEN a run started with `--detach`
- WHEN an observer looks while the run runs and again after it ended
- THEN `.concorde/locks/runs/<run>.lock` exists and is held while the run runs
- AND the file no longer exists once the runner exited
- AND no lock file lies inside the run's folder

### scenario.tracing.lock-holder-line — The holder line names the session and the task

- GIVEN a process whose environment names Claude Code session `s-7`
- WHEN it takes the [merge lock](../../glossary.json#concept.merge-lock) for `concorde task merge` of task `t1`
- THEN the lock file's holder line names that command, the process, the time, the session `s-7` and the task `t1`, and a waiter's description of the holder names both
- AND the file is empty again once the lock is released

### scenario.tracing.lock-handover — A process adopts a lock it was handed

- GIVEN a process holding a lock that starts another with the locked descriptor and names it in `CONCORDE_INHERITED_LOCKS`, then closes its own descriptor
- WHEN the started process takes that lock without waiting
- THEN it holds it at once, writes its own holder line and no longer carries the variable
- AND the lock is released when that process ends

### scenario.tracing.lock-table-holders — The lock table names the holders of the same file only

- GIVEN a lock file and an operating system lock table with `flock` entries on its inode number, one on its device and others on another major or minor device number, and a `flock` entry on another inode of its device
- WHEN an observer reads the holders of that lock file from the table
- THEN it names only the process of the entry whose device and inode both match the file
- AND it names no process of a waiting entry or of a POSIX lock on the file


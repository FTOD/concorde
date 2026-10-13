# Tracing scenarios

These concrete situations show the [requirements](requirements.md) at work. The [contracts](contracts.md)
define these items:

- The record.
- The layout.
- The command.

## Reading

### scenario.tracing.show-task — A task's trace with its cost rolled up

- GIVEN a current task's workspace ran an [Operation](../../glossary.json#concept.operation) with one worker run of two rounds
- AND each round recorded its tokens and cost
- AND the workspace then ran `delivery`
- AND no other node of the task recorded tokens, cost or turns
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `concorde trace show <task>`
- THEN it prints the task's node with its workspace, with the two runs below it
- AND it prints the worker run below the Operation's run
- AND it prints the rounds below the worker run
- AND each node's `rolled_up` sums the tokens of its whole subtree
- AND each node's `rolled_up` sums the cost of its whole subtree
- AND each node's `rolled_up` sums the turns of its whole subtree
- AND the task's `rolled_up` is the sum of the two rounds
- AND each node's own `usage` is as its `trace.json` records it
- BUT nothing is written

### scenario.tracing.show-by-identity — A run is found by its identity

- GIVEN a [workflow step](../../glossary.json#concept.workflow-step) started a run whose folder lies in the step's folder
- AND an [unbound run](../../glossary.json#concept.unbound-run) of the primary worktree exists
- AND a bound run was refused in the lobby before it held its workspace's lock
- WHEN `concorde trace show` is given any of these runs' identities
- THEN it finds and shows that run's node
- AND when the given identity names the unbound run, it shows that run as a node of its own
- AND when the given identity names the run of the lobby, it shows that run as a node of its own
- AND when it finds an identity nowhere, it refuses with `unknown_node`
- AND that refusal names the directories it searched

### scenario.tracing.lost-run — A run whose runner died is lost

- GIVEN a run's `trace.json` says `running`
- AND the run's worker run says `running`
- AND no process holds the run's [run lock](../../glossary.json#concept.run-lock)
- WHEN `concorde trace show` shows it
- THEN the run and its worker run are shown `lost`
- AND the worker run shown by its own identity is shown `lost` too

### scenario.tracing.list — Current tasks, history and unbound runs are listed

- GIVEN two current tasks exist
- AND one closed task exists in the history
- AND one unbound run exists
- WHEN `concorde trace list --history --unbound` runs
- THEN it lists the four nodes with their status
- AND it lists the four nodes with their rolled-up usage
- AND it lists the four nodes without their children

### scenario.tracing.history-reads-alike — A moved task reads the same

- GIVEN a task's folder moved unchanged with its nodes from `tasks/<task>/` to `history/<task>/`
- WHEN `concorde trace show <task>` runs
- THEN it prints the same nodes as before the move
- AND it prints the same statuses as before the move
- AND it prints the same usage as before the move
- AND it prints the new folder as `path`

### scenario.tracing.name-collision — A current task wins over a closed task of its name

- GIVEN a closed task `retry` in the history folder `history/retry/`
- AND a current task, also named `retry`
- WHEN `concorde trace show retry` runs
- THEN it shows the current task
- AND `concorde trace show history/retry` shows the closed task

### scenario.tracing.folder-in-roots — A folder is shown only inside a registered root

- GIVEN a folder `.concorde/elsewhere/n/` of the primary worktree that holds a `trace.json`
- AND a linked worktree whose `.concorde/tasks/t/` holds a task's `trace.json`
- WHEN `concorde trace show` is given each folder by its absolute path
- AND `concorde trace show` is given the first by the path `elsewhere/n`
- THEN it refuses each with `unknown_node`
- AND it shows nothing of either folder

### scenario.tracing.children-any-folder — Children are found whatever their folders are named

- GIVEN a run whose folder holds a node in `reports/1/`
- AND the run's folder holds a node in `.hidden/2/`
- WHEN `concorde trace show` shows the run
- THEN it shows both nodes as the run's children

### scenario.tracing.unreadable-node — A damaged record below is shown, not fatal

- GIVEN a task's trace whose first worker round's `trace.json` is no JSON
- AND the second round's `trace.json` has `schema_version` 2
- WHEN `concorde trace show <task>` runs
- THEN it shows the task's trace
- AND it shows each of the two rounds with status `unreadable` and its folder's name as `id`
- AND each round's `reason` names its `trace.json` and why it cannot be read
- AND the task's `rolled_up` counts no figure of the two rounds
- AND `concorde trace show` given the first round's folder refuses it with `node_unreadable`
- AND that refusal names the file

## Recording

### scenario.tracing.created-or-found — A node tells what it created from what it found

- GIVEN a run created a commit
- AND a later run found that commit at the branch head and reported it instead of creating one
- WHEN each run's node records its references
- THEN the first node references the commit with `commit`
- AND the later node references the same commit with `found_commit`, and not with `commit`
- AND both nodes satisfy the node contract
- AND the node contract refuses a reference of any other relation

### scenario.tracing.kind-registered — A node is checked against the registration of its kind

- GIVEN the node kinds the installed parts registered, such as Check execution's `check` with its content type
- AND that example kind has the metadata `check` and `module`
- WHEN a producer writes a node of a kind no installed part registered
- AND the producer writes a `check` node listing the metadata `workspace`
- AND the producer writes a `check` node whose content is of another type
- THEN each write is refused
- AND the first two writes are refused with `node_invalid`
- AND the last write is refused with `content_invalid`
- AND no `trace.json` is written

### scenario.tracing.kind-registered-written — A node that satisfies its kind's registration is written

- GIVEN Check execution's registered kind `check` with the metadata `check` and `module`
- WHEN a producer writes a `check` node with only that metadata and no content
- THEN its `trace.json` is written
- AND reading it gives the kind `check`

## Removing

### scenario.tracing.prune — Retention removes only what has ended long enough ago

- GIVEN an unbound run ended 8 days ago
- AND another unbound run ended yesterday
- AND another unbound run still runs
- AND a run was refused in the lobby 8 days ago
- AND a history folder closed a year ago
- AND that folder's [task sessions](../../glossary.json#concept.task-session) and worker runs kept their transcripts
- AND another history folder closed two days ago with a transcript
- AND no Tracing configuration exists
- WHEN `concorde trace prune` runs
- THEN it removes the unbound run that ended 8 days ago
- AND it removes the run of the lobby
- AND it removes the conversation records of the folder closed a year ago
- AND it prints each removal
- AND the year-old folder keeps its [decision log](../../glossary.json#concept.decision-log) and [trace nodes](../../glossary.json#concept.trace-node)
- AND the folder closed two days ago keeps its transcript

### scenario.tracing.prune-dry-run — A dry run prints what it would remove

- GIVEN the traces of [scenario.tracing.prune](#scenario.tracing.prune) before any prune
- WHEN `concorde trace prune --dry-run` runs
- THEN it prints the same removals as that scenario's prune
- AND it removes nothing

### scenario.tracing.prune-configured — A configured period replaces its default only

- GIVEN a history folder closed a year ago
- AND an unbound run ended 8 days ago
- AND a Tracing configuration whose `retention` holds only `history_days` 30
- WHEN `concorde trace prune` runs
- THEN it removes the history folder
- AND it removes the unbound run, by the default `unbound_days` of 7
- AND a configuration without `retention` refuses the prune with `config_invalid`

### scenario.tracing.prune-retried — A folder retention could not remove is tried again

- GIVEN an unbound run ended 8 days ago
- AND during the next prune only, the operating system refuses to remove the run's own folder once its content is gone
- WHEN `concorde trace prune` runs
- THEN it prints that folder with the error among the failed paths
- AND the folder keeps its `trace.json`
- AND when `concorde trace prune` runs again, without that refusal, it removes the folder

## Locks

### scenario.tracing.run-lock-lifetime — A run lock exists only while its runner runs

- GIVEN a run started with `--detach`
- WHEN an observer looks while the run runs and again after it ended
- THEN while the run runs, `.concorde/locks/runs/<run>.lock` exists and is held
- AND once the runner exits, the file no longer exists
- AND no lock file lies inside the run's folder

### scenario.tracing.lock-holder-line — The holder line names the session and the task

- GIVEN a process's environment names Claude Code session `s-7`
- WHEN that process takes the [merge lock](../../glossary.json#concept.merge-lock) for `concorde task merge` of task `t1`
- THEN the lock file's holder line names that command
- AND the holder line names the process
- AND the holder line names the time
- AND the holder line names the session `s-7`
- AND the holder line names the task `t1`
- AND a waiter's description of the holder names both the session and the task
- AND once the lock is released, the file is empty again

### scenario.tracing.lock-handover — A process adopts a lock it was handed

- GIVEN a process holds a lock
- AND that process starts another with the locked descriptor and names it in `CONCORDE_INHERITED_LOCKS`
- AND the first process then closes its own descriptor
- WHEN the started process takes that lock without waiting
- THEN it holds the lock at once
- AND it writes its own holder line
- AND it no longer carries the variable
- AND when that process ends, the lock is released

### scenario.tracing.lock-table-holders — The lock table names the holders of the same file only

- GIVEN a lock file exists
- AND an operating system lock table has `flock` entries on the file's inode number
- AND one of those entries is on the file's device
- AND the other entries are on another major or minor device number
- AND the table has a `flock` entry on another inode of the file's device
- WHEN an observer reads the holders of that lock file from the table
- THEN it names only the process of the entry whose device and inode both match the file
- AND it names no process of a waiting entry or of a POSIX lock on the file


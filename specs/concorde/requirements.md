# Framework requirements

These requirements hold for the Framework as a whole. Each Module states the precise behaviour it
contributes; a requirement here promises what the Modules achieve together.

## Runtime

### req.concorde.claude-code-only — Claude Code is the only agent runtime

The Framework SHALL run its main-agent guidance and every worker on Claude Code only in this version.

Pi and pi-subagents are not supported. A future version may add them without changing the Spec
Protocol, because the Protocol defines visibility, not how an agent is run.

## Boundaries

### req.concorde.grant-from-task-worktree — Grants come from the task's own Specs

Every grant a worker receives SHALL be computed from the Specs in the worktree of the task it works on.

### req.concorde.no-wider-than-type — A worker never exceeds its task type

A worker's readable and writable paths SHALL NOT exceed what its task type assigns to its bound Modules.

### req.concorde.workers-no-git — Workers have no Git access

A worker SHALL NOT be able to read or change Git metadata; diffs, commits and merges belong to the host and the main agent.

## Results and problems

### req.concorde.escalation-evidence — A problem travels up with its evidence

Every Operation result that is not successful SHALL carry the problem, the evidence the host produced and the worker's own report kept apart.

### req.concorde.spec-gaps-stop — Automatic rounds never repair Specs

An Operation SHALL stop and return an escalation instead of resuming a worker when the failure is a Spec gap, a needed path outside the grant, or a failed structural Spec check.

Only failures of configured checks against code are fed back to the same worker automatically.

## Change control

### req.concorde.delivery-separate — Delivery is its own Operation

Changes of a task SHALL reach the task branch only through the `delivery` Operation, which commits them together with their evidence.

### req.concorde.merge-by-main-agent — The main agent merges delivered tasks

The main agent SHALL be able to merge a delivered task branch into the primary branch without asking the developer for authorization.

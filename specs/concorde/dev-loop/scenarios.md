# Development Graph scenarios

These precise specifications belong directly to the [Development Graph Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Acceptance task](../planning/tasks.md#terminology) | Defined in Making work verifiable. |

## Development Graph

### scenario.development.resume-unbound — Resume a candidate before target selection

- GIVEN the host created a candidate whose change was recorded before routing or binding an owner
- WHEN a fresh host in that worktree resumes the development loop with the recorded change identity and original task
- THEN it validates the worktree identity and preserved intent, restores omitted constraints and focus hints, and performs real router discovery and single-target selection before binding the owner
- AND a supplied target hint never substitutes for routing authority
- AND both specify modes and both review modes use this same admission, with one successful route selection before the first development stage

### scenario.development.resume-bound — Restore a bound candidate without rerouting

- GIVEN a candidate has a persisted owner, task, constraints and focus
- WHEN a fresh host resumes that change
- THEN it restores omitted target, constraints and focus from the recorded owner and resolves the current complete Module contract without rerouting
- AND explicit conflicting target, task, constraints or focus returns incompatible_handoff with the conflicting field before any Agent runs, preserving the candidate state
- AND a missing change returns missing_change, an inconsistent owner returns invalid_worktree_state, and a mismatched change or worktree identity is refused before routing or execution
- AND trusted internal routes may select separately admitted components without replacing the top-level owner, while a child target differing from its host route is rejected
- AND existing stage admission, review requirements, file permissions and current-candidate freshness checks still apply

### scenario.development.dev-loop-ready — A change reaches a ready candidate

- GIVEN a developer supplies one intended change with its task and constraints
- WHEN `concorde-dev-loop` calls `concorde-specify-loop` for Spec authoring (unless `specify=false`) and Spec review, then runs planning, tasks, implementation, deterministic checks and code review in order
- THEN every stage completes successfully and the candidate reaches status `ready` with current evidence for every affected Module
- AND the loop stops there and never itself invokes delivery

### scenario.development.dev-loop-spec-gap — Development waits for a necessary Spec repair

- GIVEN a stage discovers a necessary missing or ambiguous contract
- WHEN that stage reports a Spec gap
- THEN the loop stops with status `waiting` and preserves the candidate worktree
- AND unrelated independent work may continue, and resuming after an explicit Spec repair does not repeat already-accepted authoring for the same task, focus and constraints

### scenario.development.task-scope-repair — Recover an implementation phase boundary error

- GIVEN an existing incomplete task list whose acceptance requires later Host actions
- WHEN a normal dev-loop request binds that list's canonical digest with repair_task_scope
- THEN a fresh task author receives the admitted plan, prior tasks and typed semantic boundary feedback
- AND no implementation contents or raw test logs enter that author's context
- AND accepted replacement tasks start incomplete, preserve software acceptance and use new IDs
- AND the original list remains in history and implementation precedes validation and required code review
- AND only current successful evidence reaches ready, while a replay resumes without reauthoring
- AND stale digests, unresolved gaps and invalid replacements cannot bypass the existing gates

### scenario.development.dev-loop-repair — Bounded automatic repair after blocking code review

- GIVEN a code-owning target's code review returns blocking findings
- WHEN the loop selects its automatic revision edge from code review back to task authoring
- THEN task authoring receives the current completed tasks and the blocking `concorde-review-result@2` as `stage_inputs`, and the resulting repair tasks and their implementation are checked and code-reviewed again like any other change
- AND this repair is bounded by the target's declared `max_repair_iterations` policy

See [code-review repair is the only automatic edge](requirements.md#req.development.repair-edge-only) and
[other outcomes stop the graph for a decision](requirements.md#req.development.non-repair-stops-graph).

### scenario.development.dev-loop-repair-exhausted — Repeated feedback or an exhausted limit stops the loop

- GIVEN a repair attempt reproduces the same blocking-feedback fingerprint as the previous attempt, or the declared repair limit is exhausted
- WHEN the loop would otherwise select another automatic repair
- THEN it stops instead of retrying: unchanged feedback records status `waiting` and an exhausted limit records status `limit_exhausted`, and both keep the wire `outcome` `conflicting`
- AND a human directly changing the Spec or the implementation between invocations resets the recorded repair count instead of continuing a stale attempt

### scenario.development.dev-loop-coordinated — A Module coordinates its own and dependency tasks

- GIVEN a Module task has both local code tasks and separately bound submodule or used-Module tasks
- WHEN implementation runs
- THEN each component is specified, planned and implemented from its own complete Module contract and the files its own entries bind, and the coordinator waits for every writer, including its own coordination code, before checking the final candidate
- AND a repair that changes a file listed by several Modules invalidates the already-recorded evidence of every listing Module, and finalization repeats until every participant is stable

The detailed contract is [Ready-only bounded development](execution-reference.md#development-development-graph-and-revision-loops).

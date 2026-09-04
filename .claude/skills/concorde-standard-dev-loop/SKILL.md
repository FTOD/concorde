---
name: concorde-standard-dev-loop
description: "Run the standard Concorde development loop as a controlled LangGraph Operation."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "operations/concorde-standard-dev-loop/SKILL.md"
  kind: "operation"
  exposure: "public"
  entrypoint: "operations/concorde-standard-dev-loop/operation.py"
user-invocable: true
disable-model-invocation: false
---
# Concorde Standard Development Loop

## Isolated worktree gate

After applying any Protocol-evolution guard, read-only inspection may remain in the primary
worktree. Before planning, selection persistence, attempt/checklist/reflection creation, an external
mutation, or any other write, unless the maintainer explicitly authorizes primary-worktree mutation
for this request, resolve only the primary worktree's committed `HEAD`, create a unique branch and
linked worktree at that exact commit, and continue the complete request there. If already in an
isolated worktree, stay there and do not create a nested worktree. Treat every staged, unstaged,
untracked, or ignored primary-worktree path as another programmer's state: never use it as input,
stash it, copy it, commit it, reset it, clean it, or otherwise import or alter it. If required input
is absent from committed `HEAD`, stop and report the missing input. `--allow-primary-worktree` is
valid only after an explicit instruction to modify the primary worktree; a generic task request is
not that authorization. A non-Git checkout likewise requires explicit current-directory mutation
authorization.

## Concorde Protocol evolution guard

Before graph construction, workspace resolution, or any direct/nested capability invocation, if this
is the Concorde repository and the request changes normative Concorde Protocol semantics, stop with
no completed prefix and no selection/attempt mutation. Report `feature.concorde.evolve-protocol` and
its direct isolated-worktree cutover. A change that only restores already specified Protocol behavior
remains normal standard-loop work.

Treat `$ARGUMENTS` as the complete development request. Use the paired graph at `python3 scripts/run-operation.py operations/concorde-standard-dev-loop/operation.py` as the
topology authority for exactly four stages: specify, plan, tasks, and deliver.

Before executing leaf Skills, run:

```bash
python3 scripts/run-operation.py operations/concorde-standard-dev-loop/operation.py "$ARGUMENTS" --framework-prefix .
```

Require the graph to report these ordered direct capability bundles:

1. `specify`: `concorde-specify`
2. `plan`: public nested Operation `concorde-plan` (never its internal leaves)
3. `tasks`: `concorde-tasks`, then `concorde-implement`
4. `deliver`: `concorde-validate`, then `concorde-deliver`

Execute each named direct capability faithfully in graph order, carrying forward every explicit
per-capability result. The outer host dispatches `concorde-plan` only through its public pair and sees
one opaque nested result; the inner planner alone resolves context/author leaves and their policies.
Every direct leaf receives its own immutable launch specification—never a stage-wide permission
union. Stop immediately when any leaf or nested Operation fails, blocks, or requests missing
authority. Never treat deterministic recording output as evidence that agent work completed.

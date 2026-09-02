---
description: "Execute every task in one selected Concorde attempt."
scripts:
  py: .specify/extensions/concorde/scripts/python/workspace.py --phase implement
---

## User Input

```text
$ARGUMENTS
```

# Implement a Concorde Attempt

Execute the selected attempt against the direct feature file, providing module architecture, current
source code, and tests. Code is implementation authority; tests and deterministic checks are
evidence. Delivery is a later cleanup-only operation.

## Workspace gate

Before hooks, setup inspection, or reads, run `{SCRIPT}`. Require Protocol 12 with a canonical
selected feature and an active attempt. Use only the returned durable, temporal, process, and
executable paths. Never resolve another attempt or infer a compatibility root. Bounded ancestry and
related-feature summaries are navigation; open another feature file only when an executable task names it.

Scan every file in the returned `checklists_dir`. Report total/checked/unchecked. If any item is
unchecked, stop and ask whether to proceed; checklist state is reviewer-owned and must not be edited
to make implementation eligible.

Process enabled unconditional `before_implement` hooks. Run mandatory hooks and stop on failure;
present optional hooks; leave conditional hooks to the hook executor.

## Context and protected baseline

Read the complete selected feature file, providing module architecture, plan, tasks, validation, research,
data model, quickstart, constitution, and source/tests named by executable context. Read an explicitly
tasked related feature file or ancestor architecture section only as needed and cite why.

At start, record SHA-256 evidence for the selected feature file, providing architecture, bounded ancestry
references, canonical related-feature-summary JSON, and task-declared durable related feature files. These
are not immutable when an explicit task owns their reconciliation; every before/after change must
match an executable task and its trace. An unexpected change stops completion marking.

## Execution

1. Parse phases, task IDs, dependencies, `[P]` markers, trace tokens, paths, and verification checks.
2. Execute phase by phase. Run tests before implementation. Sequential tasks stay ordered; parallel
   tasks may run concurrently only when file ownership and dependencies remain disjoint.
3. Inspect setup/ignore files read-only unless a dependency-ready task names the trace, detected
   tool, exact setup path, and authorized creation/edit.
4. Implement the complete task delta. A task may reconcile:

   - module `architecture.md` entity/type/locator, relationship, interaction, inventory, or textual
     diagram counterpart;
   - selected or explicitly named related feature-file outcome, usage, embedded interface,
     failures, requirements, or Architecture Zoom;
   - source code and executable tests/fixtures; and
   - generated projections, packages, and public documentation.

   Do not make an unplanned durable edit. Never create a nested feature, standalone interface spec,
   diagram source beside a feature file, or prose implementation summary.
5. For architecture-owned diagrams, update source and textual architecture together; keep
   `meta.legend.mode: hidden`, validate normalized unique output resolution, run deterministic delivery/freshness, and
   truthfully record whether visual inspection occurred. Generated output is never authority.
6. Before checking any task, append compact Attempt Evidence to the returned validation log: task ID
   and trace, actual command/check, `passed`/`failed`/truthful `skipped`, evidence path, scope, and
   limitation. Only a proportionate passed check permits `[X]`.
7. If a sequential task fails, record the problem then stop. For independent parallel failures,
   continue only the unaffected tasks and leave failed tasks open.

## Reflection recording

Record every difficulty encountered, including one solved by a workaround and every provisional
prototype design choice. Before appending a new entry to `workspace.reflections`, run the installed
`.specify/extensions/concorde/scripts/python/reflections_queue.py --allocate-id`, use only its
`allocated_id`, and never derive an ID from the remaining log entries. Append with fixed grammar,
`Phase: implement`, and `Status: open`, or add an occurrence to the same existing problem without
allocating a new ID. Name the concerned design, architecture, interface ID, guidance, tool, or code path. Keep
Expected/Observed/Action concise. Never copy reflection identity or prose into code, tests, durable
sources, diagrams, or attempt evidence.

## Completion validation

After all tasks:

- rerun the focused and integration checks named by the plan;
- validate module/entity/relationship/interaction and feature/interface/zoom consistency;
- verify source/test fixture and generated projection freshness;
- record before/after digests and prove every durable change was task-authorized;
- prove every task and checklist is complete with passed evidence; and
- confirm the selected attempt still exists for explicit delivery.

Process enabled unconditional `after_implement` hooks before reporting. Run mandatory hooks, present
optional hooks, and leave conditional hooks to the executor.

Report completed/open tasks, changed architecture/feature/code/test/projection paths, commands and
results, limitations, and `Reflections added: <ids or none> · open for this feature: <count>`.

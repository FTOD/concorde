---
name: concorde-converge
description: "Append remaining verified work to one active Concorde task list."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "commands/concorde.converge.md"
---
# Concorde Converge

## User Input

```text
$ARGUMENTS
```

# Converge a Concorde Attempt

Convergence compares the current repository state and evidence with the selected feature file,
architecture, and plan, then appends only genuinely remaining executable work. It does not implement
the work or rewrite completed history.

## Workspace gate

Run `python3 scripts/workspace.py --phase converge` first and require Protocol 12 plus an active attempt. Use only returned feature file,
architecture, bounded context, executable context, plan, tasks, validation, checklist, and reflection
paths. Never inspect another attempt.

Read current code/tests and generated state named by tasks. Preserve every existing task ID, text,
marker, phase, and evidence entry. Do not mark tasks complete or reopen them.

## Reconciliation

1. Determine which design requirements, embedded interface obligations, architecture entity/
   relationship/interaction changes, source/test changes, projections, and validation outcomes remain
   unproven.
2. Trust a completed task only as historical state; use its recorded passed evidence and current
   repository checks when deciding whether follow-up is needed.
3. Append dependency-ordered tasks with new monotonically increasing IDs. Each task names exact
   paths, requirement/acceptance trace, dependencies, and a proportionate verification check.
4. Include explicit architecture/feature-file reconciliation when current code or tests changed the entity
   graph, interface, behavior, failures, or Architecture Zoom. Do not create alternate source forms.
5. Add final integration or cleanup-readiness tasks when checklists, evidence, package freshness,
   architecture diagram freshness, or proposal digest coverage is incomplete.
6. If no work remains, leave the task file byte-identical and report convergence.

Record contradictions, workarounds, or provisional decisions encountered in
`workspace.reflections` with `Phase: converge`. Before appending a new entry, run the installed
`python3 ./scripts/reflections_queue.py --allocate-id`, use only its
`allocated_id`, and never derive an ID from the remaining log entries; update an existing occurrence
without allocating a new ID.
Convergence may write only the selected task list, its compact reconciliation evidence when a check
was actually run, and the centralized reflection log.

Report appended task IDs and reasons, dependency placement, checks run, remaining risks, or that no
new tasks were necessary.

---
name: concorde-converge
description: "Append remaining verified work to one active Concorde task list."
argument-hint: "Optional capability guidance"
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-converge/SKILL.md"
  kind: "skill"
  exposure: "public"
user-invocable: true
disable-model-invocation: false
---
## User Input

```text
$ARGUMENTS
```

# Converge a Concorde Attempt

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

Convergence compares the current repository state and evidence with the selected feature file,
architecture, and plan, then appends only genuinely remaining executable work. It does not implement
the work or rewrite completed history.

## Concorde Protocol evolution guard

Before workspace resolution or task mutation, if this is the Concorde repository and the remaining
work changes normative Concorde Protocol semantics, stop without appending tasks or reflections.
Report `feature.concorde.evolve-protocol`; Protocol evolution has no attempt to converge.

## Workspace gate

Run `python3 scripts/workspace.py --phase converge` first and require Protocol 13 plus an active attempt. Use only returned feature file,
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

Planning and task generation are the normal reflection-recording points. If convergence encounters a
distinct problem that must persist, record it under `workspace.reflections` with `phase: converge`
using Reflection Document v2: allocate the ID, fill only the factual problem sections, leave triage
sections blank, omit `human_intervention`, and retain `User Comments`. Do not propose a resolution or
make the intervention decision. Update an existing occurrence without allocating a new ID.
Immediately after creating the document or appending an occurrence, run
`scripts/reflections_queue.py --validate-entry <id>`; correct only that new entry until it reports
`valid`. Findings on other entries are reported separately as unrelated and are not this phase's to
fix; a reserved ID stays retired even if the entry is abandoned.
Convergence may write only the selected task list, its compact reconciliation evidence when a check
was actually run, and authorized per-file reflection state.

Any reconciliation evidence it writes must use the same delivery-readable validation grammar:

```markdown
- **T### · <trace>**
  - **Outcome**: passed|failed|skipped
  - **Check**: <actual command or check>
  - **Evidence**: <project-relative path or concise output>
  - **Scope**: <behavior or boundary proved>
  - **Limitation**: <material limit or none>
```

Keep the `- **T### · <trace>**` boundary on one complete top-level line with no trailing prose, and
put the exact `**Outcome**` field inside that block. Do not treat “passed” in a title or narrative as
task evidence, duplicate a task's current block, or alter an existing outcome merely to make
delivery eligible.

Report appended task IDs and reasons, dependency placement, checks run, remaining risks, or that no
new tasks were necessary.

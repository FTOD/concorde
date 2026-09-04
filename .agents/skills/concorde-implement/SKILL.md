---
name: concorde-implement
description: "Execute every task in one selected Concorde attempt."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-implement/SKILL.md"
  kind: "skill"
  exposure: "public"
---
## User Input

```text
$ARGUMENTS
```

# Implement a Concorde Attempt

Execute the selected attempt against the direct feature file, providing module architecture, current
source code, and tests. Code is implementation authority; tests and deterministic checks are
evidence. Delivery is a later cleanup-only Tool.

## Concorde Protocol evolution guard

Before workspace resolution, setup inspection, or any write, if this is the Concorde repository and
the requested implementation changes normative Concorde Protocol semantics, stop without opening or
updating an attempt. Report `feature.concorde.evolve-protocol`; the change must be authored directly
in its isolated worktree and validated as one cutover commit. A fix that restores already specified
Protocol behavior remains eligible for normal implementation.

## Workspace gate

Before setup inspection or reads, run `python3 scripts/workspace.py --phase implement`. Require Protocol 13 with a canonical
selected feature and an active attempt. Use only the returned durable, temporal, process, and
executable paths. Never resolve another attempt or infer a compatibility root. Bounded ancestry and
related-feature summaries are navigation; open another feature file only when an executable task names it.

Scan every file in the returned `checklists_dir`. Report total/checked/unchecked. If any item is
unchecked, stop and ask whether to proceed; checklist state is reviewer-owned and must not be edited
to make implementation eligible.

Concorde has no extension-hook phase. The selected attempt, checklist state, and task dependencies
are the complete pre-execution gate.

## Context and protected baseline

Read the complete selected feature file, providing module architecture, plan, tasks, validation, research,
data model, quickstart, `.concorde/constitution.md` when present, and source/tests named by executable context. Read an explicitly
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
5. Every affected module must retain one Archify `architecture` system overview of its principal
   entities and directed relationships. When its entity graph changes, update that overview and the
   textual architecture together. For every created or changed architecture diagram keep
   `meta.quality_profile: showcase` and `meta.legend.mode: hidden`, validate normalized unique output
   resolution, require all nine Archify showcase checks with zero composition errors/warnings, run
   deterministic delivery/freshness, and truthfully record whether visual inspection occurred. A
   basic four-check receipt is not acceptance. Generated output is never authority.
6. Before checking any task, append compact Attempt Evidence to the returned validation log using
   this exact delivery-readable shape. The task ID and trace belong in its boundary; the actual
   command/check, evidence path, scope, and limitation belong inside the block:

   ```markdown
   - **T### · <trace>**
     - **Outcome**: passed|failed|skipped
     - **Check**: <actual command or check>
     - **Evidence**: <project-relative path or concise output>
     - **Scope**: <behavior or boundary proved>
     - **Limitation**: <material limit or none>
   ```

   The `- **T### · <trace>**` boundary is one complete top-level line with no trailing prose and may
   not wrap or be nested. `**Outcome**` is a separate nested field inside that task's block; writing
   “passed” only in the boundary or surrounding prose is not evidence. Use the exact task ID, keep
   one current block per task, and record `passed`/`failed`/truthful `skipped` as applicable. Only a
   proportionate passed check permits `[X]`; concretely, its field must say `**Outcome**: passed`.
7. If a sequential task fails, record the problem then stop. For independent parallel failures,
   continue only the unaffected tasks and leave failed tasks open.

## Reflection recording

Planning and task generation are the normal reflection-recording points. Prefer compact attempt
evidence for an implementation failure. If implementation encounters a distinct problem that must
persist beyond the attempt, inspect the collection for a match, then either add an occurrence or
allocate and create one Reflection Document v2 with `phase: implement`, `status: open`, and `triage:
pending`. Fill only Context, Expected, Observed, Impact, and Evidence. Leave the triage-owned sections
blank, omit `human_intervention`, retain `User Comments`, and do not analyze root cause or propose a
resolution. Never copy reflection identity or prose into code, tests, durable sources, diagrams, or
attempt evidence. Immediately after creating the document or appending an occurrence, run
`scripts/reflections_queue.py --validate-entry <id>`; correct only that new entry until it reports
`valid`. Findings on other entries are reported separately as unrelated and are not this phase's to
fix; a reserved ID stays retired even if the entry is abandoned.

## Completion validation

After all tasks:

- rerun the focused and integration checks named by the plan;
- validate module/entity/relationship/interaction and feature/interface/zoom consistency;
- verify source/test fixture and generated projection freshness;
- record before/after digests and prove every durable change was task-authorized;
- prove every task and checklist is complete with passed evidence; and
- confirm the selected attempt still exists for explicit delivery.

Run the declared validation and reconciliation checks before reporting; there is no
post-implementation extension-hook layer.

Report completed/open tasks, changed architecture/feature/code/test/projection paths, checks and
results, limitations, and `Reflections added: <ids or none> · open for this feature: <count>`.

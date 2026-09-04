---
name: concorde-analyze
description: "Analyze one direct feature file, architecture context, and temporal attempt without mutation."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-analyze/SKILL.md"
  kind: "skill"
  exposure: "public"
---
## User Input

```text
$ARGUMENTS
```

# Analyze Concorde Alignment

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

This is a read-only semantic audit. It reports inconsistencies and coverage gaps across the selected
feature file, providing module architecture, attempt plan/tasks/evidence, `.concorde/constitution.md` when present, and named
code/test surfaces. It never fixes them.

## Workspace gate and scope

Run `python3 scripts/workspace.py --phase analyze` first and require Protocol 13. Use only returned paths. Read the selected feature file,
providing architecture, plan/tasks/research/validation when present, optional `.concorde/constitution.md`, checklist state,
and source/test paths needed to verify task coverage. Related-feature summaries and module ancestry
remain bounded navigation; open another feature file only for a named interface dependency, never another
attempt.

Build internal inventories of requirements, success criteria, interfaces, architecture entities and
interactions, planned decisions, executable tasks, evidence, and affected paths. Do not echo full
documents in the report.

## Checks

Report findings for:

- duplication, ambiguity, underspecification, conflicting terminology, or unmeasurable criteria;
- unresolved or redefined architecture entity IDs/types/locators/ownership;
- a providing or affected module whose responsibility is an artifact type or residual bucket
  rather than a capability, features that are inventories rather than use cases, or a feature placed
  by artifact kind instead of by the capability it serves (constitution A.VI);
- unresolved relationship endpoints or interaction/interface governance;
- incomplete interface consumer/direction, entry point, input/output, obligations, failures,
  compatibility, example, or implementing-entity semantics;
- Architecture Zoom references that do not resolve in module visibility;
- requirements or interfaces without tasks/tests and tasks without design/plan traces;
- missing module architecture or feature-file reconciliation tasks;
- task dependency/order/path ambiguity, unsafe setup mutation, or missing evidence checks;
- generated projection or architecture-diagram source/text/freshness gaps; and
- delivery readiness gaps, including incomplete checklist/task/evidence or an unsafe removal target.

Use stable finding IDs by category and severity: CRITICAL for constitutional or unsafe conflicts,
HIGH for blocking requirement/interface/entity/task gaps, MEDIUM for ambiguity or incomplete
coverage, and LOW for wording/redundancy. Provide a concrete location and recommendation for each.

## Concept and data-flow review

Prioritize missing project concepts and undefined transfers before layout/style findings. For each
significant entity verify identity, owner, cardinality, lifetime, and source of truth; distinguish
Operation definitions, invocations, and stored artifacts. For each cross-boundary transfer trace
producer output fields to a consumer's named input type/version and governing interface. Separate
initialized configuration, runtime input, and host-derived context. Flag opaque context blobs,
free-form prior-result assumptions, missing field/null/default rules, and unspecified stale/failure
handling. Walk one success and one rejected handoff. Compare the target contract with actual code;
a diagram or structural validator pass does not prove runtime support. Keep the review read-only.

## Mutation boundary and reflections

Do not edit design, architecture, attempt artifacts, code, tests, control state, or generated output.
Prefer an ordinary report finding; planning and task generation are the normal reflection-recording
points. If the analysis itself encounters a distinct guidance/tooling/source problem that must
persist, follow the Reflection Document v2 template with `phase: analyze`: allocate the ID, create
exactly the returned per-file path, and fill only the factual problem sections. Leave all triage
sections blank, omit `human_intervention`, preserve `User Comments`, and do not recommend a change.
Update an existing occurrence without allocating a new ID, and never duplicate the reflection.
Immediately after creating the document or appending an occurrence, run
`scripts/reflections_queue.py --validate-entry <id>`; correct only that new entry until it reports
`valid`. Findings on other entries are reported separately as unrelated and are not this phase's to
fix; a reserved ID stays retired even if the entry is abandoned.

Report a compact summary table, requirement-to-task/test coverage metrics, architecture/interface
coverage, delivery readiness, and the top recommended next actions. State clearly that analysis did
not apply changes.

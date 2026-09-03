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

---
name: concorde-plan
description: "Plan one Concorde feature change against architecture, code, and tests."
compatibility: "Requires a Concorde project"
metadata:
  author: "concorde"
  source: "skills/concorde-plan/SKILL.md"
  kind: "skill"
---
## User Input

```text
$ARGUMENTS
```

# Plan a Concorde Feature Change

Planning converts the selected feature file into a technical delta against the providing module
architecture, current source code, and executable evidence. All planning outputs are temporal.

## Workspace gate

Before setup checks, template reading, or artifact reads, run `python3 scripts/workspace.py --phase plan`. Require Protocol 13
with `resolved` or `selected` status. Use the returned paths as the only authority:

- `feature_path` and `module_architecture`;
- bounded `module_ancestry` and `related_features` summaries;
- `attempt_dir`, `attempt_state`, `plan`, `tasks`, `checklists_dir`, `research`, `data_model`,
  `quickstart`, and `validation`;
- `reflections` and its open count; and
- `executable_context` source/test roots or inventory hints.

Do not resolve a root-level compatibility plan. Do not implicitly load another feature body or any
other attempt. If the returned attempt is absent, create exactly that directory and seed its plan by
reading `./templates/plan-template.md` as the temporal format reference.

## Inputs and authority

Read `.concorde/constitution.md` when present, the complete selected feature file, providing module architecture, current
source code and executable tests named by executable context, and existing attempt planning artifacts.
There is no prose implementation baseline. Open a related
feature file only for an explicitly relevant interface dependency and cite why. Generated pages
and diagrams are evidence/projections, not behavior or structure authority.

Hash the selected feature file, providing architecture, bounded ancestry references, and canonical
related-feature-summary JSON at plan start and completion. Record comparisons in the attempt
validation log. Planning writes only temporal attempt artifacts. Planning must leave durable sources
byte-identical.

## Planning workflow

1. Resolve Technical Context. Mark unknowns, research them, and write decisions plus alternatives to
   returned `research` path. Record provisional or imperfect prototype choices in the project reflection
   log rather than stopping when a safe bounded assumption allows progress.
2. Execute the Constitution Check before research and after the technical design. Explain any justified exception.
3. Build the Concorde Architecture Gate:

   - resolve every feature interface and Architecture Zoom entity;
   - identify affected architecture entities, directed relationships, interactions, modules, feature
     files, code paths, tests, external systems, and projections;
   - state whether each durable source needs an explicit implementation task;
   - compare desired behavior directly with code/tests; and
   - name bounded related features whose interfaces must be reconciled.

   Require every affected module to retain one Archify `architecture` system overview that depicts
   its principal entities and directed relationships. Any entity, relationship, boundary, or module
   inventory delta must state whether and how that overview changes.

4. Generate only useful Phase 1 artifacts: data model, research, and runnable quickstart. Readable
   interface promises remain embedded in feature files. Executed schemas/examples go under source
   or test fixture paths through later tasks.
5. The module system overview is mandatory; plan other architecture-owned diagrams only when a
   dynamic interaction or secondary structure materially benefits from another view. Keep source in
   the owning module's `diagrams/`, textual explanation in
   `architecture.md`; require `meta.legend.mode` to be `hidden`. Before planning diagram work, verify each
   declaration's output is a normalized project-relative `.html` path under `generated/`, its
   source-relative `meta.output` resolves to that same unique target, and no declaration duplicates
   the target. Require `meta.quality_profile: showcase`, run Archify showcase validation for every
   created or changed diagram, and reject a basic four-check receipt. Invalid declarations must return
   to architecture authority before planning proceeds.
6. Define test-first phases and exact source structure. Include deterministic validation, package or
   doc projection freshness, and cleanup-only delivery readiness proportional to scope.
7. Keep ignore/tool setup inspection read-only unless one dependency-ready task explicitly names a
   trace token, detected tool, exact setup file, and authorized edit.

## Reflection recording

Whenever planning must assume, work around, defer, or stop because feature intent, architecture, related
interfaces, code/tests, guidance, or tooling disagree, append or update the project-wide reflection
log at `workspace.reflections`. Before appending a new entry, run the installed
`python3 ./scripts/reflections_queue.py --allocate-id`, use only its
`allocated_id`, and never derive an ID from the remaining log entries. Use fixed field grammar,
`Phase: plan`, and `Status: open`; an existing problem receives an occurrence without allocating a
new ID. This includes design
choices that are knowingly provisional for the prototype. Never copy reflection identity or prose
into attempt or durable artifacts. Continue with a bounded prototype whenever a safe explicit
assumption permits useful progress.

## Completion gate

Verify that planning wrote only returned attempt paths plus any required reflection occurrence; all
unknowns are resolved or explicit bounded assumptions; every affected durable/interface/code/test
surface has a task-ready path; diagram checks passed; and protected hashes show no unexpected change.

Report the feature ID, module architecture, plan path, generated artifacts,
architecture/interface delta, code/test baseline examined, and reflections added.

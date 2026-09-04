---
name: concorde-plan-author
description: "Author one temporal Concorde plan from a verified bounded context receipt."
exposure: internal
effects:
  reads:
    - selected-feature
    - module-architecture
    - module-ancestry
    - related-summaries
    - required-feature-specs
    - owned-implementation
    - attempt
    - checklists
    - constitution
    - reflections
    - framework
    - templates
  writes:
    - attempt
    - reflections
  network: false
  credentials: none
---

## User Input

```text
$ARGUMENTS
```

# Plan a Concorde Feature Change

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

Planning converts the selected feature file into a technical delta against the providing module
architecture, current source code, and executable evidence. All planning outputs are temporal.

## Bounded context gate

Require the immediately prior `concorde-plan-context` result. It must identify the selected feature,
providing architecture, exact required-interface provider feature bodies, owned implementation/test
locators, attempt/control paths, deny categories, and workspace digest. Use only the paths in that
receipt and the immutable launch policy; do not rerun workspace resolution, infer another root,
open another attempt, or broaden a related-feature summary into body access.

If the returned attempt is absent, create exactly that authorized directory and seed its plan by
reading the authorized framework `templates/plan-template.md`. A missing, stale, unsafe, ambiguous,
or policy-mismatched context stops authorship before any write.

## Inputs and authority

Read `.concorde/constitution.md` when admitted, the complete selected feature file, providing module
architecture, current source code and executable tests in the owned locators, the exact admitted
provider feature specifications, and existing selected-attempt planning artifacts. There is no prose
implementation baseline. Generated pages and diagrams are evidence/projections, not behavior or
structure authority.

Hash the selected feature file, providing architecture, bounded ancestry references, and canonical
related-feature-summary JSON at plan start and completion. Record comparisons in the attempt
validation log. Planning writes only temporal attempt artifacts plus authorized per-file reflection
state. Planning must leave durable sources byte-identical.

## Planning workflow

1. Resolve Technical Context. Mark unknowns, research them, and write decisions plus alternatives to
   the returned `research` path. Record a concrete contradiction, missing authority, or failed tool
   as a reflection when a safe bounded assumption still allows progress.
2. Execute the Constitution Check before research and after the technical design. Explain any
   justified exception.
3. Build the Concorde Architecture Gate:

   - resolve every feature interface and Architecture Zoom entity;
   - identify affected architecture entities, directed relationships, interactions, modules,
     feature files, code paths, tests, external systems, and projections;
   - state whether each durable source needs an explicit implementation task;
   - compare desired behavior directly with admitted code/tests; and
   - name bounded related features whose interfaces must be reconciled.

   Require every affected module to retain one Archify `architecture` system overview that depicts
   its principal entities and directed relationships. Any entity, relationship, boundary, or module
   inventory delta must state whether and how that overview changes. When the plan creates,
   splits, merges, or renames a module, state the capability, use case, or axis of change that
   bounds it (constitution A.VI); reject a plan that introduces an artifact-type layer or a residual
   bucket, and place each new entity in the module whose use case it realizes rather than beside
   artifacts of the same kind.

4. Generate only useful Phase 1 artifacts: data model, research, and runnable quickstart. Readable
   interface promises remain embedded in feature files. Executed schemas/examples go under source
   or test fixture paths through later tasks.
5. The module system overview is mandatory; plan other architecture-owned diagrams only when a
   dynamic interaction or secondary structure materially benefits from another view. Keep source in
   the owning module's `diagrams/`, textual explanation in `architecture.md`; require
   `meta.legend.mode` to be `hidden`. Before planning diagram work, verify each declaration's output
   is a normalized project-relative `.html` path under `generated/`, its source-relative
   `meta.output` resolves to that same unique target, and no declaration duplicates the target.
   Require `meta.quality_profile: showcase`, run Archify showcase validation for every created or
   changed diagram, and reject a basic four-check receipt. Invalid declarations must return to
   architecture authority before planning proceeds.
6. Define test-first phases and exact source structure. Include deterministic validation, package or
   doc projection freshness, and cleanup-only delivery readiness proportional to scope.
7. Keep ignore/tool setup inspection read-only unless one dependency-ready task explicitly names a
   trace token, detected tool, exact setup file, and authorized edit.

## Reflection recording

Planning and task generation are the normal points at which reflections are created. Create one only
when planning encounters a concrete contradiction, ambiguity, missing authority, tooling failure, or
other problem worth later investigation. First inspect the per-file collection under the returned
`reflections` directory so the same problem receives an `Occurrences` item instead of another ID.

For a new problem, run the installed `scripts/reflections_queue.py --allocate-id`, use only its
`allocated_id`, never derive an ID from existing files, and create exactly the returned
`reflection_path` (always under `.concorde/reflections/pending/`) from
`templates/reflections-template.md`. Use `phase: plan`, `status: open`, and `triage: pending`. Fill Context, Expected, Observed, Impact, and Evidence with enough
specific detail for a later investigator. Describe only the problem and its effect on this planning
pass: do not analyze root cause, propose a resolution, or decide whether human intervention is
needed. Omit `human_intervention` and leave the three triage-owned sections blank. Always retain the
blank `User Comments` section. Only `concorde-reflections-triage` may complete those details and make
the intervention decision. Never copy reflection identity or prose into attempt or durable artifacts.
Immediately after creating the document or appending an occurrence, run
`scripts/reflections_queue.py --validate-entry <id>`; correct only that new entry until it reports
`valid`. Findings on other entries are reported separately as unrelated and are not this phase's to
fix; a reserved ID stays retired even if the entry is abandoned.
Continue with a bounded prototype whenever a safe explicit assumption permits useful progress.

## Completion gate

Verify that planning wrote only selected-attempt paths plus authorized reflection index/document paths;
all unknowns are resolved or explicit bounded assumptions; every affected
durable/interface/code/test surface has a task-ready path; diagram checks passed; and protected
hashes show no unexpected change.

Report the feature ID, module architecture, plan path, generated temporal artifacts,
architecture/interface delta, code/test baseline examined, and reflections added.

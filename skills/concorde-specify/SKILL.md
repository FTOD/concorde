---
name: concorde-specify
description: "Create or update one direct module-level feature file."
scripts:
  py: scripts/workspace.py --phase specify
---

## User Input

```text
$ARGUMENTS
```

# Specify a Concorde Feature

Create or revise exactly one complete durable feature file. A feature is a level-local
capability of one module, never a hierarchy container. Its purpose, usage, requirements, embedded
interfaces, failures, and Architecture Zoom all belong in that one document.

## Workspace gate

Before resolving templates, reading feature artifacts, or writing anything, run `{SCRIPT}` from the
project root. Require a successful Protocol 13 result (`schema_version: 13`) whose status is
`resolved` or `selected`. Treat returned paths as the sole authority:

- identity: `feature_id`, `feature_path`, and `providing_module`;
- durable context: `feature_path`, `module_architecture`, bounded `module_ancestry`, and bounded
  `related_features` summaries;
- temporal context for an existing feature: stable-ID-derived `attempt_dir`, `attempt_state`,
  `checklists_dir`, and returned attempt paths;
- process context: `reflections` and its open count; and
- executable context: deterministic source/test roots or inventory hints.

For a missing feature, require `feature_id: null`, `attempt_state: unresolved`, and null temporal
paths. `phase_root` remains `feature_path`. Those nulls are a safety boundary, not paths to derive or
replace locally.

Do not derive alternate roots. Related-feature summaries and module ancestry are navigation only;
do not load another feature body or attempt unless the user's requested relationship makes that body
an explicit dependency. Reject a selected path outside the providing module's direct
`features/<NNN-name>.md` file.

## Authoring workflow

1. Consider `$ARGUMENTS` as the complete feature description. If it is empty, stop and ask for the
   intended capability.
2. Read the providing module's `architecture.md` as bounded structural authority. Confirm the
   module responsibility and boundary, immediate feature inventory, and all entities/interfaces the
   proposed feature will reference. Require its declared Archify `architecture` system overview to
   show the principal entities and directed relationships. If the overview is absent, invalid, or
   inconsistent with the architecture text, route that module to architecture work before declaring
   the feature ready. Do not descend into child modules merely because they exist.
3. Read `{FRAMEWORK}/templates/feature-template.md` as the format reference. Use the returned `feature_path`;
   create its `features/` parent only when Protocol 13 identifies a new canonical feature selection.
   A missing feature has no trustworthy attempt key until its front-matter stable ID exists: do not
   derive an ID from its filename or module, and do not create a provisional attempt.
4. Write one self-contained design with:

   - front matter containing stable `id`, `kind: feature`, `module`, `related_features`, provided and
     required interface IDs, and `evidence_status`;
   - observable Outcome and Scope;
   - representative success, edge, and failure Usage;
   - User Scenarios & Testing, testable Requirements, assumptions, and measurable Success Criteria;
   - one `## Interfaces` section defining every meaningful entry point's consumer/direction, inputs,
     outputs, obligations, failures, compatibility, example, and implementing architecture entities;
   - one `## Architecture Zoom` that references visible entity IDs and explains their collaboration
     without redefining entity identity, type, locator, or ownership; and
   - stable related-feature IDs with explicit composition, refinement, or dependency meaning.

5. Existing `contract.*` identifiers may remain as interface identities, but their semantics live in
   this design. Do not create a separate interface document or directory. Executed schemas/examples
   belong with source or tests, not beside the direct feature file.
6. The feature owns no diagram source. It may link the providing module's required system overview or
   another architecture-owned explanatory view. Verify that the system overview exists and that each
   referenced declaration has a
   normalized project-relative `.html` output below `generated/`, its source-relative `meta.output`
   resolves to that same unique target, and `meta.legend.mode` is `hidden`. Route an invalid module
   declaration to architecture work; do not repair it silently during feature specification.
7. For a newly created feature, reconcile only the providing architecture's immediate feature
   inventory entry after the design is ready. Any needed entity, relationship, interaction, or
   diagram change is an architecture change: surface it explicitly for review rather than inventing
   structural facts in the feature.
8. After writing a new feature and reconciling its module inventory, run `{SCRIPT}` again. Require
   Protocol 13 to resolve the exact non-null stable feature ID and return
   `.concorde/attempts/<stable-feature-id>/`; reject any basename-derived, module-local, or mismatched
   attempt path.
9. Create or re-evaluate the built-in requirements-quality checklist only at the second response's
   returned `checklists_dir/requirements.md`. Checklist marks judge the quality of requirements, not
   product completion. Never create a compatibility copy beside the direct feature file.
10. Persist Concorde selection in `.concorde/feature.json`; it is control state, not design
   authority.

## Quality gate

Before reporting readiness, verify:

- one canonical direct feature file exists and there is no feature wrapper directory;
- the feature ID and providing module resolve uniquely;
- every interface named in front matter is defined or explicitly external-required;
- each interface covers consumer/direction, entry points, inputs, outputs, obligations, failures,
  compatibility, examples where needed, and implementing entities;
- every Architecture Zoom entity resolves in the providing module or permitted ancestry;
- no architecture entity is redefined by the feature;
- related feature IDs resolve and their relationship meaning is explicit;
- requirements are testable and scenarios cover success plus material failures;
- the providing module's Archify architecture system overview represents its principal entities and
  directed relationships and passes showcase validation;
- any referenced architecture diagram passes output-boundary, source resolution, target uniqueness,
  and hidden-legend checks; and
- every requirements checklist item is truthfully evaluated.

Resolve at most three high-impact ambiguities by asking concise questions. Record unresolved matters
inside the design's Assumptions without inventing product facts. Specification does not modify code,
tests, generated projections, or another feature.

Concorde has no extension-hook phase. After the quality gate, the selected feature, module inventory,
requirements checklist, and deterministic validation are the complete readiness boundary.

## Completion report

Report the stable feature ID, providing module, `feature_path`, checklist status, architecture inventory
change if any, assumptions, and validation result.

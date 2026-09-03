# Specification model

Architecture Source Profile 7 has two durable authoring entry points: one module architecture and one
direct Markdown file per level-local feature.

## Canonical tree

```text
<specification-root>/
├── architecture.md
├── diagrams/
│   └── <question>.json
├── modules/
│   └── <child>/
│       └── architecture.md         # repeats complete module shape
└── features/
    └── <NNN-name>.md               # complete durable feature

<project>/.concorde/
├── config.json
├── attempts/<stable-feature-id>/   # optional and temporal
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── tasks.md
│   ├── checklists/
│   └── validation.md
└── reflections/
    ├── index.json                   # tracked allocation high-water only
    ├── pending/R-NNN.md             # recorded; triage pending
    ├── planned/R-NNN.md             # triaged; no maintainer input needed
    ├── needs-comments/R-NNN.md      # triaged; waiting for User Comments
    ├── config.json                  # triage configuration
    ├── plans/                       # ignored/disposable
    └── worktrees/                   # ignored/disposable
```

Mixed profiles are invalid. A feature is one file; while work is active, project control state may
contain one attempt keyed by that feature's globally unique stable ID. Features cannot contain
another feature, and attempts/reflections are not specification children.

## Module architecture profile

Each `architecture.md` uses front matter for stable identity/profile metadata and includes these
semantic sections:

- responsibility and boundary;
- immediate child-module inventory;
- level-local feature inventory;
- architecture entities;
- directed entity relationships;
- representative interactions;
- interface/feature governance references; and
- one declared Archify `architecture` system overview of principal entities and directed
  relationships, plus any optional secondary diagram declarations.

Entity tables provide stable ID, type, definition, and implementation path or external/conceptual
locator. Relationship tables provide stable ID/predicate, source, target, meaning, and governing
feature interface when applicable. Interaction descriptions preserve order/conditions without
descending into unimportant symbol detail.

Parent visibility includes its own entities, bounded child-module entities, and explicitly permitted
ancestor entities. A parent never copies a child's internal entity table.

## Feature file profile

Each feature file's front matter declares:

```yaml
id: feature.example.capability
kind: feature
module: module.example
related_features: []
interfaces:
  provided: [contract.example.capability]
  required: []
evidence_status: unknown
```

The body is self-contained for its consumer. It defines Outcome and Scope, Usage, scenarios and
testing, Requirements, Success Criteria, Interfaces, Architecture Zoom, edge/failure behavior,
assumptions, and Related Features. Heading details may vary when semantics remain unambiguous, but
all required information must be present.

An embedded interface defines consumer/direction, entry points, inputs, outputs, obligations,
failures, compatibility, representative example, and implementing entity IDs. Every provided ID in
front matter resolves locally. Required external interfaces identify an external provider; required
project interfaces resolve to another feature.

The Architecture Zoom names visible architecture entity IDs and describes their feature-specific
roles/collaboration. It never redeclares entity type, locator, or ownership.

## Architecture diagrams

Maintained diagram sources belong to modules and supplement `architecture.md`. Each has a complete
textual counterpart, provenance, `meta.legend.mode: hidden`, and a normalized unique generated HTML
target. Dynamic workflow/sequence/data-flow/lifecycle views remain explanatory interactions; stable
entity identity and relationships stay textual architecture authority.

Feature files may link a relevant module diagram but do not own diagram source files. Generated
HTML, screenshots, and receipts are projections.

## Temporal attempt profile

Planning creates the selected returned `attempt_dir` at
`.concorde/attempts/<stable-feature-id>/` when absent.
No temporal file is mirrored beside the feature file. Checklists are requirements-quality review state. Tasks are executable work state.
Validation evidence records actual commands/checks, outcomes, paths, scope, and limitations.

Planning reads feature file + architecture + code/tests and writes only temporal artifacts. Tasks may
explicitly authorize architecture/feature reconciliation together with code/tests. An implementation
task is complete only after a proportionate passed check is recorded.

## Workspace Protocol 13

Protocol 13 returns:

| Group | Fields |
|---|---|
| Identity | schema version, phase/status, feature ID, `feature_path`, providing module. |
| Durable | direct feature path, module architecture, bounded module ancestry, bounded related features. |
| Temporal | attempt directory/state and plan/tasks/checklist/research/data-model/quickstart/validation paths. |
| Process | `.concorde/reflections/` and open count. |
| Executable | deterministic source/test roots or inventory hints. |

All paths are safe project-relative canonical paths. Summaries are bounded navigation and do not
authorize loading another feature body or attempt.

## Validation

Deterministic validation checks profile/layout, acyclic hierarchy, unique identities, entity fields
and locators, relationship endpoints/direction, interactions, direct feature placement, complete
embedded interfaces, Architecture Zoom visibility, stable-ID control-attempt isolation, diagram
provenance/freshness, reflection grammar, generated-source boundaries, and unsafe paths/symlinks.

Warnings never become evidence of agreement. An invalid mixed profile fails instead of guessing a
migration.

## Cleanup-only delivery

Delivery requires complete tasks/checklists, passed proportionate evidence, current deterministic
validation, and a digest-bound Proposal 9. Apply revalidates the digest and safe exact target, then
atomically removes the attempt. Failure preserves the complete attempt and every durable/executable
authority.

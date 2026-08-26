# Contract: Concorde Architecture Source Profile 1

**Profile ID**: `profile.concorde.architecture-sources.v1`

**Governing boundary contract**: `contract.core.architecture-services`. This document is the
normative maintained-source representation used by that service, not an additional module boundary.

**Representation**: UTF-8 Markdown with constrained YAML front matter and UTF-8 JSON

## Authority

- Markdown owns module, feature, scenario, contract, constraint, and decision prose plus stable
  relationship metadata.
- A module's `architecture.json` owns its bounded component placement, connections, and canonical
  named scenario views. Descriptively named feature-owned Archify JSON may supplement that view by
  explaining component invocation, workflow, sequence, data flow, or lifecycle for representative
  scenarios; it does not own feature behavior or module boundaries.
- Each top-level feature has one canonical module-owned specification at
  `specs/<root-slug>[/modules/<child-slug>...]/features/<number-name>/spec.md`. It may declare
  immediate sub-features at `subfeatures/<number-name>/spec.md`; no deeper feature containment is
  valid. Every selected lifecycle root has one adjacent durable `design.md`. A parent specification
  owns aggregate outcomes and shared constraints; a sub-feature specification owns its focused
  outcome. The design at each root explains that root's accepted realization while referring to,
  never redefining, parent intent or module architecture.
- Code and tests own implementation and executable evidence. Missing evidence remains `unknown`.

## Feature Workspace Layout

Each feature or immediate sub-feature root separates durable intent from one temporal delivery
attempt:

```text
features/<number-name>/
├── spec.md
├── design.md
├── diagrams/
│   └── <scenario-or-question>.json
├── contracts/
├── subfeatures/
│   └── <number-name>/
│       ├── spec.md
│       ├── design.md
│       ├── diagrams/
│       ├── contracts/
│       └── implementation/
└── implementation/
    ├── checklists/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md
    └── validation.md
```

The `subfeatures/` directory is optional and valid only at a top-level feature root. A sub-feature
cannot contain or register another sub-feature. `spec.md`, `design.md`, declared feature-owned
Archify JSON below `diagrams/`, and feature-level
contract definitions/representations are durable. Requirements-quality checklists and the other files
below `implementation/` describe, review, and evidence at most one active delivery attempt. They are
not architecture entities and do not amend feature behavior or accepted design by changing.
Root-level `checklists/`, `plan.md`, `tasks.md`, research, technical models, acceptance guides, or
delivery evidence are invalid; compatibility copies and symlinks are prohibited.

After every current task is complete, explicit maintainer approval may harden the accepted realization
into `design.md` and remove the whole `implementation/` directory. A completed attempt remains
temporal until this operation succeeds. An existing non-empty attempt requires an explicit resume
decision and must never be replaced, archived as a second authority, or removed silently.

## Phase Path Mapping

The selected feature pointer identifies the feature root. Operations resolve from it as follows:

| Operation class | Resolved authority |
|---|---|
| specify, clarify, feature contracts | feature root for durable inputs/outputs; generated review state goes only to `implementation/checklists/` |
| custom requirements checklists | read durable root plus available attempt context; write only `implementation/checklists/` |
| plan, research, technical model, quickstart | read root `spec.md` + `design.md`; write `implementation/` |
| tasks, implement, analyze, converge, task-to-issue conversion, delivery validation | `implementation/` |
| feature hardening | read root `spec.md` + `design.md` and all attempt inputs; approved apply updates `design.md` and removes `implementation/` |

`.specify/feature.json` is the standard project-scoped selection record and may point to a valid
top-level feature or immediate sub-feature root. Read-only resolution may inspect but not rewrite it.
`SPECIFY_FEATURE_DIRECTORY` is the explicit one-command override. Concorde does not maintain a
second active-feature registry. When the selected root is a sub-feature, workspace resolution returns
the parent feature's stable ID and durable `spec.md`/`design.md` paths as read-only context plus
bounded sibling summaries; it never exposes sibling bodies or parent/sibling attempt paths.

## Package Discovery

`.concorde/config.json` is JSON with this initial shape:

```json
{
  "profile_version": 1,
  "specification_root": "specs/example",
  "root_module_id": "module.example"
}
```

`specification_root` is the unified subtree recursively containing `module.md`,
`contracts/**/contract.md`, `features/*/spec.md`,
`features/*/subfeatures/*/spec.md`, adjacent feature/sub-feature `design.md`, and declared Archify
JSON views. A feature-like `spec.md` at another depth is invalid rather than silently ignored.
Temporary requirements-quality checklists remain discoverable below each active lifecycle root's
`implementation/` subtree but are not durable specification sources. Readers MAY accept
the legacy key `architecture_root` only as an explicitly versioned migration alias; writers emit
`specification_root`. Paths are project-relative POSIX paths. Absolute paths, backslashes, empty
segments, `.` segments, `..` segments, and symlink escapes are invalid.

## Front-Matter Subset

Profile 1 supports:

- a document beginning with `---`, a closing `---`, then Markdown;
- mappings expressed by indentation in multiples of two spaces;
- string, integer, boolean, and null scalars;
- inline empty arrays (`[]`) and mappings (`{}`);
- block scalar lists using `- value`;
- nested mappings and lists of mappings needed by contract representations and scenario interactions;
- quoted strings without YAML tags, anchors, aliases, merge keys, or executable/custom types.

Unsupported YAML constructs produce a parse finding; the runtime never guesses their meaning.

## Document Profiles

### Module

Required front matter:

```yaml
id: module.example
kind: module
parent: null
view: specs/example/architecture.json
children: []
features: []
contracts:
  provided: []
  required: []
```

Required Markdown sections are `Responsibility` and `Boundary`. A leaf may omit `view` or set it to
null; a non-leaf must identify exactly one current-level view.

### Feature

Required front matter:

```yaml
id: feature.example.outcome
kind: feature
module: module.example
refines: []
subfeatures:
  - feature.example.outcome.focused-part
scenarios:
  - scenario.example.primary
contracts:
  provided:
    - contract.example.workflow
  required: []
architecture_view: specs/example/architecture.json
diagrams:
  - source: specs/example/features/001-outcome/diagrams/component-interactions.json
    role: core
    kind: architecture
    scenarios:
      - scenario.example.primary
    output: generated/architecture/example-component-interactions.html
evidence_status: unknown
canonical_spec: specs/example/features/001-outcome/spec.md
```

A direct sub-feature uses the same `kind: feature` and stable ID namespace but declares:

```yaml
parent_feature: feature.example.outcome
subfeatures: []
canonical_spec: specs/example/features/001-outcome/subfeatures/001-focused-part/spec.md
```

Its providing module must equal its parent's module, the parent must register its ID exactly once,
and it must not be registered as a top-level module feature. Its Markdown body includes a non-empty
`## Outcome` section used for bounded summaries. A lower-module feature without a parent refinement
must include `internal: true` and a non-empty `internal_rationale`; containment never substitutes for
the existing adjacent-module refinement rule. Every feature body contains the primary textual
definition and requirements; scenario references supply examples and do not exhaustively define it.

The `canonical_spec` path must equal the document's own project-relative path. Its containing feature
root must match the providing module's package, contain a real non-symlink `design.md`, and may contain
at most one active `implementation/` child. Durable feature metadata or design decisions must never
be inferred from that child without explicit hardening.

### Feature design

`design.md` is UTF-8 Markdown at exactly the feature root. It has no independent feature ID and does
not duplicate `spec.md` front matter. Before the first hardened milestone it explicitly says that no
realization has been hardened. Once hardened, it contains enough current information to explain:

- how related modules and lower-level features collaborate for the feature's scenarios;
- which maintained contracts govern boundaries and what data/control moves across them;
- durable implementation decisions and code/evidence references needed to understand the realization;
- known limitations, compatibility constraints, and deferred work that remains true after the
  temporal attempt is removed; and
- traceability back to behavioral requirements and maintained architecture sources.

The design may quote stable identifiers and summarize the current structure, but module responsibility,
ownership, contracts, and one-level organization remain authoritative only in module architecture
sources. Planning and implementation commands read `design.md` as a baseline and must not update it.

`diagrams` is optional for a simple feature with a recorded sufficiency rationale. Each entry has a
safe `source` immediately below the feature's `diagrams/` directory, a `role` of `core` or
`supplemental`, an Archify `kind`, one or more scenario IDs or a named question, and a safe generated
`output`. A feature may declare at most one core diagram. That core MUST use `kind: architecture` and
show the stable components, responsibilities, and interactions that provide the feature. Dynamic
workflow, sequence, data-flow, and lifecycle diagrams are supplemental views for narrower scenario
questions; none may be designated as the core diagram. A cross-component feature requires a core
component diagram unless the Markdown records why its text and module-level view are sufficient.
The source filename must be descriptive and must not be `architecture.json`; its generated output is
evidence, not maintained intent. Documentation publication discovers these declarations and embeds
every fresh generated view on the canonical feature page automatically.

### Contract

Required front matter:

```yaml
id: contract.example.workflow
kind: contract
module: module.example
role: provided
flow: bidirectional
counterparties:
  - external.maintainer
representation:
  kind: standard
  format: Example Protocol
  version: "1"
  definition: https://example.invalid/protocol
features:
  - feature.example.outcome
evidence_status: unknown
```

Required Markdown sections are `Purpose`, `Information`, `Obligations`, `Failure Semantics`,
`Compatibility`, and `Evidence`. A custom representation uses a project-relative schema or grammar,
includes complete field semantics and compatibility rules, and references at least one representative
example.

### Scenario

A scenario may be a dedicated Markdown document or a structured current-level record referenced by a
feature. Its machine-readable data includes a stable ID, owning module, participants, and ordered
interactions. Each interaction has `from`, `to`, `description`, and `contract` when it crosses a
module boundary. A prose-only scenario sets `prose_only: true` and supplies a rationale.

### Architecture view

The JSON document follows the Archify architecture schema supported by this project and must also
satisfy Concorde visibility rules:

- participants are the current module boundary, its immediate child modules, and permitted externals;
- child features, grandchild modules, and implementation details are absent;
- every referenced scenario belongs to the current module level;
- every connection endpoint resolves within the view; and
- every boundary-crossing connection can be traced to a declared contract in maintained Markdown.

### Feature-owned explanatory view

The JSON document follows the matching Archify schema for `architecture`, `workflow`, `sequence`,
`dataflow`, or `lifecycle`. It must identify the scenario or question it explains, use participants
consistent with maintained module/contract prose, preserve ordered and directional interactions, and
have a complete textual counterpart in `spec.md`. Boundary-crossing interactions name or trace to
their governing contract. Validation and delivery are deterministic; visual-check automation records
containment/captures but never substitutes for human perceptual review.

## Stable IDs

- IDs use lowercase dotted namespaces and hyphenated terminal words.
- IDs are unique across all documents of the same kind and may not be reassigned to a different
  meaning within the same Concorde major version.
- References use IDs, not titles or inferred filenames.
- Module containment, feature refinement, and feature containment are independently acyclic.
- Feature refinements cross one adjacent module level only.

## Diagnostics

Every invalid source yields a `Validation Finding` with a stable rule ID, severity, project-relative
source and optional location, message, and concrete remediation. The validator is read-only and
reports all independently detectable findings in deterministic order.

Validation also checks feature-workspace layout, selected-root safety, durable/temporal phase paths,
custom definition/example resolution, scenario boundary contract references, explicit evidence
references, and generated-output freshness through the responsible deterministic adapter. Unsupported
custom formats are reported as unsupported rather than treated as conforming. Renderer and
publication validators retain ownership of their formats; Architecture Core normalizes their
findings without reimplementing them.

## Compatibility

Readers of profile 1 reject an unsupported `profile_version`. Adding optional fields is compatible;
removing a required field, changing field meaning, or expanding accepted syntax incompatibly requires
a new profile version and migration guidance.

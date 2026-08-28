# Contract: Concorde Architecture Source Profile 2

**Profile ID**: `profile.concorde.architecture-sources.v2`

**Governing boundary contract**: `contract.core.architecture-services`. This document is the
normative maintained-source representation used by that service, not an additional module boundary.

**Representation**: UTF-8 Markdown with constrained YAML front matter and UTF-8 JSON

**Supersedes**: Profile 1. Profile 2 introduces the module design reference, the module summary
shape and reading budget, and renames the feature-level accepted realization from `design.md` to
`implementation.md`. Readers of Profile 2 reject any other `profile_version`.

## Authority

- Every level of the hierarchy separates a summary that is read from a reference that is consulted:
  - `module.md` (module summary) owns module responsibility, boundary, current-level inventories,
    a representative scenario, and the key design rationale, within a reading budget;
  - `design.md` (module design reference) records implementation detail and the ideas, rationales,
    alternatives, and decisions developed during development; it explains the summary, the level
    view, and the contracts and never redefines them, and no operation reads it implicitly.
- A module's `architecture.json` owns its bounded component placement, connections, and canonical
  named scenario views and is the module summary's required structure diagram. Descriptively named
  module- or feature-owned Archify JSON may supplement it; supplemental views do not own behavior or
  boundaries.
- Each top-level feature has one canonical specification at
  `specs/<root-slug>[/modules/<child-slug>...]/features/<number-name>/spec.md`. It may declare
  immediate sub-features at `subfeatures/<number-name>/spec.md`; no deeper containment is valid.
  Every lifecycle root has one adjacent durable `implementation.md` (accepted realization). A parent
  specification owns aggregate outcomes and shared constraints; a sub-feature specification owns
  its focused outcome. The accepted realization at each root explains that root's realization while
  referring to, never redefining, parent intent or module architecture.
- The name `design.md` is reserved for module level; `implementation.md` is reserved for feature
  roots. A `design.md` at a feature root is a legacy artifact and invalid; aliases and symlinks are
  invalid for either name.
- Code and tests own implementation and executable evidence. Missing evidence remains `unknown`.

## Module Package Layout

```text
<module>/
├── module.md          summary (required)
├── design.md          design reference (required; may state nothing is recorded yet)
├── architecture.json  level view (required for a non-leaf module)
├── diagrams/          optional supplemental module-owned Archify views
├── contracts/
├── features/
└── modules/
```

## Feature Workspace Layout

Each feature or immediate sub-feature root separates durable intent from one temporal delivery
attempt:

```text
features/<number-name>/
├── spec.md
├── implementation.md
├── diagrams/
│   └── <scenario-or-question>.json
├── contracts/
├── subfeatures/
│   └── <number-name>/
│       ├── spec.md
│       ├── implementation.md
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
cannot contain or register another sub-feature. `spec.md`, `implementation.md`, declared
feature-owned Archify JSON below `diagrams/`, and feature-level contract definitions/representations
are durable. Requirements-quality checklists and the other files below `implementation/` describe,
review, and evidence at most one active delivery attempt. They are not architecture entities and do
not amend feature behavior or accepted realization by changing. Root-level `checklists/`, `plan.md`,
`tasks.md`, research, technical models, acceptance guides, or delivery evidence are invalid;
compatibility copies and symlinks are prohibited.

After every current task is complete, explicit maintainer approval may harden the accepted
realization into `implementation.md`, optionally amend the providing module's `design.md` in the
same atomic operation, and remove the whole `implementation/` directory. A completed attempt
remains temporal until this operation succeeds. An existing non-empty attempt is reported as
`implementation_state: active` and must never be replaced, archived as a second authority, or
removed silently.

## Phase Path Mapping

The selected feature pointer identifies the feature root. Operations resolve from it as follows:

| Operation class | Resolved authority |
|---|---|
| specify, clarify, feature contracts | feature root for durable inputs/outputs; a new root receives `spec.md` and a placeholder `implementation.md`; generated review state goes only to `implementation/checklists/`; the providing module's `module.md` is bounded context |
| custom requirements checklists | read durable root plus available attempt context; write only `implementation/checklists/` |
| plan, research, technical model, quickstart | read root `spec.md` + `implementation.md` and the module summary; consult the module `design.md` only deliberately and cite it; write `implementation/` |
| tasks, implement, analyze, converge, task-to-issue conversion, delivery validation | `implementation/` |
| feature hardening | read root `spec.md` + `implementation.md`, the module summary and `design.md`, and all attempt inputs; approved apply writes `implementation.md`, optionally the module `design.md`, and removes `implementation/` |

`.specify/feature.json` is the standard project-scoped selection record and may point to a valid
top-level feature or immediate sub-feature root. Read-only resolution may inspect but not rewrite
it. `SPECIFY_FEATURE_DIRECTORY` is the explicit one-command override. Concorde does not maintain a
second active-feature registry. When the selected root is a sub-feature, workspace resolution
returns the parent feature's stable ID and durable `spec.md`/`implementation.md` paths as read-only
context plus bounded sibling summaries; it never exposes sibling bodies or parent/sibling attempt
paths. Every workspace result also names the providing module's `module.md` and `design.md` as
navigation references.

## Package Discovery

`.concorde/config.json` is JSON with this shape:

```json
{
  "profile_version": 2,
  "specification_root": "specs/example",
  "root_module_id": "module.example"
}
```

`specification_root` is the unified subtree recursively containing `module.md`, each module's
adjacent `design.md`, `contracts/**/contract.md`, `features/*/spec.md`,
`features/*/subfeatures/*/spec.md`, adjacent feature/sub-feature `implementation.md`, and declared
Archify JSON views. A feature-like `spec.md` at another depth is invalid rather than silently
ignored, and so is a `design.md` beside a feature `spec.md`. Temporary requirements-quality
checklists remain discoverable below each active lifecycle root's `implementation/` subtree but are
not durable specification sources. Paths are project-relative POSIX paths. Absolute paths,
backslashes, empty segments, `.` segments, `..` segments, and symlink escapes are invalid.

## Front-Matter Subset

Profile 2 supports the same subset as Profile 1:

- a document beginning with `---`, a closing `---`, then Markdown;
- mappings expressed by indentation in multiples of two spaces;
- string, integer, boolean, and null scalars;
- inline empty arrays (`[]`) and mappings (`{}`);
- block scalar lists using `- value`;
- nested mappings and lists of mappings needed by contract representations and scenario interactions;
- quoted strings without YAML tags, anchors, aliases, merge keys, or executable/custom types.

Unsupported YAML constructs produce a parse finding; the runtime never guesses their meaning.

## Document Profiles

### Module summary

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

Required Markdown H2 sections (any order; additional sections are permitted):

| Section | Content rule |
|---|---|
| `Responsibility` | non-empty prose |
| `Boundary` | non-empty prose |
| `Structure` | a Markdown link whose target resolves to the declared `view` (non-leaf); a leaf with `view` null or absent records a non-empty rationale instead; further diagrams may be linked or embedded |
| `Features` | a Markdown table inventorying current-level features, or the line `None.` |
| `Contracts` | a Markdown table inventorying provided and required contracts, or `None.` |
| `Submodules` | a Markdown table inventorying immediate children, or `None.` |
| `Representative Scenario` | non-empty prose describing one current-level scenario |
| `Design Rationale` | short prose plus a Markdown link whose target resolves to the adjacent `design.md` |

The summary body (excluding front matter, fenced code blocks, and HTML comments) is expected to
stay within the reading budget of 4,000 words; exceeding it is reported as a warning. A non-leaf
module must identify exactly one current-level view; a leaf may omit `view` or set it to null.

### Module design reference

`design.md` is UTF-8 Markdown at exactly the module root. It has no front matter and no
independent ID, and is never parsed for metadata. It contains an H1 and at least one H2 and is
organized under stable headings such as `Implementation Notes`, `Design Rationale`,
`Alternatives Considered`, and `Decision Log`. Before anything is recorded it may state that no
implementation detail or design rationale has been recorded yet. It must be a real, non-empty,
non-symlink file. Maintainers may edit it directly; workflow operations write it only through an
approved hardening proposal targeting the module at which the hardened feature is specified. It is
included in the package's source digest and returned by context as a navigation reference only.

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
root must match the providing module's package, contain a real non-symlink `implementation.md`,
contain no `design.md`, and may contain at most one active `implementation/` child. Durable feature
metadata or accepted realization must never be inferred from that child without explicit hardening.

### Feature implementation (accepted realization)

`implementation.md` is UTF-8 Markdown at exactly the feature root. It has no independent feature ID
and does not duplicate `spec.md` front matter. Before the first hardened milestone it holds only
the explicit statement that no implementation realization has been hardened yet under the required
headings. The first approved hardening writes it in full and each later hardening completes it.
Once hardened, it contains enough current information to explain:

- how related modules and lower-level features collaborate for the feature's scenarios;
- which maintained contracts govern boundaries and what data/control moves across them;
- durable implementation decisions and code/evidence references needed to understand the realization;
- known limitations, compatibility constraints, and deferred work that remains true after the
  temporal attempt is removed; and
- traceability back to behavioral requirements and maintained architecture sources.

Required H2 sections: `Realization Overview`, `Module and Feature Collaboration`,
`Scenario Realization`, `Durable Implementation Decisions`, `Traceability and Evidence`,
`Known Limitations`. The document may quote stable identifiers and summarize the current
structure, but module responsibility, ownership, contracts, and one-level organization remain
authoritative only in module architecture sources. Planning and implementation commands read
`implementation.md` as a baseline (treating the placeholder as the absence of a baseline) and must
not update it.

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

### Feature-owned or module-owned explanatory view

The JSON document follows the matching Archify schema for `architecture`, `workflow`, `sequence`,
`dataflow`, or `lifecycle`. It must identify the scenario or question it explains, use participants
consistent with maintained module/contract prose, preserve ordered and directional interactions, and
have a complete textual counterpart in the owning `spec.md` or `module.md`. Boundary-crossing
interactions name or trace to their governing contract. Validation and delivery are deterministic;
visual-check automation records containment/captures but never substitutes for human perceptual
review.

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

Validation also checks the module summary shape (required sections, structure link or leaf
rationale, inventory tables, reachability of the design reference), the reading budget (warning
severity; it never changes the validation status), module design-reference presence, feature-root
document pairing and legacy names (a feature-root `design.md`, or both names present),
feature-workspace layout, selected-root safety, durable/temporal phase paths, custom
definition/example resolution, scenario boundary contract references, explicit evidence references,
and generated-output freshness through the responsible deterministic adapter. Unsupported custom
formats are reported as unsupported rather than treated as conforming. Renderer and publication
validators retain ownership of their formats; Architecture Core normalizes their findings without
reimplementing them.

## Compatibility

Readers of Profile 2 reject an unsupported `profile_version`, including Profile 1; Concorde is
currently the only adopter and migrated in one refactor, so no Profile 1 reader is retained. Adding
optional fields or sections is compatible; removing a required field, changing field meaning, or
expanding accepted syntax incompatibly requires a new profile version and migration guidance.

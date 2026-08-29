# Contract: Concorde Architecture Source Profile 4

**Profile ID**: `profile.concorde.architecture-sources.v4`

**Governing boundary contract**: `contract.core.architecture-services`. This document is the
normative maintained-source representation used by that service, not an additional module boundary.

**Representation**: UTF-8 Markdown with constrained YAML front matter and UTF-8 JSON

**Supersedes**: Profile 3. Profile 4 gives every module package an `architecture/` directory that
holds the level's Archify diagrams (`architecture/diagrams/`, any number, discovered rather than
declared), its boundary contracts (`architecture/contracts/`), and its immediate submodules
(`architecture/modules/`), beside the level's `features/`. It keeps Profile 3's document tiers:
`abstract.md` as the read-first feature tier, `design.md` as feature behavioral authority,
`implementation.md` as accepted feature realization, and module `design.md` as the module design
reference. Readers reject any other `profile_version`.

## Authority

- Every level of the hierarchy separates what is read from what is consulted:
  - `module.md` (module summary) owns module responsibility, boundary, current-level inventories,
    a representative scenario, and the key design rationale, within a reading budget;
  - the module `design.md` (module design reference) records implementation detail and the ideas,
    rationales, alternatives, and decisions developed during development; it explains the summary,
    the level view, and the contracts and never redefines them, and no operation reads it
    implicitly;
  - `abstract.md` (feature abstract) gives a self-contained quick understanding of a feature — purpose,
    functionality, basic structure, logic — within a reading budget; it summarizes `design.md` and
    never defines beyond it;
  - `design.md` (feature specification) is the complete, self-contained authority for required
    behavior;
  - feature `implementation.md` records how the
    accepted implementation realizes the feature in full detail; it is consulted when writing the
    code or fixing a bug and no operation reads it implicitly.
- A module's diagrams under `architecture/diagrams/` own its bounded component placement,
  connections, and canonical named scenario views. Its `architecture`-kind diagrams are the level
  views: together they show the current module, its immediate children, and permitted externals, and
  at least one of them is the module summary's structure diagram, linked from `## Structure`. Any
  further diagram of any supported kind explains one question or scenario of the level and is linked
  from the summary, the design reference, or the project reflection log; no diagram owns behavior or
  boundaries, and none is declared in front matter.
- Each top-level feature has one canonical specification at
  `specs/<root-slug>[/architecture/modules/<child-slug>...]/features/<number-name>/design.md`. It may declare
  immediate sub-features at `subfeatures/<number-name>/design.md`; no deeper containment is valid.
  Every lifecycle root owns the durable trio `abstract.md`, `design.md`, and `implementation.md`. A parent
  specification owns aggregate outcomes and shared constraints; a sub-feature specification owns
  its focused outcome. `implementation.md` at each root explains that root's realization while
  referring to, never redefining, parent intent or module architecture.
- Aliases and symlinks are invalid for `abstract.md`, feature `design.md`, and `implementation.md`.
- Where `abstract.md` and `design.md` disagree, `design.md` prevails; the disagreement is a defect of the
  abstract reported by analysis and fixed by specification review, never resolved by tooling.
- Code and tests own implementation and executable evidence. Missing evidence remains `unknown`.

## Module Package Layout

```text
<module>/
├── module.md                      summary (required)
├── design.md                      module design reference (required; may state nothing is recorded yet)
├── reflections.md                 root module only: the project reflection log
├── features/<number-name>/        features specified at this level (layout below)
└── architecture/                  how the level is composed
    ├── diagrams/<name>.json       module-owned Archify diagrams; a non-leaf module has at least one
    │                              architecture-kind level view; every file is linked from module.md,
    │                              design.md, or reflections.md
    ├── contracts/<id>/contract.md the module's boundary contracts
    └── modules/<child-slug>/      immediate submodules, each repeating this layout
```

`features/` and `architecture/` sit side by side at every level: a feature says what the level can do;
`architecture/` says how the level is composed. A child module lives at exactly
`<parent>/architecture/modules/<child-slug>/`; the root module lives at the configured specification
root. An `architecture.json`, `contracts/`, or `modules/` entry directly at a module root, a `view`
field in `module.md`, and an `architecture_view` field in a feature `design.md` are Profile 3 remnants
and are invalid.

## Feature Workspace Layout

Each feature or immediate sub-feature root separates durable intent from one temporal delivery
attempt:

```text
features/<number-name>/
├── abstract.md            read first: self-contained quick understanding (under 15 minutes)
├── design.md            complete behavioral authority
├── implementation.md accepted realization, full implementation detail
├── diagrams/
│   └── <scenario-or-question>.json
├── contracts/
├── subfeatures/
│   └── <number-name>/
│       ├── abstract.md
│       ├── design.md
│       ├── implementation.md
│       ├── diagrams/
│       ├── contracts/
│       └── attempt/
└── attempt/
    ├── checklists/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md
    └── validation.md
```

The `subfeatures/` directory is optional and valid only at a top-level feature root. A sub-feature
cannot contain or register another sub-feature. `abstract.md`, `design.md`, `implementation.md`, declared
feature-owned Archify JSON below `diagrams/`, and feature-level contract definitions/representations
are durable. Requirements-quality checklists and the other files below `attempt/` describe,
review, and evidence at most one active delivery attempt. They are not architecture entities and do
not amend feature behavior or accepted realization by changing. Root-level `checklists/`, `plan.md`,
`tasks.md`, research, technical models, acceptance guides, or delivery evidence are invalid;
compatibility copies and symlinks are prohibited.

After every current task is complete, explicit maintainer approval may accept the accepted
realization into feature `implementation.md`, optionally amend the providing module's `design.md` in
the same atomic operation, and remove the whole `attempt/` directory. A completed attempt
remains temporal until this operation succeeds. An existing non-empty attempt is reported as
`attempt_state: active` and must never be replaced, archived as a second authority, or
removed silently. Acceptance never writes `abstract.md` or `design.md`.

## Phase Path Mapping

The selected feature pointer identifies the feature root. Operations resolve from it as follows:

| Operation class | Resolved authority |
|---|---|
| specify, clarify, feature contracts | feature root for durable inputs/outputs; a new root receives authored `abstract.md`, `design.md`, and placeholder `implementation.md`; clarification updates `design.md` and the abstract wherever it summarized the changed behavior; generated review state goes only to `attempt/checklists/`; the providing module's `module.md` is bounded context |
| custom requirements checklists | read durable root plus available attempt context (the abstract is in scope); write only `attempt/checklists/` |
| plan, research, technical model, quickstart | read root `design.md` + `implementation.md` and the module summary (the abstract orients only); consult the module `design.md` only deliberately and cite it; write `attempt/` |
| tasks, implement, analyze, converge, task-to-issue conversion, delivery validation | `attempt/`; analysis also reads `abstract.md` to report disagreement with `design.md` |
| feature acceptance | read root `abstract.md` + `design.md` + `implementation.md`, the module summary and `design.md`, and all attempt inputs; approved apply writes feature `implementation.md`, optionally module `design.md`, and removes `attempt/` |

`.specify/feature.json` is the standard project-scoped selection record and may point to a valid
top-level feature or immediate sub-feature root. Read-only resolution may inspect but not rewrite
it. `SPECIFY_FEATURE_DIRECTORY` is the explicit one-command override. Concorde does not maintain a
second active-feature registry. When the selected root is a sub-feature, workspace resolution
returns the parent feature's stable ID and durable `abstract.md`/`design.md`/`implementation.md` paths as
read-only context plus bounded sibling summaries; it never exposes sibling bodies or parent/sibling
attempt paths. Every workspace result also names the providing module's `module.md` and `design.md`
as navigation references.

## Package Discovery

`.concorde/config.json` is JSON with this shape:

```json
{
  "profile_version": 4,
  "specification_root": "specs/example",
  "root_module_id": "module.example"
}
```

`specification_root` is the unified subtree recursively containing `module.md`, each module's
adjacent `design.md`, each module's `architecture/contracts/**/contract.md`, every `*.json` directly
beneath each module's `architecture/diagrams/`, `features/*/design.md`,
`features/*/subfeatures/*/design.md`, each feature root's adjacent `abstract.md` and `implementation.md`, and
declared feature-owned Archify JSON. A feature-like `design.md` at another depth is invalid rather than
silently ignored. Former `tldr.md`/`spec.md` files, `implementation/` attempt directories, and the
Profile 3 module entries named above are invalid. Temporary
requirements-quality checklists remain discoverable below each active lifecycle root's
`attempt/` subtree but are not durable specification sources. Paths are project-relative
POSIX paths. Absolute paths, backslashes, empty segments, `.` segments, `..` segments, and symlink
escapes are invalid.

## Front-Matter Subset

Profile 4 supports the same subset as Profiles 1 to 3:

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
| `Structure` | a Markdown link whose target resolves to at least one `architecture`-kind diagram beneath the module's `architecture/diagrams/` (required whenever the module has one; a non-leaf module always has one); a module without such a diagram records a non-empty rationale instead; further diagrams may be linked or embedded |
| `Features` | a Markdown table inventorying current-level features, or the line `None.` |
| `Contracts` | a Markdown table inventorying provided and required contracts, or `None.` |
| `Submodules` | a Markdown table inventorying immediate children, or `None.` |
| `Representative Scenario` | non-empty prose describing one current-level scenario |
| `Design Rationale` | short prose plus a Markdown link whose target resolves to the adjacent `design.md` |

The summary body (excluding front matter, fenced code blocks, and HTML comments) is expected to
stay within the reading budget of 4,000 words; exceeding it is reported as a warning. A non-leaf
module maintains at least one `architecture`-kind diagram beneath `architecture/diagrams/`; a leaf
may maintain none.

### Module design reference

The module `design.md` is UTF-8 Markdown at exactly the module root. It has no front matter and no
independent ID, and is never parsed for metadata. It contains an H1 and at least one H2 and is
organized under stable headings such as `Implementation Notes`, `Design Rationale`,
`Alternatives Considered`, and `Decision Log`. Before anything is recorded it may state that no
implementation detail or design rationale has been recorded yet. It must be a real, non-empty,
non-symlink file. Maintainers may edit it directly; workflow operations write it only through an
approved acceptance proposal targeting the module at which the accepted feature is specified. It is
included in the package's source digest and returned by context as a navigation reference only.

### Feature abstract

`abstract.md` is UTF-8 Markdown at exactly the feature root. It has no front matter and no independent
ID, and is never parsed for metadata. Its H1 is conventionally `# Feature Abstract: <title>`. Its body
consists of exactly these H2 sections, in this order, each non-empty:

| Section | Content rule |
|---|---|
| `Purpose` | the outcome and for whom, in short prose |
| `Functionality` | what the feature does and does not do: its operations, surfaces, parts, and boundaries; tables where an inventory helps |
| `Structure` | the participating parts and how they collaborate; at least one link that resolves to a declared feature diagram source, the level view, or a delivered `/architecture/*.html` route, or a fenced ```` ```text ```` sketch |
| `Logic` | how it works (the main flows in order) and the rules an implementer must not break; the section names at least one `FR-NNN` requirement identifier, and every identifier it names is defined in the adjacent `design.md` as `**FR-NNN**` |
| `Read Next` | links to `design.md`, `implementation.md`, the contracts, the module summary, and any sub-features or parent, for the reader who wants the next level of detail |

The abstract is self-contained: its links redirect and are never required to understand it. It must
not state a requirement, scope boundary, or success criterion absent from `design.md`. The body
(excluding front matter, fenced code blocks, and HTML comments) is expected to stay within the
reading budget of 3,000 words; exceeding it is reported as a warning. It is authored by the specify
phase from the `abstract-template`, kept current by the specify and clarify phases, and written by no
other operation. It must be a real, non-empty, non-symlink file, is included in the package's
source digest, and is returned by context and workspace results as a navigation reference only.

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
diagrams:
  - source: specs/example/features/001-outcome/diagrams/component-interactions.json
    role: core
    kind: architecture
    scenarios:
      - scenario.example.primary
    output: generated/architecture/example-component-interactions.html
evidence_status: unknown
canonical_design: specs/example/features/001-outcome/design.md
```

A direct sub-feature uses the same `kind: feature` and stable ID namespace but declares:

```yaml
parent_feature: feature.example.outcome
subfeatures: []
canonical_design: specs/example/features/001-outcome/subfeatures/001-focused-part/design.md
```

Its providing module must equal its parent's module, the parent must register its ID exactly once,
and it must not be registered as a top-level module feature. Its Markdown body includes a non-empty
`## Outcome` section used for bounded summaries. A lower-module feature without a parent refinement
must include `internal: true` and a non-empty `internal_rationale`; containment never substitutes for
the existing adjacent-module refinement rule. Every feature body contains the primary textual
definition and requirements; scenario references supply examples and do not exhaustively define it.
`design.md` is self-contained — readable without the abstract — and may link `abstract.md` and `implementation.md`
for redirection.

The `canonical_design` path must equal the document's own project-relative path. Its containing feature
root must match the providing module's package and contain real non-symlink `abstract.md` and
`implementation.md` files with at most one active `attempt/` child.
Durable feature metadata or accepted realization must never be inferred from that child without
explicit acceptance.

### Feature implementation (accepted realization)

Feature `implementation.md` is UTF-8 Markdown at exactly the feature root. It has no independent
feature ID and does not duplicate `design.md` front matter. Its H1 is conventionally
`# Feature Implementation: <title>`. Before the first accepted milestone it holds only the
explicit statement that no implementation realization has been accepted yet under the required
headings (seeded from the `implementation-template`). The first approved acceptance writes it in full and
each later acceptance completes it. Once accepted, it contains enough current information to explain:

- how related modules and lower-level features collaborate for the feature's scenarios;
- which maintained contracts govern boundaries and what data/control moves across them;
- durable implementation decisions and code/evidence references needed to understand the realization;
- the implementation detail a coder needs when writing the code or fixing a bug;
- known limitations, compatibility constraints, and deferred work that remains true after the
  temporal attempt is removed; and
- traceability back to behavioral requirements and maintained architecture sources.

Required H2 sections, in this order and before any further heading: `Realization Overview`,
`Module and Feature Collaboration`, `Scenario Realization`, `Durable Implementation Decisions`,
`Traceability and Evidence`, `Known Limitations`. Further headings may follow for implementation
detail. The document may quote stable identifiers and summarize the current structure, but module
responsibility, ownership, contracts, and one-level organization remain authoritative only in
module architecture sources, and required behavior remains authoritative only in `design.md`.
Planning and implementation commands read feature `implementation.md` as a baseline (treating the
placeholder as the absence of a baseline) and must not update it.

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
every fresh generated view on the canonical feature page, which is the abstract, automatically.

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

### Module-owned diagrams (`architecture/diagrams/`)

Every `*.json` directly beneath a module's `architecture/diagrams/` is a maintained diagram of that
level. Each is a JSON object whose `diagram_type` is one of `architecture`, `workflow`, `sequence`,
`dataflow`, or `lifecycle` and whose `meta` object carries a non-empty `title` and, when the diagram
is delivered, a safe `output` path (relative to the diagram) beneath `generated/`. Symlinks and
files at any other depth are invalid. Each diagram must be referenced by a Markdown link from the
level's `module.md`, its `design.md`, or the project reflection log; an unreferenced diagram is a
validation finding, not a silently ignored file.

The `architecture`-kind diagrams are the level views. Each follows the Archify architecture schema
supported by this project and must also satisfy Concorde visibility rules:

- participants are the current module boundary, its immediate child modules, and permitted externals;
- child features, grandchild modules, and implementation details are absent;
- every scenario named in `meta.views` uses only participants visible in that diagram;
- every connection endpoint resolves within the diagram;
- every boundary-crossing connection can be traced to a declared contract in maintained Markdown;
- every immediate child drawn carries an explicit `module_id`; and
- across a non-leaf module's level views, every immediate child appears at least once.

A scenario a feature cites must be defined in `meta.views` of one of the providing module's diagrams
(of any kind); bounded context, readiness, and validation read all of a level's diagrams together.

### Explanatory views (feature-owned, or module-owned beyond the level views)

The JSON document follows the matching Archify schema for `architecture`, `workflow`, `sequence`,
`dataflow`, or `lifecycle`. It must identify the scenario or question it explains, use participants
consistent with maintained module/contract prose, preserve ordered and directional interactions, and
have a complete textual counterpart in the owning feature `design.md` or, for a module-owned diagram,
in the level's `module.md` or `design.md` (an abstract may link and summarize it but is not its
counterpart). Boundary-crossing interactions name or trace to their governing contract. Validation
and delivery are deterministic; visual-check automation records containment/captures but never
substitutes for human perceptual review.

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

Validation also checks the module package layout (a child module beneath its parent's
`architecture/modules/`, no Profile 3 `architecture.json`, `contracts/`, or `modules/` entry at a
module root, no `view` or `architecture_view` field), the module summary shape (required sections, a
structure link to one of the level's architecture diagrams or a leaf rationale, inventory tables,
reachability of the design reference) and reading budget (warning severity; it never changes the
validation status), module design-reference presence, that every diagram beneath
`architecture/diagrams/` is referenced from the level's documents, the feature
abstract shape (exactly the five sections in order, a structure link or inline sketch, `Logic`
requirement citations that resolve in the adjacent `design.md`) and reading budget (warning), the
feature-root durable trio and legacy names (former `tldr.md`/`spec.md` files, a former
`implementation/` attempt directory, or a missing `abstract.md` or `implementation.md`),
feature-workspace layout, selected-root safety, durable/temporal phase paths, custom
definition/example resolution, scenario boundary contract references, explicit evidence references,
and generated-output freshness through the responsible deterministic adapter. Unsupported custom
formats are reported as unsupported rather than treated as conforming. Renderer and publication
validators retain ownership of their formats; Architecture Core normalizes their findings without
reimplementing them.

## Compatibility

Readers of Profile 4 reject an unsupported `profile_version`, including Profiles 1 to 3; Concorde
is currently the only adopter and migrates in one refactor, so no earlier reader is retained. Adding
optional fields or sections is compatible; removing a required field, changing field meaning, or
expanding accepted syntax incompatibly requires a new profile version and migration guidance.

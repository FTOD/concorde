<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Modified principles:
  - I. Recursive, Bounded Architecture -> III. Recursive, Bounded Architecture (renumbered)
  - II. Explicit Ownership and Feature Alignment -> IV. Explicit Ownership and Feature Alignment
    (renumbered)
  - III. Contracts Govern Every Boundary -> V. Contracts Govern Every Boundary (renumbered)
  - IV. One Authority per Fact, Traceable Everywhere -> VI. One Authority per Fact, Traceable
    Everywhere (renumbered)
  - V. Deterministic Validation and Reviewed Evidence -> VII. Deterministic Validation and Reviewed
    Evidence (renumbered)
- Added principles:
  - I. Concorde Is the Workflow Product and Its Proving Ground
  - II. Spec Kit-Native and Composable
- Added sections:
  - Product and Ecosystem Requirements
- Modified sections:
  - Architecture Documentation Standards
  - Development Workflow and Quality Gates
- Removed sections: None
- Follow-up TODOs: None
-->
# Concorde Constitution

## Core Principles

### I. Concorde Is the Workflow Product and Its Proving Ground
Concorde's primary product MUST be a repeatable workflow that joins Spec Kit's feature-oriented
development lifecycle to hierarchical architecture authoring, review, validation, and publication.
Project success requires installable integration artifacts and an end-to-end usable workflow; a
reference document, standalone diagram set, or bespoke demonstration alone is insufficient.

Concorde MUST develop itself with the same architecture, feature, scenario, contract, traceability,
and evidence rules it provides to users. When an unfinished Concorde capability cannot yet enforce a
required rule, maintainers MUST apply the rule manually, record the tooling gap as planned work, and
migrate the affected artifact once the capability exists. A milestone MUST NOT be declared complete
while a bootstrap gap needed to demonstrate that milestone remains unresolved. Self-application is
the acceptance test that the workflow is practical rather than merely aspirational.

### II. Spec Kit-Native and Composable
Concorde MUST integrate through Spec Kit's supported ecosystem mechanisms: presets for composing
architecture-aware artifact structure and guidance, extensions for commands and lifecycle behavior,
and a bundle that distributes the compatible pieces together. Concorde MUST extend the normal Spec
Kit workflow rather than replace its feature specification, clarification, planning, task, and
implementation responsibilities with a parallel system.

Integrations MUST use public, versioned Spec Kit extension and preset contracts where available. A
fork or incompatible orchestration layer is permitted only when a recorded prototype demonstrates
that supported mechanisms cannot satisfy a named requirement, and the decision includes compatibility
impact and a migration path back to the ecosystem. Concorde-specific behavior MUST remain composable
with other presets and extensions and MUST fail with actionable diagnostics when compatibility cannot
be maintained. This constraint makes Concorde adoptable within the Spec Kit ecosystem instead of
becoming an isolated workflow.

### III. Recursive, Bounded Architecture
The project MUST be modeled as a hierarchy rooted at the project module. Every module MUST have
one clear responsibility, and every declared submodule MUST be architecturally meaningful. A module view
MUST show the current module's features and boundary contracts, its immediate submodules and their
boundary contracts, relevant external actors, and connections among those visible participants. It
MUST NOT expose child features, grandchildren, or deeper implementation details. Selecting a child
MUST repeat the same view with that child as the current module. This one-level visibility rule keeps
architecture comprehensible at project scale and gives agents a bounded context for each task.

### IV. Explicit Ownership and Feature Alignment
Every feature MUST have a stable ID, an observable outcome, and exactly one providing module at its
current abstraction level. Behavior spanning multiple modules MUST be owned by their nearest common
parent and refined by features in participating child modules. A lower-level feature MUST link to at
least one feature owned by its parent module unless it is explicitly marked internal with a rationale.
Refinement links MUST connect adjacent module levels, MUST be acyclic, and MAY express many-to-many
realization. Every feature MUST include a representative scenario unless the feature records why an
example would not improve understanding. This alignment makes placement and decomposition
reviewable before implementation choices harden into structure.

### V. Contracts Govern Every Boundary
Every module MUST explicitly declare its provided and required contracts, including an explicit empty
set when none exist. Each contract MUST have a stable ID, owner, provided or required role, flow
direction, counterparties or audience, obligations, failure semantics, compatibility expectations,
and validation evidence. Every feature MUST identify at least one provided contract through which it
is available and all required contracts on which it depends. Every scenario interaction that crosses
a module boundary MUST reference its governing contract.

A contract MUST use either a commonly adopted format or a custom programmer-readable serialized
format. A commonly adopted format MUST name its relevant version, link to its authoritative
definition, and summarize the information exchanged. A custom format MUST include a normative schema
or grammar, complete field semantics, compatibility rules, at least one representative example, and
evidence that examples and implementations conform. Opaque or undocumented payloads are prohibited.
Contract changes MUST be reviewed as potential feature and compatibility changes because boundary
obligations, not internal details, are the promises on which other modules may rely.

### VI. One Authority per Fact, Traceable Everywhere
Concorde MUST maintain architectural and behavioral intent in version-controlled, machine-readable
sources without duplicating canonical meaning. Module, feature, contract, scenario, constraint, and
decision prose belongs in Markdown. Module-level structure and ordered scenario interactions belong
in Archify JSON. Normative contract representations belong in their referenced standard definitions
or checked-in custom schemas and examples. Code records the actual implementation, and tests record
executable evidence. Archify HTML, Docusaurus pages, indexes, traceability reports, and validation
reports MUST be reproducible generated outputs and MUST NOT be edited as sources.

Stable IDs MUST connect all maintained sources, generated projections, implementation locations, and
test evidence. When artifacts disagree, tooling and documentation MUST expose the disagreement rather
than silently selecting one artifact as universally correct. Unknown or missing implementation
evidence MUST be reported as unknown. This separation preserves clear authority while allowing users
and agents to trace intent through structure to evidence.

### VII. Deterministic Validation and Reviewed Evidence
Validation, rendering, documentation builds, freshness checks, and cross-reference checks MUST be
deterministic and MUST NOT require an LLM. Every architecture change proposed or authored by an AI
MUST receive human review and pass applicable validation before it is accepted as project intent.
Tests MUST verify changed behavior, contract conformance, hierarchy integrity, scenario boundaries,
and generated-output freshness in proportion to the change. A successful architecture check MUST NOT
be presented as proof that the implementation is correct; code and test evidence remain distinct.
These gates make AI-assisted changes reviewable and reproducible without granting generated artifacts
unearned authority.

## Product and Ecosystem Requirements

- Concorde MUST ship as an installable Spec Kit bundle containing one or more Concorde presets and
  extensions that provide the supported end-to-end workflow. Each distributable part
  MUST declare its responsibility, version, dependencies, and compatibility expectations.
- Presets MUST compose Concorde metadata and architecture-aware guidance into Spec Kit artifacts
  through the normal template-resolution stack. They MUST NOT create a second canonical feature
  specification solely for Concorde.
- Extensions MUST provide the lifecycle operations that do not belong in static templates, including
  architecture validation, bounded context retrieval, diagram rendering, documentation publication,
  and workflow integration. Each operation MUST have deterministic inputs, outputs, and failure
  behavior even when an agent assists with authoring.
- Spec Kit MUST remain authoritative for feature specification, clarification, planning, task
  generation, implementation, and convergence. Concorde MUST own module and feature hierarchy,
  boundary contracts, one-level architecture views, structural traceability, and publication.
- Archify MUST remain the rendering and validation boundary for maintained architecture JSON, while
  Docusaurus MUST remain a generated read model. Adapters MUST preserve those ownership boundaries and
  MUST NOT duplicate their canonical inputs.
- Every supported Spec Kit version MUST be stated explicitly and covered by an automated fixture that
  installs the bundle and exercises the supported workflow. Unsupported or incompatible versions MUST
  stop with an actionable diagnostic rather than produce partially composed artifacts.
- Ecosystem decisions that constrain compatibility or composition MUST be documented as architectural
  decisions and validated with a prototype before they become irreversible dependencies.

## Architecture Documentation Standards

- Every module, feature, scenario, and contract MUST have a unique, stable ID, and all references
  MUST resolve.
- Concorde-managed architecture sources MUST mirror the declared architecture hierarchy directly or
  through an explicit deterministic path mapping. They MUST NOT require a document for every class,
  function, or call edge or duplicate a canonical Spec Kit feature specification.
- Every non-leaf module MUST declare its immediate submodules and maintain one valid Archify JSON view
  for that level. Module containment and feature-refinement graphs MUST be acyclic.
- A scenario MUST use only the current module, its immediate submodules, and permitted external actors
  as participants. Each documented scenario MUST resolve to its module-level architecture view unless
  it is explicitly marked prose-only.
- Custom contract examples MUST validate against their normative schema or grammar. Contract format,
  schema, semantics, examples, affected feature references, and evidence MUST change together.
- Markdown and Archify JSON MUST divide responsibility by meaning. The same intent MUST NOT require
  canonical maintenance in more than one location.
- Generated pages and diagrams MUST include source provenance and generator version, provide a textual
  representation for accessibility and search, and be reproducible from maintained sources.
- Architecture MUST document responsibilities, boundaries, contracts, and representative behavior;
  it MUST NOT become a duplicate inventory of the implementation.

## Development Workflow and Quality Gates

Every material change to Concorde MUST proceed through the Spec Kit lifecycle augmented by the
Concorde workflow available at that revision. The author MUST first identify the providing module and
abstraction level. Unclear ownership or boundary effects MUST be resolved before the implementation
plan is approved. The feature specification MUST then record parent refinement links, relevant
scenarios, immediate participants, governing provided and required contracts, and expected source and
test evidence. Affected module views and contract definitions MUST be updated before implementation is
treated as architecture-complete.

During bootstrap, a missing command or validator does not waive its governing rule. The change MUST
include the equivalent reviewable source artifact or manual validation record, plus a linked feature
or task for automating the gap. Once the corresponding Concorde capability exists, subsequent changes
MUST use it and the temporary manual path MUST be retired. Development evidence MUST therefore test
both the product behavior and its use within Concorde's own repository.

Planning and review MUST use only the bounded context required for the affected module levels. Review
MUST verify behavior, ownership, abstraction level, dependency direction, boundary contracts,
contract-format compatibility, one-level visibility, traceability, implementation evidence, and stale
generated artifacts. Any deliberate exception to a principle or standard MUST be documented in the
change with its scope, rationale, owner, expiry or reassessment condition, and migration path.

Before merge, all applicable deterministic validation, schema/example validation, contract tests,
behavioral tests, reference checks, Archify validation, and documentation freshness checks MUST pass.
Generated Archify HTML and the Docusaurus site MUST be rebuilt reproducibly in CI. A change is not
complete while maintained sources, implementation, tests, and generated projections contain an
unreported disagreement.

## Governance

This constitution is the highest-authority governance document for Concorde development. Feature
specifications, plans, tasks, implementation choices, review conventions, and generated guidance MUST
comply with it. When another project document conflicts with this constitution, this constitution
prevails until an amendment resolves the conflict.

An amendment MUST be proposed as a reviewed change to this file. The proposal MUST describe the
motivation, affected principles or sections, compatibility impact, required migration work, and the
semantic version bump. Approval requires explicit maintainer acceptance and successful validation of
the constitution. Amendments take effect when merged; affected templates and project artifacts MUST
be reconciled in the same change or tracked by named follow-up work with an owner.

Constitution versions follow semantic versioning. MAJOR increments remove or incompatibly redefine a
principle or governance obligation. MINOR increments add a principle or materially expand mandatory
guidance. PATCH increments clarify wording or make non-semantic corrections. The ratification date
records the first adoption; the last-amended date changes whenever normative content changes.

Every feature and architecture review MUST include a constitution compliance check. Reviewers MUST
reject unexplained violations, invisible boundary changes, duplicated canonical intent, or claims of
implementation agreement without evidence. Exceptions are temporary governance records, not silent
precedent, and MUST meet the documentation requirements in the workflow section. Maintainers MUST
review the constitution at least once per major release and whenever recurring exceptions indicate
that a rule no longer serves the project's goals.

**Version**: 1.1.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-19

<!--
Sync Impact Report
- Version change: 1.4.0 -> 2.0.0 (MAJOR: principle removed, principles restructured and redefined)
- Structure change: Core Principles split into two parts:
  - Part A "Workflow Principles" governs every project that adopts the Concorde workflow.
  - Part B "Project Principles" governs the Concorde project that builds the workflow's tooling.
- Removed principles:
  - II. Spec Kit-Native and Composable (demoted to a Project Constraints bullet; integration
    mechanism is a feature decision, not a constitutional principle)
- Added principles:
  - A.I Fast Human Comprehension at Every Level (new; states the human-spec interaction goal)
  - A.II Complete Beneath the Surface (new; absorbs "One Authority per Fact")
  - A.III Architecture-Driven, Not Only Feature-Driven (new; absorbs "Recursive, Bounded
    Architecture" and "Explicit Ownership and Feature Alignment")
- Modified principles:
  - V. Contracts Govern Every Boundary -> A.IV Contracts Are Human-Readable Promises
  - VII. Deterministic Validation and Reviewed Evidence -> A.V Deterministic Validation,
    Human-Reviewed Evidence
  - I. Concorde Is the Workflow Product and Its Proving Ground -> split into B.I Concorde Ships a
    Usable Workflow and B.II Concorde Develops Itself with Concorde
- Removed sections: Product and Ecosystem Requirements (replaced by shorter Project Constraints);
  Architecture Documentation Standards (reduced to Workflow Standards)
- Detail relocated out of the constitution (now framework documentation / feature specs):
  feature-diagram `core`/`supplemental` role mechanics, `diagrams/` directory layout, contract
  field inventory, Spec Kit version fixture policy, adapter ownership boundaries.
- Feature placement redefined (A.III): a feature is specified at one level of the hierarchy but
  MAY be realized by several modules; "exactly one providing module" and "nearest common parent
  ownership" are dropped. One-level visibility becomes the default practice (SHOULD), and a
  level MAY show a submodule's features when that makes the level clearer.
- Follow-up TODOs:
  - Reconcile preset/extension guidance that cites old principle numerals (I-VII) with the new
    A.I-A.V / B.I-B.II identifiers.
  - `speckit.concorde.feature.create` and `feature.select` assumed one providing module per feature
    and were removed on 2026-08-27; features are now created through the normal specify phase at
    their canonical path and selected through standard Spec Kit selection. The feature path layout
    and Protocol v3 `providing_module` field still reflect the old assumption and remain to be
    aligned with A.III.
-->
# Concorde Constitution

Concorde exists because AI now writes most code. The programmer's problem has shifted from writing
implementation to staying oriented: understanding what a project does, how it is structured, and
what its parts promise each other, without reading every line of code. This constitution has two parts.
Part A states the principles of the Concorde workflow, which every project adopting Concorde
follows. Part B states the principles of the Concorde project itself, whose job is to make Part A
practical through tooling. Part A is the purpose; Part B is the means.

## Part A: Workflow Principles

### A.I Fast Human Comprehension at Every Level
The specification MUST be a hierarchy with a stopping point at every level. A reader MUST be able
to stop at any module, understand what it does and how its visible parts interact, and go no
deeper. Each level MUST be understandable in minutes, not hours: it MUST combine a diagram (structure
and interaction), tables (inventories such as features, contracts, and submodules), and short prose
(responsibility, rationale, representative scenario). Long narrative documents are prohibited at the
level a human is expected to read; depth is reached by descending, not by scrolling.

Rationale: nobody reads long documents. The programmer who no longer writes the code still needs to
own the project, and ownership requires a representation that can be absorbed fast at the altitude
where the current question lives.

### A.II Complete Beneath the Surface
Although a human rarely reads the whole specification, the whole specification MUST exist. Every fact
needed to understand, extend, or verify the system MUST be recorded exactly once in a maintained,
version-controlled, machine-readable source, and MUST be reachable from the hierarchy by stable ID.
A human or agent starting at the root MUST be able to locate almost any necessary detail by
descending; a detail that can only be found by reading code is an incomplete specification.

Each kind of fact has one authority: prose intent in Markdown, structural and interaction models in
architecture JSON, contract shapes in their normative schema or standard definition, actual behavior
in code, and executable evidence in tests. Rendered diagrams, sites, indexes, and reports are
generated projections and MUST NOT be edited as sources. When sources disagree, tooling MUST expose
the disagreement rather than pick a winner; missing evidence MUST be reported as unknown.

Rationale: fast comprehension at the top is only trustworthy if the detail underneath is complete
and unambiguous. Completeness serves the agent, which reads everything; single authority serves both.

### A.III Architecture-Driven, Not Only Feature-Driven
Development MUST be driven by architecture as well as by features. A feature says what the project
or a module can do; the architecture says how the project is composed to do it. The project MUST be
modeled as a module hierarchy rooted at the project module. Every module MUST have one clear
responsibility, an explicit boundary, and declared immediate submodules that are each
architecturally meaningful. The purpose of every level is a good abstraction: the modules visible at
that level, their responsibilities, and their interactions MUST be chosen so that the level can be
understood on its own terms and reasoned about without the levels below.

Features are realized through modules. Every feature MUST have a stable ID, an observable outcome,
and exactly one place in the hierarchy where it is specified: the level at which every module it
uses is visible. A feature MAY be realized by a single module or by combining several modules and
lower-level features; it need not be owned by any one module. Where a feature is refined by features
at the next level down, the refinement links MUST connect adjacent levels and MUST be acyclic.

A level's view shows the current module, its features and boundary contracts, its immediate
submodules with their features and boundary contracts, the relevant external actors, and the
interactions among them. It SHOULD NOT descend further: grandchildren and implementation detail
belong to the levels below, and selecting a submodule produces the same kind of view with that
submodule as the current module. A level MAY show selected detail from below when that makes the
level clearer, provided the detail remains authoritative at its own level. This bounded view is what
makes A.I possible for humans and gives agents a bounded context for every task.

Rationale: the central task of architecture is making a good abstraction at each level. A list of
features does not tell a human how the system hangs together, and it does not tell an agent where
new behavior belongs; structure and interaction must be first-class.

### A.IV Contracts Are Human-Readable Promises
Every module boundary MUST be governed by explicit contracts, and every module MUST declare its
provided and required contracts (an explicit empty set is a valid declaration). A contract MUST be
presentable to a human without reading the implementation: it MUST state who provides and who
consumes it, the direction of flow, the data structure exchanged and what information that structure
encodes, the obligations of each side, and what happens on failure. Every feature MUST name the
provided contract(s) through which it is reachable and the required contracts on which it depends.
Every scenario interaction that crosses a module boundary MUST reference its governing contract.

A contract MUST use either a commonly adopted format (named, versioned, linked to its authoritative
definition, with a summary of the information exchanged) or a custom format with a normative schema
or grammar, field semantics, and at least one conforming example. Opaque or undocumented payloads are
prohibited. Contract changes MUST be reviewed as potential feature and compatibility changes.

Rationale: contracts are the promises other modules rely on. If a human cannot read what a boundary
carries, the human cannot judge whether a change is safe, and the architecture view is decoration.

### A.V Deterministic Validation, Human-Reviewed Evidence
Validation, rendering, documentation builds, freshness checks, and cross-reference checks MUST be
deterministic and MUST NOT require an LLM. Every architecture change proposed or authored by an AI
MUST receive human review and pass applicable validation before it becomes project intent. Tests MUST
verify changed behavior, contract conformance, hierarchy integrity, and generated-output freshness in
proportion to the change. A passing architecture check MUST NOT be presented as proof that the
implementation is correct; structural validity and behavioral evidence remain distinct.

Rationale: AI-assisted changes are only trustworthy when they are reproducibly checkable and a
human has accepted them. Generated artifacts earn no authority by existing.

## Part B: Project Principles

### B.I Concorde Ships a Usable Workflow
Concorde's product MUST be a repeatable, installable, end-to-end workflow that lets a project live by
Part A: establishing the root, finding the owning level, creating and selecting features, retrieving
bounded context, validating architecture, and publishing comprehensible views. A reference document,
a diagram set, or a bespoke demonstration alone is insufficient. Every distributable part MUST declare
its responsibility, version, dependencies, and compatibility expectations, and every operation MUST
have deterministic inputs, outputs, and failure behavior even when an agent assists with authoring.

### B.II Concorde Develops Itself with Concorde
Concorde MUST develop itself under Part A using its own tooling. When an unfinished capability cannot
yet enforce a required rule, maintainers MUST apply the rule manually, record the gap as planned
work, and migrate the affected artifact once the capability exists. A milestone MUST NOT be declared
complete while a bootstrap gap needed to demonstrate it remains unresolved. Self-application is the
acceptance test that the workflow is practical rather than aspirational.

## Project Constraints

- Concorde currently integrates with Spec Kit as its host lifecycle: Spec Kit remains authoritative
  for feature specification, clarification, planning, tasks, implementation, and convergence, while
  Concorde owns module and feature hierarchy, boundary contracts, level views, traceability, and
  publication. How that integration is mechanically achieved (presets, extensions, bundles, supported
  versions) is a feature and architectural-decision concern, not a constitutional one, but any change
  MUST preserve the ownership split above and MUST fail with actionable diagnostics rather than
  produce partially composed artifacts.
- Rendering and publication tools (currently Archify for diagrams and Docusaurus for the site) are
  generated read models of maintained sources. Replacing a tool is permitted; making a generated
  output a source is not.

## Workflow Standards

- Every module, feature, scenario, and contract MUST have a unique, stable ID, and all references
  MUST resolve. Module containment and feature-refinement graphs MUST be acyclic.
- Architecture sources MUST mirror the declared hierarchy directly or through an explicit
  deterministic path mapping. They MUST NOT require a document per class, function, or call edge;
  architecture documents responsibilities, boundaries, contracts, and representative behavior, not
  a duplicate inventory of the implementation.
- Every non-leaf module MUST maintain one valid level view. A scenario SHOULD use only the current
  module, its immediate submodules, and permitted external actors as participants; deeper
  participants MUST be justified by clarity at that level.
- Every feature MUST include a representative scenario unless it records why an example would not
  improve understanding. A feature MAY own additional explanatory diagrams; at most one is its core
  component-interaction view, every diagram MUST have a complete textual counterpart, and no diagram
  may redefine behavior, ownership, or boundary obligations stated in the specification.
- Custom contract examples MUST validate against their schema. Contract format, semantics, examples,
  affected feature references, and evidence MUST change together.
- Generated pages and diagrams MUST carry source provenance and generator version, provide a
  textual representation, and be reproducible from maintained sources.

## Development Workflow and Quality Gates

Every material change MUST proceed through the host lifecycle augmented by the Concorde workflow
available at that revision. The author MUST first identify the level at which the feature is
specified and the modules that realize it; unclear placement or boundary effects MUST be resolved
before the implementation plan is approved. The feature specification MUST record parent refinement links, immediate participants,
governing contracts, representative scenarios, and expected source and test evidence. Affected module
views and contract definitions MUST be updated before implementation is treated as
architecture-complete.

Planning and review MUST use only the bounded context required for the affected levels. Review MUST
verify behavior, placement, abstraction level, dependency direction, boundary contracts, bounded
visibility, traceability, implementation evidence, and stale generated artifacts. Any deliberate
exception to a principle or standard MUST be documented with its scope, rationale, owner, expiry or
reassessment condition, and migration path.

Before merge, all applicable deterministic validation, contract and behavioral tests, reference
checks, and documentation freshness checks MUST pass, and generated outputs MUST be rebuilt
reproducibly in CI. A change is not complete while maintained sources, implementation, tests, and
generated projections contain an unreported disagreement.

## Governance

This constitution is the highest-authority governance document for Concorde. Feature
specifications, plans, tasks, implementation choices, review conventions, and generated guidance MUST
comply with it; where another project document conflicts, this constitution prevails until amended.

An amendment MUST be proposed as a reviewed change to this file describing motivation, affected
principles, compatibility impact, required migration work, and the semantic version bump. Approval
requires explicit maintainer acceptance. Amendments take effect when merged; affected templates and
artifacts MUST be reconciled in the same change or tracked by named follow-up work with an owner.

Versions follow semantic versioning: MAJOR removes or incompatibly redefines a principle or
governance obligation, MINOR adds a principle or materially expands mandatory guidance, PATCH
clarifies wording. The ratification date records first adoption; the last-amended date changes
whenever normative content changes.

Every feature and architecture review MUST include a constitution compliance check. Reviewers MUST
reject unexplained violations, invisible boundary changes, duplicated canonical intent, and claims
of implementation agreement without evidence. Exceptions are temporary records, not precedent.
Maintainers MUST review this constitution at least once per major release and whenever recurring
exceptions indicate a rule no longer serves the project's goals.

**Version**: 2.0.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-27

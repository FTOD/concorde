<!--
Sync Impact Report
- Version change: 5.2.0 -> 6.0.0 (MAJOR: Concorde becomes a standalone workflow and removes its host
  lifecycle, component composition, and host-owned control paths)
- Modified principles:
  - B.I Concorde Ships a Usable Workflow: one Concorde package now owns commands, templates, runtime,
    installation, and agent projection end to end.
  - B.II Concorde Develops Itself with Concorde: root package sources precede generated agent surfaces,
    without a duplicated host installation.
- Modified constraints: no external specification framework owns a lifecycle phase; retained
  `speckit-*` IDs are compatibility labels only.
- Modified standards: selection and constitution move under `.concorde/`; root `commands/`,
  `templates/`, `src/concorde/`, and `agent-assets/` are distribution authorities.
- Compatibility impact: old preset, extension, bundle, catalog, and `.specify/` installations are not
  read or updated by the native installer.
- Required migration: install the standalone package, review its ownership plan, then remove any old
  host-managed Concorde components separately.
-->
# Concorde Constitution

Concorde exists because AI now writes most code. The programmer's problem has shifted from typing the
implementation to staying oriented: understanding what a project does, how it is structured, and how
its parts collaborate, without reading every line. Part A states the workflow principles every
Concorde project follows. Part B states the principles of the Concorde project that makes that
workflow practical.

## Part A: Workflow Principles

### A.I Fast Human Comprehension at Every Module

The specification MUST be a recursive module hierarchy with a useful stopping point at every module.
A reader MUST be able to open that module's single `architecture.md`, understand its responsibility,
boundary, significant entities, immediate child modules, level-local features, and important
interactions, and stop without opening descendants or source code.

Each feature at that module MUST be understandable from its single durable
`features/<NNN-name>.md`: what the
module provides, how a consumer uses it, what can fail, and which architecture entities collaborate.
Diagrams and generated pages MAY improve orientation, but they never replace the textual entity,
relationship, interface, and usage definitions. Depth is reached by descending modules or following
stable entity/feature references, not by reconciling parallel summaries.

Rationale: one architectural entry point and one feature entry point at each level minimize both
reading time and disagreement. The reader should choose an altitude, not a document role.

### A.II Complete Architecture, Real Implementation

The maintained specification MUST completely describe the abstractions needed to understand,
extend, and safely change the system: module boundaries; architecturally significant entities;
stable identities and locators; structural, dependency, control, and data relationships; feature
interfaces; requirements; failures; and representative usage. A fact has one owning module or
feature and MUST be reachable by stable ID.

The specification MUST NOT duplicate the implementation. Source code at the checked-out revision is
the authority for actual algorithms, private helpers, and implementation detail. Tests and
deterministic checks are the evidence for bounded claims about that code. A module architecture
inventories modules plus exported, boundary-visible, entry-point, orchestration, schema, shared-state,
or otherwise architecture-significant entities; it need not list every private symbol or call.

Generated diagrams, sites, indexes, knowledge graphs, reports, and delivery results are disposable
projections. Temporal plans, tasks, checklists, research, and validation logs live only in the active
feature attempt. When specification, code, tests, or projections disagree, tooling exposes the
disagreement instead of manufacturing another narrative authority.

Rationale: completeness means the architecture's concepts and promises are explicit, while the code
remains the most precise account of implementation. Rewriting code in prose creates stale truth.

### A.III Architecture Is a Typed Entity and Relationship Model

The project MUST be modeled as an acyclic tree of modules rooted at the configured project module.
Every module has exactly one parent except the root, one clear responsibility, one explicit boundary,
one `architecture.md`, zero or more immediate child modules, and zero or more level-local features.
Modules are the only hierarchical specification unit.

Each module architecture MUST define its architecturally significant entities and state what each
entity is. Preferred types include module, directory, file, script, program, function or method,
class, interface or type, configuration, schema, endpoint or command, service, pipeline, resource,
data store, test surface, document, external system, and explicitly defined project-specific types.
Each entity has a stable identity distinct from its mutable code locator, one owning module, a
non-circular definition, and important typed relationships.

Relationships MUST be directed and semantically named. The vocabulary SHOULD reuse clear code and
system relationships such as contains, declares, imports, exports, calls, inherits, implements,
depends on, provides, requires, routes to, reads from, writes to, transforms, validates, triggers,
configures, documents, tested by, generates, and realizes. Project-specific predicates MUST define
their direction and meaning. Interactions explain ordered or conditional collaborations over those
entities and relationships.

A parent architecture exposes each immediate child module as one bounded entity and MUST NOT copy
the child's internal inventory. Supporting views show only what is useful at the current level;
grandchildren and child internals remain owned below.

Rationale: architecture is not a folder list or a feature catalog. Its core is the identity and type
of the parts plus the relationships that make those parts a system.

### A.IV Feature Interfaces Are Human-Readable Promises

A feature is one module-level functionality or interface specified exactly once in
`features/<NNN-name>.md`. Features MUST NOT contain features. Composition, refinement, or
dependency among features is expressed through stable related-feature references and MUST remain
acyclic where directional.

Every externally meaningful entry point or promise MUST be defined inside the feature design that
exposes it. The interface definition states the consumer and provider, direction, entry point,
inputs and the information they encode, outputs, obligations, failure behavior, compatibility, and
implementing architecture entity references. A commonly adopted machine format MAY be linked by
name and version; custom serialized behavior MUST still have readable field semantics and at least
one conforming example in the design. Opaque payloads are prohibited.

Each feature design MUST include an architecture zoom: the visible entities it uses and how they
collaborate for representative usage. The feature may add behavioral detail but MUST NOT redefine an
entity's identity, type, ownership, or architecture-level relationship. If a needed entity does not
exist, its owning module architecture changes in the same reviewed lifecycle.

Rationale: an interface belongs beside the functionality a consumer chooses. Separating promises
into architecture contract inventories obscures how the module is actually used.

### A.V Deterministic Validation, Risk-Proportional Review

Validation, rendering, documentation builds, freshness checks, cross-reference checks, workspace
resolution, and delivery eligibility MUST be deterministic and MUST NOT require an LLM. AI-authored
architecture or feature changes require explicit maintainer direction and applicable validation.
An explicitly invoked fast loop or completed normal delivery may apply within its bounded authority
without a redundant second approval.

The fast-loop exception applies only when deterministic preflight establishes all of the following:

- every affected feature has durable required behavior and no active attempt;
- the change creates or restructures no module or feature, changes no responsibility, entity
  ownership, dependency direction, public interface, or project-level compatibility policy;
- affected architecture, feature designs, code, tests, and generated projections are bounded and
  reconciled; and
- proportionate behavioral, hierarchy, entity-reference, interface, freshness, and documentation
  checks pass.

The delivery exception applies only when one selected feature has a real active attempt with at
least one recognizable task, every task and existing checklist item is complete and well formed,
applicable validation has passed, and the maintainer explicitly invokes delivery. Delivery verifies
a current digest and safe canonical paths, removes exactly that selected stable-ID control attempt,
and leaves module architecture, feature files, `.concorde/reflections/log.md`, source code, tests,
and other feature attempts
byte-identical. It MUST NOT create an implementation narrative or amend architectural intent.
Ineligibility, ambiguity, unsafe paths, failed validation, or stale inputs preserves the full attempt.

Rationale: authority is trustworthy when scope and evidence are explicit. Removing completed working
memory is a lifecycle transition, not a reason to create another version of implementation truth.

## Part B: Project Principles

### B.I Concorde Ships a Usable Workflow

Concorde's product MUST be a repeatable, installable, end-to-end workflow that lets a project live by
Part A: initialize a root architecture, find a feature's module, retrieve bounded context, specify a
feature and its interface, plan and execute against code reality, validate the entity model, deliver
the attempt, and publish comprehensible views. Every distributable part MUST declare responsibility,
version, dependencies, compatibility, deterministic inputs, outputs, and failure behavior.

### B.II Concorde Develops Itself with Concorde

Concorde MUST develop itself under Part A using its own tooling. When a capability cannot yet enforce
the new profile, maintainers apply the rule manually, record the bootstrap compromise in the one
project reflection log, and migrate the artifact in the same prototype milestone. Self-application
is the acceptance test that the workflow is practical rather than aspirational.

## Project Constraints

- Concorde owns its complete lifecycle: constitution, specification, clarification, planning, tasks,
  implementation, convergence, bounded context, validation, delivery, installation, and publication.
  No external specification framework is an authority or runtime dependency. The `speckit-*` command
  IDs remain temporarily as user-facing compatibility names and MUST NOT imply external ownership.
- Canonical distributable sources are the root `commands/`, `templates/`, `src/concorde/`, `scripts/`,
  and `agent-assets/` paths plus `concorde.json`. Generated Codex/Claude surfaces are projections.
- Rendering and publication tools (currently Archify and Docusaurus) are generated read models.
  Replacing a tool is permitted; making a generated output a source is not.
- Understand Anything may supply adapter types and relationships for exploration, but Concorde's
  recursive modules, stable entity identities, feature ownership, and authority boundaries remain
  normative. A UA layer or path-derived node ID is not a Concorde module or durable entity identity.

## Workflow Standards

- Every module, architecture entity, feature, interface, scenario, and reflection MUST have a stable
  identity in its owning scope, and every reference MUST resolve. Module containment and directional
  feature relationships MUST be acyclic.
- Canonical module paths are `<module>/architecture.md` and `<module>/modules/<child>/`; canonical
  feature paths are `<module>/features/<NNN-name>.md`. A module contains no workflow-control child.
  Temporal work lives at `.concorde/attempts/<stable-feature-id>/` and is absent when that feature has
  no active attempt; the tracked process log lives at `.concorde/reflections/log.md`.
- Stable feature IDs, not filenames or module paths, key attempts and MUST use a safe lowercase
  qualified grammar. A planned feature with no authored ID exposes no attempt path; specification
  reruns workspace resolution after front matter before creating its checklist.
- A module architecture MUST declare its immediate module and feature inventory, directly owned
  entity inventory, typed directed relationships, and representative interactions. Entity locators
  resolve to real project paths/symbols or state why the entity is external or conceptual.
- A feature design MUST state outcome, scope, related features, representative usage, requirements,
  edge/failure behavior, embedded interfaces, and its architecture zoom.
- Architecture-owned diagrams are optional maintained explanations, MUST be referenced by the owning
  `architecture.md`, and MUST carry textual counterparts and reproducible output provenance. A
  diagram never defines an entity, relationship, feature requirement, or interface independently.
- Interface format, semantics, examples, affected feature references, implementing entity links, and
  evidence change together.
- Generated pages and diagrams carry source provenance and generator version, provide a textual
  representation, and are reproducible from maintained sources.
- Structural conformance is not implementation proof. Completion claims name the executable tests
  or checks and the exact scope each result establishes.

## Development Workflow and Quality Gates

Every material change proceeds through the Concorde lifecycle. Specification first
identifies the feature's module, related features, affected architecture entities, interface changes,
representative usage, and expected source/test evidence. Architecture changes are written in the
owning module; feature behavior and interfaces are written in the owning feature design.

Planning and review use the selected feature design, bounded module architecture and ancestry,
bounded related-feature summaries, current code/tests, and the selected temporal attempt. They MUST
NOT depend on feature abstracts, accepted-realization prose, module summary/design pairs, nested
subfeature workspaces, or specification-owned contract directories.

Tasks explicitly reconcile every affected architecture, feature interface, code path, test, and
generated projection. Implementation records compact evidence in the attempt before completing each
task. Deliberate compromises or difficult choices are appended to `.concorde/reflections/log.md` with their
scope, observed limitation, current action, and improvement path; they do not block a prototype when
a safe bounded assumption permits progress.

Before delivery, all applicable deterministic hierarchy, layout, entity/reference, interface,
behavioral, package, documentation, and freshness checks pass. Delivery removes the complete attempt
and changes nothing else. A milestone is incomplete while maintained specifications, executable
reality, tests, and generated projections contain an unreported disagreement.

## Governance

This constitution is Concorde's highest-authority governance document. Feature designs, plans, tasks,
implementation choices, review conventions, and generated guidance MUST comply with it; where
another project document conflicts, this constitution prevails until reconciled.

An amendment MUST describe motivation, affected principles, compatibility impact, required migration,
and the semantic version bump. Explicit maintainer direction for the change constitutes review; all
affected templates and artifacts are reconciled in the same milestone or named in the reflection log
with a concrete improvement path.

Versions follow semantic versioning. MAJOR removes or incompatibly redefines a principle, MINOR adds
or materially expands a mandatory obligation, and PATCH clarifies wording. Every feature and
architecture review includes a constitution check. Reviewers reject unexplained violations,
invisible boundary changes, duplicated canonical intent, and implementation claims without evidence.

**Version**: 6.0.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-09-02

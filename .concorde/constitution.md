<!--
Sync Impact Report
- Version change: 7.1.0 -> 7.2.0 (MINOR: adds mandatory principle A.VI, which requires module
  decomposition to follow business capability, use case, or axis of change rather than artifact type)
- Added principles:
  - A.VI Modules Follow Capabilities, Not Artifact Types: a module is defined by the capability it
    serves; artifact-type layers (all Skills, all scripts, all Operations, all models) and residual
    buckets (misc, common, shared) are invalid module boundaries; the root module holds only
    project-wide features; physical distribution directories never determine ownership.
- Modified principles:
  - B.II Concorde Develops Itself with Concorde: the repository re-partitions its own architecture
    into capability modules (understanding, lifecycle, reflections, capabilities, distribution,
    auto-docs) as the first application of A.VI.
- Modified standards: initialization, specification, planning, and analysis guidance check A.VI
  before creating or restructuring a module; deterministic validation reports artifact-type or
  residual module names as advisory findings.
- Compatibility impact: stable module IDs `module.concorde.skills`, `.operations`, `.runtime`, and
  `.workspace` are retired; their features and entities move to the owning capability modules with
  new stable IDs. No compatibility alias remains.
- Required migration: none for installed projects; projects that already partition by artifact type
  receive advisory validation findings and re-partition in a normal attempt.
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

### A.VI Modules Follow Capabilities, Not Artifact Types

Module decomposition MUST follow business capability, use case, or axis of change, so that the
things which change together are owned together. A module's responsibility MUST be one capability a
consumer could ask for, and its features MUST be use cases of that capability rather than inventories
of what the module happens to contain.

A module MUST NOT be defined by the kind of artifact it collects, such as every Skill, every script,
every Operation, every model, every controller, or every test, and MUST NOT be a residual bucket such
as `misc`, `common`, `shared`, or `utilities`. When one use case needs a Skill, a Tool, an Operation,
a template, and a schema, one module owns all of them. The root module holds only features that span
the whole project; a use case that belongs to one capability descends to that module.

Physical layout does not determine ownership. A distribution format may keep artifacts in flat
directories such as `skills/` or `operations/`; each artifact still belongs, through its stable
entity identity, to the capability module whose use case it realizes. Placing a new feature or
entity MUST start by naming the capability it serves; a candidate module whose only honest
responsibility sentence is "contains all X" is evidence that the partition is wrong.

Rationale: a reader looking for how the system does something opens one module and finds the whole
answer, and a change to one capability touches one module instead of every artifact-type layer. Type
layers scatter each use case across the tree and push every real feature to the root.

## Part B: Project Principles

### B.I Concorde Ships a Usable Workflow

Concorde's product MUST be a repeatable, installable, end-to-end workflow that lets a project live by
Part A: initialize a root architecture, find a feature's module, retrieve bounded context, specify a
feature and its interface, plan and execute against code reality, validate the entity model, deliver
the attempt, and publish comprehensible views. Its capability structure MUST have three explicit
levels: Scripts expose bounded deterministic Tools; canonical leaf Skills invoke Tools and declare
exposure plus integration-neutral effects; and paired LangGraph Operations compose two or more
ordered direct Skills or public Operations with state, ordering, branching, retries, gates, or other
controls. Operation composition MUST be acyclic and nested Operations MUST remain opaque to parents.
Every distributable part MUST declare responsibility, version, dependencies,
compatibility, deterministic inputs, outputs, and failure behavior.

Each leaf Skill MUST have exactly one canonical `skills/<name>/SKILL.md` authority, MUST embed no
multi-Skill loop, and MUST declare public/internal exposure plus exact read/write/network/credential
effects whenever an Operation composes it. Public leaves remain independently invocable; internal
leaves are package/runtime implementation capabilities and MUST NOT project to users. Each Operation MUST have exactly one
`operations/<name>/operation.py` execution authority and one associated `SKILL.md` invocation and
behavioral contract and MUST be public. Installation MUST project public leaf Skills and Operation
skills into the user's agent Skill namespace while retaining every packaged leaf and paired Python
graph in the installed framework.

### B.II Concorde Develops Itself with Concorde

Concorde MUST develop itself under Part A using its own tooling. When a capability cannot yet enforce
the new profile, maintainers apply the rule manually, record the bootstrap compromise in the one
project reflection log, and migrate the artifact in the same prototype milestone. Self-application
is the acceptance test that the workflow is practical rather than aspirational. Concorde's own
architecture is therefore partitioned by capability under A.VI: understanding, lifecycle,
reflections, capabilities, distribution, and auto-docs.

## Project Constraints

- Concorde owns its complete lifecycle: constitution, specification, clarification, planning, tasks,
  implementation, convergence, bounded context, validation, delivery, installation, and publication.
  No external specification framework is an authority or runtime dependency. Canonical public
  capability names use the `concorde-*` Skill namespace and MUST NOT imply external ownership.
- Canonical distributable sources are root `scripts/`, `skills/`, `operations/`, `templates/`,
  `src/concorde/`, and `agent-assets/` plus Package Manifest 2 in `concorde.json`. Generated
  Codex/Claude surfaces are projections.
- Operation is reserved for a LangGraph that composes at least two ordered direct capabilities, each
  a canonical leaf Skill or another public paired Operation. Composition cycles are invalid. Initialization,
  context retrieval, exploration, validation, delivery, and other bounded deterministic runtime
  actions are Tools, even when invoked through a CLI subcommand or Skill.
- A maintained Operation Python file without its associated Markdown skill, a leaf Skill that embeds
  multi-Skill graph topology, or a canonical capability retained in a legacy flat/example layout is
  invalid. Concorde MUST NOT ship a compatibility reader, alias source, or implementation shim for the
  retired layout.
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
- Package Manifest 2 MUST inventory leaf Skills and paired Operations separately, require globally
  unique safe names across both sets, and bind each Operation's Markdown `capabilities` declaration
  to its Python entry point, literal ordered topology, and exact per-occurrence policies without
  importing arbitrary graph code during validation. Internal leaves remain in the leaf inventory but
  are absent from public projections.
- Workspace Protocol 13, Delivery Proposal 9, Tool result envelopes, capability-surface status schema
  2, and reflection-triage/v4 MUST use `tool` for bounded deterministic actions. Operation metadata is
  reserved for paired LangGraph execution.
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

Leaf Skills and Operations MUST resolve only the context their contracts authorize. An Operation
MUST load canonical direct capability bodies rather than duplicate or flatten them, preserve declared
stage/capability order and nested boundaries, make state/control transitions inspectable, and stop or
route failures as its paired skill documents. Before every direct leaf launch, trusted code MUST
resolve concrete non-symlink paths, prove the Operation binding narrows the leaf's effects, render a
supported native or equivalently narrow outer sandbox configuration, and require a matching receipt.
Multi-leaf stages MUST NOT share the union of their effects. Missing, widened, unsafe, or unenforceable
policy and Tool failures remain explicit and MUST NOT silently fall through to another source.

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

**Version**: 7.2.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-09-04

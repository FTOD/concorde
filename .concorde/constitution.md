<!--
Sync Impact Report
- Version change: 8.0.0 -> 8.1.0 (MINOR: adds a mandatory committed-base isolated-worktree
  boundary for every agent-authored mutation)
- Added principle:
  - A.VII Agent Mutations Start in Isolated Worktrees: read-only work may inspect the primary
    worktree, but planning, attempt/control creation, project edits, and external mutations default
    to a unique linked worktree created from the primary worktree's exact committed HEAD.
- Modified principles and standards:
  - B.II Protocol evolution now binds to an exact committed base and excludes, preserves, and does
    not require cleanliness of unrelated primary-worktree dirty state.
  - Workflow and development gates reject staged, unstaged, untracked, or ignored primary-worktree
    content as implicit agent input and require an explicit primary-mutation override.
- Compatibility impact: agent mutation in a primary worktree is no longer the default. Existing
  mutating Skills, Operations, and deterministic entry points must move to a linked worktree or carry
  an explicit maintainer-authorized primary-worktree override; read-only capabilities are unchanged.
- Required migration: reconcile workflow/lifecycle/reflection/capability specifications, canonical
  and projected agent guidance, Git worktree preflight code/tests, architecture diagrams, and resolve
  R-045 through the single Protocol cutover commit.
- Deferred placeholders: none.
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
dependency among features is expressed through stable related-feature references that name their
relation (`composes`, `refines`, `depends_on`, an inverse form, or symmetric `relates_to`; a plain
ID means `relates_to`) and MUST remain acyclic where directional.

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
and leaves module architecture, feature files, `.concorde/reflections/`, source code, tests,
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

### A.VII Agent Mutations Start in Isolated Worktrees

Read-only inspection MAY run in a repository's primary Git worktree. Any coding-agent request that
may mutate project or external state MUST establish its Git boundary before planning, persisting a
feature selection, creating an attempt/checklist/reflection, or performing any other write. Unless
the maintainer explicitly authorizes mutation of the primary worktree for that exact request, the
agent MUST resolve the primary worktree's committed `HEAD`, create a unique branch and linked
worktree at that exact commit, and continue the complete request there. An agent already assigned an
isolated worktree MUST remain there and MUST NOT create a nested worktree merely to enter another
phase. Independently mutating agents MUST NOT write concurrently to one worktree.

Every staged, unstaged, untracked, or ignored path in the primary worktree is outside the default
request authority and MUST be treated as another programmer's state. An agent MUST NOT use those
bytes as planning or implementation input, stash/apply them, copy them into its worktree, commit
them, reset them, clean them, or otherwise import or alter them. If required input is absent from the
committed base, the agent stops and reports the missing input. A generic request to plan, implement,
or fix something is not authorization to mutate the primary worktree; the exception must name that
boundary explicitly. A non-Git checkout likewise requires explicit current-directory mutation
authorization because no committed linked-worktree base exists.

The worktree remains bound to its captured base until integration. If the integration branch
advances, reconciliation occurs in isolation and all applicable validation reruns before merge.
Merge, worktree removal, and branch deletion remain explicit integration/cleanup actions and MUST
preserve unrelated primary-worktree state.

Rationale: a dirty primary worktree commonly belongs to another programmer. Treating its transient
bytes as authoritative input creates hidden coupling, lost files, and unsafe cleanup; an immutable
committed base plus one isolated worktree makes ownership and review explicit.

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

### B.II Concorde Self-Applies and Explicitly Evolves Its Protocol

Concorde MUST develop every normal change under Part A using its own tooling. Self-application is the
acceptance test that the workflow is practical rather than aspirational. Concorde's own architecture
is therefore partitioned by capability under A.VI: understanding, lifecycle, reflections,
capabilities, distribution, and auto-docs.

Concorde is also the only project that defines, implements, and consumes the complete normative
Concorde Protocol. Every change to that Protocol's semantics MUST use the root Protocol-evolution
feature rather than an attempt, fast loop, standard development loop, or delivery. The maintainer
MUST explicitly authorize the cutover from an exact committed checkpoint; the change MUST be authored
directly in an isolated Git worktree, reconcile every affected maintained and executable authority,
pass complete target-state validation, and merge as one reviewable cutover commit. No active
Protocol-evolution attempt may exist. A failed cutover leaves the base checkout unchanged and is
abandoned or reverted through Git. A code or test fix that restores already specified Protocol
semantics remains normal lifecycle work. Staged, unstaged, untracked, or ignored state in the
primary worktree is neither cutover input nor a preflight blocker; it remains untouched and absent
from the isolated target.

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
  no active attempt; tracked process memory lives in `.concorde/reflections/<bucket>/R-NNN.md` with a
  metadata-only allocation index.
- Every agent-authored mutation uses A.VII's committed-base isolated-worktree boundary before
  planning or control-state creation. Primary-worktree dirty bytes never extend a feature's input
  authority, and only an explicit maintainer instruction may enable the primary-worktree override.
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
- A `related_features` entry is `{id, relation}` with `relation` from `composes`, `refines`,
  `depends_on`, `composed_by`, `refined_by`, `depended_on_by`, or `relates_to`; a plain ID is
  `relates_to`. After inverse forms normalize, each directional family MUST be acyclic, validation
  MUST report unknown relations and cycles, and publication MUST derive one typed feature graph from
  these entries and interface ownership as a projection with a textual counterpart.
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
- Concorde Protocol is the complete normative process by which a selected feature is resolved,
  permission-bounded, specified, planned, executed, validated, reflected on, and delivered, together
  with the Source Profile and control-state rules that make those phases authoritative. Feature
  Workspace Protocol is one serialized component of Concorde Protocol, not its synonym. Every
  Concorde project consumes the Protocol; only the Concorde repository defines, implements, and
  self-applies it.
- Structural conformance is not implementation proof. Completion claims name the executable tests
  or checks and the exact scope each result establishes.
- No stored status substitutes for verification. A feature design carries no evidence-status field;
  every attempt to resolve a reflection re-verifies the recorded problem against the current
  checkout before acting, and a problem that no longer reproduces is dismissed, never implemented.

## Development Workflow and Quality Gates

Every material change except normative Concorde Protocol evolution proceeds through the Concorde
lifecycle inside the A.VII worktree boundary. Before specification, planning, attempt creation, or
any other mutation, the acting agent creates or enters its committed-base isolated worktree unless
the maintainer explicitly authorized primary-worktree mutation. Specification first
identifies the feature's module, related features, affected architecture entities, interface changes,
representative usage, and expected source/test evidence. Architecture changes are written in the
owning module; feature behavior and interfaces are written in the owning feature design.

Normative Concorde Protocol evolution follows B.II instead: it creates no attempt or checklist,
invokes no lifecycle or delivery capability, and changes the complete specification/code/test/control
boundary directly in one isolated worktree created from the exact committed base. Uncommitted primary
state is excluded and preserved. The target checkout MUST pass all applicable deterministic
validation before its single cutover commit is eligible to merge.

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
task. Deliberate compromises or difficult choices are recorded as one
`.concorde/reflections/<bucket>/R-NNN.md` document with their scope, observed limitation, current
action, and improvement path; they do not block a prototype when a safe bounded assumption permits
progress.

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

**Version**: 8.1.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-09-04

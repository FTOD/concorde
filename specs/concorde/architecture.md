---
id: module.concorde
kind: module
parent: null
modules:
  - module.concorde.understanding
  - module.concorde.lifecycle
  - module.concorde.reflections
  - module.concorde.capabilities
  - module.concorde.distribution
  - module.concorde.auto-docs
features:
  - feature.concorde.workflow
  - feature.concorde.define-project-ontology
  - feature.concorde.evolve-protocol
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-system-overview.html
  - source: diagrams/module-collaboration.json
    kind: architecture
    output: generated/architecture/concorde-module-collaboration.html
  - source: diagrams/operation-dataflow.json
    kind: dataflow
    output: generated/architecture/concorde-operation-dataflow.html
---

# Architecture: Concorde

## Responsibility

Provide a standalone, module-centered development system in which durable architecture and feature
intent, executable reality, evidence, temporal work state, and a permission-bounded capability
structure have explicit, non-overlapping authority, every agent-authored mutation begins from one
committed-base isolated Git worktree, and every capability a maintainer or coding agent needs is
owned by exactly one module.

## Boundary

Concorde owns six capability modules: understanding a project, changing one feature through its
lifecycle, recording and triaging reflections, running any capability on a coding agent,
distributing and installing the package, and publishing the documentation read model. It owns the
project-wide file roles those modules share (package manifest, specification, control state, source
code, tests, templates, generated projections), the Package Manifest 2 identity, the complete
normative Concorde Protocol, and the isolated process by which this repository evolves that Protocol
without self-hosting the cutover in an attempt. It does not own a coding-agent/model runtime, a
project's own virtual environment, project product code, Archify rendering, Docusaurus internals, or
Understand Anything graph semantics.

## Project Concept Model

**Operation is Concorde's core execution concept.** It is a stable named callable unit with exactly
one associated Skill for an agent CLI and at least one executable Python script; one primary entry
point is designated. The Skill describes invocation and behavior, while Python executes it. A
particular invocation is separate from that reusable definition. A composite Operation additionally
declares its ordered/conditional children and the data each child consumes and produces.

The [Operation registry](#operation-registry) enumerates the three installed paired LangGraphs and
their concrete owners, entry points, and data contracts. Public leaf Skills remain leaf capabilities
in Package Manifest 2; an installed Skill name alone does not make a registered Operation.

The shared model below is project-owned; concrete Operations and their domain payloads stay owned
by the capability modules. Configuration expresses reusable project choices such as integration.
Runtime input expresses the current task, such as `feature_path`. The host derives workspace paths,
stable feature identity, and receipts. Typed results and explicit field mappings connect invocations.
Modules partition responsibility; directories locate implementations of this model.

**Realization boundary:** paired Operations and permission/completion receipts exist today. The
separate JSON configuration/input envelopes, project-wide Operation defaults, and typed domain
handoffs below are target contracts for runtime migration. They are not supported CLI examples.
The current/target review and owner map below identify that work explicitly.

## Operation Registry

This project-level registry contains exactly the Operation IDs in `concorde.json.operations`.
The manifest owns executable registration; the linked module architectures own the concrete
entities. Skill and Python paths below are canonical repository-relative sources; installed
Codex/Claude projections expose the same identities.

The registrations, source pairs, and nested calls exist today. **Configuration, input, and output
types are target JSON contracts**, with `@1` meaning `schema_version: 1`; each type links to its
field-definition authority. All three currently execute through the CLI/string request ABI.

| Operation ID | Owning module / concrete entity | Canonical Skill / primary Python script | Target configuration type | Target runtime input type | Target domain output type | Nested Operations |
|---|---|---|---|---|---|---|
| `concorde-plan` | [Lifecycle](modules/lifecycle/architecture.md): `module.concorde.lifecycle`; `entity.lifecycle.plan-operation` | `operations/concorde-plan/SKILL.md`; `operations/concorde-plan/operation.py` | [concorde-operation-configuration@1](modules/capabilities/features/002-provide-capability-surfaces.md#project-configuration-lifecycle) | [concorde-plan-context@1](modules/lifecycle/features/002-plan-attempt.md#target-planning-data-types) | [concorde-plan-result@1](modules/lifecycle/features/002-plan-attempt.md#target-planning-data-types) | None; its direct children are the internal leaf Skills `concorde-plan-context` then `concorde-plan-author`. |
| `concorde-standard-dev-loop` | [Lifecycle](modules/lifecycle/architecture.md): `module.concorde.lifecycle`; `entity.lifecycle.standard-dev-loop` | `operations/concorde-standard-dev-loop/SKILL.md`; `operations/concorde-standard-dev-loop/operation.py` | [concorde-operation-configuration@1](modules/capabilities/features/002-provide-capability-surfaces.md#project-configuration-lifecycle) | [concorde-standard-dev-loop-context@1](modules/lifecycle/features/006-standard-development-loop.md#target-standard-loop-data-types) | [concorde-standard-dev-loop-result@1](modules/lifecycle/features/006-standard-development-loop.md#target-standard-loop-data-types) | `concorde-plan`, after `concorde-specify` and before `concorde-tasks`; followed by `concorde-implement`, `concorde-validate`, and `concorde-deliver`. |
| `concorde-reflections-triage` | [Reflections](modules/reflections/architecture.md): `module.concorde.reflections`; `entity.reflections.triage-operation` | `operations/concorde-reflections-triage/SKILL.md`; `operations/concorde-reflections-triage/operation.py` | [concorde-operation-configuration@1](modules/capabilities/features/002-provide-capability-surfaces.md#project-configuration-lifecycle) | [concorde-reflections-triage-context@1](modules/reflections/features/001-record-and-triage-reflections.md#target-triage-data-types) | [concorde-reflections-triage-result@1](modules/reflections/features/001-record-and-triage-reflections.md#target-triage-data-types) | `concorde-plan` only for `action: implement`, `route: plan`, between analyze and tasks/implement/validate. The `fast-loop` route and other actions do not call a nested Operation. |

Each source pair has exactly one primary Python entry point. The shared managed launcher is
`scripts/run-operation.py`, declared by `concorde.json.operation_runtime.launcher`. Nested Operations
inherit the run's configuration snapshot; their exact input/result field mappings are in
[Operation Data Flow](#operation-data-flow). The internal Skill named `concorde-plan-context` and
the runtime input type with that spelling are separate identities.

Adding, removing, or renaming an Operation, changing its source pair or owner, or changing a data
contract or nested call requires updating this registry with the manifest and owning specifications.
An architecture review checks that every manifest Operation has exactly one row and every listed
source pair resolves to its registered ID.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.concorde.operation` | concept | Reusable named callable definition, owned by one capability module, exposed by one associated Skill and realized by one or more Python scripts with one primary entry point. | `concept:Operation definition` |
| `entity.concorde.operation-skill` | document | One Operation's canonical agent invocation/behavioral surface; installed Codex/Claude copies are projections, not additional definitions. | `concept:Operation Skill` |
| `entity.concorde.execution-script` | script | Executable Python authority realizing an Operation; script paths locate code but do not identify the Operation. | `concept:Operation execution script` |
| `entity.concorde.operation-configuration` | configuration | Target project-owned reusable Operation settings, established during initialization and snapshotted for a run; excludes task input and credentials. | `concept:Operation configuration` |
| `entity.concorde.runtime-input` | type | Target per-invocation caller data with a stable type ID/version, complete fields, and no ambient project-setting overrides. | `concept:Typed runtime input` |
| `entity.concorde.data-contract` | schema | A named versioned data definition owned by its providing feature, including fields, requiredness, constraints, and compatibility rules. | `concept:Operation data contract` |
| `entity.concorde.operation-invocation` | concept | One execution of one Operation definition in one host-bound workspace, with one configuration snapshot and one typed runtime input. | `concept:Operation invocation` |
| `entity.concorde.operation-result` | type | Target typed success/failure result of one invocation; separates domain data from execution/completion evidence. | `concept:Operation result` |
| `entity.concorde.artifact-reference` | type | Stable artifact identity, project-relative locator, and digest for data kept in its owning durable or temporal store. | `concept:Artifact reference` |
| `entity.concorde.data-handoff` | type | Explicit mapping of a successful producer result to one consumer input, bound to compatible contracts and the same selected work context. | `concept:Operation data handoff` |
| `module.concorde.understanding` | module | Knows what a project is: models it as a validated Profile 7 hierarchy, loads it deterministically, bounds one feature's context and permission paths, explores alignment with code evidence, and answers grounded questions. | `specs/concorde/modules/understanding/architecture.md` |
| `module.concorde.lifecycle` | module | Carries one selected feature from specification through permission-bounded planning, dependency-ordered tasks, reconciled implementation, deterministic validation gates, and cleanup-only delivery, including the bounded fast loop. | `specs/concorde/modules/lifecycle/architecture.md` |
| `module.concorde.reflections` | module | Records one tracked problem per file during workflow phases and triages it through the conditional permission-bounded reflection Operation until maintainer disposition closes it. | `specs/concorde/modules/reflections/architecture.md` |
| `module.concorde.capabilities` | module | Defines how every Concorde capability exists and runs on a coding agent: Tools, effect-declared Skills, paired Operations, host workspace receipts, task-policy enforcement, attested client bootstrap, typed semantic completion, and identical public projection into Codex and Claude. | `specs/concorde/modules/capabilities/architecture.md` |
| `module.concorde.distribution` | module | Packages, validates, installs, and updates Concorde while preserving identity, integrity, path safety, explicit ownership, and user-authored files. | `specs/concorde/modules/distribution/architecture.md` |
| `module.concorde.auto-docs` | module | Scaffolds and publishes validated module architectures, direct features, and architecture-owned diagrams as one searchable provenance-preserving site. | `specs/concorde/modules/auto-docs/architecture.md` |
| `entity.concorde.package-manifest` | configuration | Concorde 2.1.0 Package Manifest 2: the single version, profile, protocol, and inventory authority for Scripts, 17 leaf Skills, three Operation pairs, templates, the docsite template, the managed Operation runtime, and supported integrations. | `concorde.json` |
| `entity.concorde.protocol` | interface | Complete normative selected-feature change process, including Source Profile, workspace resolution, permission-bounded phases, attempts, reflections, validation, and delivery; Feature Workspace Protocol is one serialized component. | `concept:Concorde Protocol` |
| `entity.concorde.protocol-cutover` | pipeline | Concorde-repository-only procedure that directly evolves normative Protocol semantics from one exact committed Git checkpoint to one complete validated commit without an attempt, delivery, or imported primary dirty state. | `concept:Concorde Protocol evolution` |
| `entity.concorde.git` | external-system | Required version-control boundary for exact committed bootstrap checkpoints, default per-agent linked worktrees, reviewable diffs/commits, merge, abandonment, and revert; primary-worktree dirty bytes are outside its agent-input contract. | `external:git` |
| `entity.concorde.specification` | directory | Concorde's self-applied module architectures and direct feature files; the maintained project documentation. | `specs/concorde` |
| `entity.concorde.control-state` | directory | Project configuration, feature selection, constitution, stable-ID attempts, the reflection collection, and installed framework, runtime, and receipt state. | `.concorde` |
| `entity.concorde.source-code` | package | The standard-library Python package in which every capability module's programs are realized. | `src/concorde` |
| `entity.concorde.tests` | test | Unit, contract, integration, and acceptance evidence for every capability module. | `tests/concorde` |
| `entity.concorde.templates` | directory | Complete Markdown format references for features, constitutions, plans, tasks, checklists, and reflections, each owned by the capability module that consumes it. | `templates` |
| `entity.concorde.generated` | directory | Disposable diagram and site projections that carry source provenance. | `concept:generated projections` |
| `entity.concorde.coding-agent` | external-system | Codex or Claude host that follows projected Skills/Operations under an enforced task policy, bootstraps through an attested exact client executable, returns typed semantic completion, defaults mutations to committed-base linked worktrees, and authors only authorized sources. | `external:coding-agent` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.concorde.operation` | `has_entry_point` | `entity.concorde.operation-skill` | One definition has exactly one canonical Skill; each such Skill exposes one Operation. Installation may generate several integration projections. |
| `entity.concorde.operation` | `composed_of` | `entity.concorde.execution-script` | One definition has one or more executable Python scripts and exactly one primary entry point; the shipped pair currently uses one operation.py. |
| `entity.concorde.operation-invocation` | `realizes` | `entity.concorde.operation` | Each invocation runs exactly one definition; a definition may have zero or many invocations. |
| `entity.concorde.operation-configuration` | `configures` | `entity.concorde.operation-invocation` | Target: one initialized project configuration can serve many runs; each run pins exactly one immutable effective snapshot, inherited by nested Operations. |
| `entity.concorde.operation-invocation` | `reads_from` | `entity.concorde.runtime-input` | Target: exactly one typed input object per invocation, validated before side effects; task data cannot widen configuration or host authority. |
| `entity.concorde.data-contract` | `defines` | `entity.concorde.runtime-input` | Target: every input has exactly one resolvable type_id/schema_version pair with field semantics owned by its provider. |
| `entity.concorde.data-contract` | `defines` | `entity.concorde.operation-result` | Target: every domain result has exactly one declared type/version; semantic completion evidence alone is not that domain schema. |
| `entity.concorde.operation-invocation` | `generates` | `entity.concorde.operation-result` | Target: one terminal result for an admitted invocation; only validated success data may feed a consumer. |
| `entity.concorde.operation-result` | `contains` | `entity.concorde.artifact-reference` | Target: zero or more artifact references; each retains its actual owner/lifetime instead of copying the artifact into global state. |
| `entity.concorde.data-handoff` | `reads_from` | `entity.concorde.operation-result` | Target: names one successful producer result and its selected fields; fan-in names each producer explicitly. |
| `entity.concorde.data-handoff` | `transforms` | `entity.concorde.runtime-input` | Target: maps selected fields into one consumer's declared input, rejecting missing, incompatible, cross-feature, or stale data. |
| `entity.concorde.package-manifest` | `declares` | `module.concorde.capabilities` | Inventories every Script, leaf Skill, and Operation pair by globally unique safe name. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.templates` | Inventories every complete Markdown format reference. |
| `entity.concorde.package-manifest` | `declares` | `module.concorde.auto-docs` | Inventories the docsite adapter as the packaged template root. |
| `entity.concorde.protocol` | `governs` | `module.concorde.understanding` | Defines Source Profile, workspace, context, validation, and authority semantics used by every phase. |
| `entity.concorde.protocol` | `governs` | `module.concorde.lifecycle` | Defines the normal selected-feature phases, temporal attempt, and cleanup-only delivery boundary. |
| `entity.concorde.protocol` | `governs` | `module.concorde.reflections` | Defines when process problems are recorded and how their resolution re-enters lifecycle capabilities. |
| `entity.concorde.protocol` | `governs` | `module.concorde.capabilities` | Defines the Tool/Skill/Operation and permission/effect rules under which phases execute. |
| `entity.concorde.protocol-cutover` | `evolves` | `entity.concorde.protocol` | Changes normative Protocol semantics outside the attempt/delivery lifecycle they govern. |
| `entity.concorde.protocol-cutover` | `depends_on` | `entity.concorde.git` | Keeps the valid base and complete target in separate worktrees and records one reviewable transition. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.specification` | Reconciles Constitution, architecture, feature, interface, and guidance semantics directly. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.control-state` | Changes tracked control authorities only when the target Protocol requires it and never creates a cutover attempt. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.source-code` | Reconciles the implementation of the target Protocol in the same cutover. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.tests` | Reconciles executable evidence and requires the complete target checks before merge. |
| `module.concorde.understanding` | `validates` | `entity.concorde.specification` | Loads and deterministically validates the Profile 7 model that every other module reads. |
| `module.concorde.understanding` | `reads_from` | `entity.concorde.control-state` | Resolves native selection, stable-ID attempt state, and reflection state into Protocol 13. |
| `module.concorde.lifecycle` | `calls` | `module.concorde.understanding` | Every phase resolves its workspace, bounded context, and validation through understanding Tools before it changes anything. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.control-state` | Phases create, update, and finally remove exactly one stable-ID attempt. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.specification` | Specification and implementation reconcile module architectures and direct feature files. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.source-code` | Implementation and the fast loop change code only within task-authorized paths. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.tests` | Implementation records executable evidence beside the code it proves. |
| `module.concorde.lifecycle` | `writes_to` | `module.concorde.reflections` | Planning, task generation, implementation, and the fast loop record one problem per file. |
| `module.concorde.reflections` | `composes` | `module.concorde.lifecycle` | Triage routes a reflection through analyze, fast-loop, plan, tasks, implement, and validate as opaque direct capabilities. |
| `module.concorde.capabilities` | `provides` | `module.concorde.understanding` | Declares, validates, launches, and projects the understanding Skills and Tools. |
| `module.concorde.capabilities` | `provides` | `module.concorde.lifecycle` | Declares, permission-bounds, launches, and projects the lifecycle Skills and Operations. |
| `module.concorde.capabilities` | `provides` | `module.concorde.reflections` | Declares, permission-bounds, launches, and projects the triage Operation and its agents. |
| `module.concorde.capabilities` | `reads_from` | `module.concorde.understanding` | Compiles Protocol 13 roles into concrete per-leaf policies before any launch. |
| `module.concorde.capabilities` | `configures` | `entity.concorde.coding-agent` | Renders task policy, attests native runtime bootstrap, supplies the host workspace receipt/completion schema, and accepts only validated semantic success. |
| `entity.concorde.coding-agent` | `depends_on` | `entity.concorde.git` | Establishes one committed-base linked worktree before planning, attempt/control creation, or any other write unless the maintainer explicitly authorizes primary-worktree mutation. |
| `module.concorde.distribution` | `reads_from` | `entity.concorde.package-manifest` | Installs one allowlisted package from the native package identity. |
| `module.concorde.distribution` | `calls` | `module.concorde.capabilities` | Projects the 18 public capabilities and verifies every installed Operation through the managed launcher. |
| `module.concorde.distribution` | `writes_to` | `entity.concorde.control-state` | Writes the framework projection, the isolated Operation runtime, and the ownership receipt. |
| `module.concorde.auto-docs` | `reads_from` | `entity.concorde.specification` | Publishes only validated architectures, direct features, and architecture-owned diagrams. |
| `module.concorde.auto-docs` | `generates` | `entity.concorde.generated` | Renders diagram deliveries and the site as disposable provenance-bearing projections. |
| `entity.concorde.coding-agent` | `reads_from` | `entity.concorde.specification` | Reads only the bounded architecture and feature context its policy admits. |
| `entity.concorde.source-code` | `realizes` | `entity.concorde.specification` | Code is the actual implementation of every module's entities and features. |
| `entity.concorde.source-code` | `tested_by` | `entity.concorde.tests` | Tests provide bounded executable evidence. |

## Identity, Ownership, and Lifetime

| Concept | Identity / cardinality | Owner and source of truth | Lifetime |
|---|---|---|---|
| Operation definition | Stable `concorde-*` name; one owner, one Skill, one primary Python entry point | Its capability module and canonical pair, inventoried by `concorde.json` | Across many runs; paths may change without changing identity |
| Invocation | Target host-issued `invocation_id`; exactly one definition, config snapshot, and input | Trusted runtime; input JSON cannot invent workspace authority | One run, including its nested calls; distinct from a feature attempt |
| Configuration | Target `concorde-operation-configuration@1`; one effective snapshot shared by a run | Project configuration, with settings established by init | Reused until explicitly changed; in-flight runs retain their snapshot |
| Runtime input / result | Target `(type_id, schema_version)` identifies a type, not an instance or Skill | Field definitions in the providing feature's interface | One invocation / one producer-to-consumer transfer |
| Feature and attempt | Stable `feature.*` identity; at most one active attempt per feature | Durable feature file; Lifecycle owns `.concorde/attempts/<feature-id>/` | Feature persists; attempt is removed by delivery |
| Artifact reference | Target `id`, `path`, `digest`; never path alone | Original artifact's owner; references grant no additional read rights | Expires when bytes change or delivery removes the attempt |
| Host context | Resolved feature/workspace identity and digest-bound receipts | Understanding resolves; Capabilities binds/enforces | Bound to current source/worktree and checked before use |

## Operation Data Flow

The [Operation dataflow](diagrams/operation-dataflow.json) is a **target data-contract view** of the
planning boundary shared by the standard loop and reflection triage. The
[system overview](diagrams/system-overview.json) shows the shared concept structure; the
[module collaboration view](diagrams/module-collaboration.json) retains the implementation ownership
map. These views answer different questions and share the definitions above.

In the following table, `@1` means `schema_version: 1`; each type's `data` fields are defined by its
owning feature. A host workspace receipt is bound alongside data, never accepted as caller authority.

| Producer | Consumer | Payload and exact mapping | Storage / rejection | Governing feature |
|---|---|---|---|---|
| Project init/configuration | Any Operation invocation | `concorde-operation-configuration@1`: copy the validated `integration` and `enforcement` settings into an immutable snapshot | Project config persists; missing settings block execution instead of each script silently selecting Codex | `feature.capabilities.provide-capability-surfaces` |
| Standard development loop | Plan Operation | `concorde-standard-dev-loop-context@1` → `concorde-plan-context@1`: copy `feature_path`, `request`, `constraints` after specification; inherit config/worktree | Re-resolve the authored feature and reject absent or mismatched identity | `feature.lifecycle.standard-development-loop` |
| Reflection triage, implement/plan route | Plan Operation | `concorde-reflections-triage-context@1` → `concorde-plan-context@1`: copy `feature_path`, `request`, `constraints`; retain `reflection_ids` in the parent only | Recheck selected reflections and route; unrelated records are not implicit plan inputs | `feature.reflections.record-and-triage` |
| Plan Operation | Understanding context provider | `concorde-plan-context@1`: `feature_path` selects one workspace; request/constraints remain task intent | Read-only resolution; dependency access follows published required interfaces | `feature.lifecycle.plan-attempt` |
| Understanding context provider | Plan author | `concorde-planning-context@1` → `concorde-plan-author-context@1`: copy the resolved context plus the original `concorde-plan-context@1` task | Context carries feature, owned/provider artifact refs and source digest; ambiguity/staleness stops the author | `feature.understanding.bound-planning-context` |
| Plan author / Plan Operation | Standard loop or triage parent | `concorde-plan-result@1`: `feature_id`, `feature_path`, `attempt_dir`, `source_digest`, `artifacts`; parent checks identity and forwards only these fields to tasks/implementation | Attempt remains authoritative; parents do not parse child traces or inherit arbitrary prior prose | `feature.lifecycle.plan-attempt` |
| Validation and delivery | Parent final result | Typed final domain result plus separately bound completion evidence; copy feature identity and terminal outcome | Failed validation stops delivery; delivered attempt refs must not be treated as live artifacts | `feature.lifecycle.standard-development-loop` |

The current runtime does not yet implement these domain envelopes: its nested dispatch returns
JSON-encoded lists of `CapabilityResult` and its leaf prompts receive string prior results. The
target requires explicit adapters and domain validation at these exact boundaries, preserving
existing workspace, permission, and completion checks.

## Review of Current Architecture and Required Runtime Work

| Finding | Specification correction in this revision | Current implementation / next owner |
|---|---|---|
| Project-level inventory hid the core Operation concept behind folders and modules | Shared concepts, ownership/lifetime table, constrained relationships, and complementary diagrams above | Existing three Operation pairs are concrete instances; module ownership stays unchanged |
| `--integration`, task request, and `--feature-path` were mixed in parser arguments | Separate project config, typed runtime input, and host-derived context | Capabilities: introduce JSON boundary/config snapshot; Understanding: extend init through a reviewed proposal |
| No fixed domain input type identified a planning request | `concorde-plan-context@1` fields and examples in the planning feature | Lifecycle: replace positional request parsing in the executable Operation cutover |
| Stage ordering obscured data transfer; nested results were opaque strings | Explicit producer/consumer mappings and domain result contracts | Capabilities/Lifecycle/Reflections: validate types, map fields, and retain nested opacity |
| Semantic completion could be mistaken for a domain data schema | Domain payload and execution evidence have separate authorities | Existing Capability Completion Envelope 1 remains supported; typed domain results are additional target work |
| Initializer/validator success appeared to imply a complete concept model | Prompt/template review checks distinguish semantic completeness from structural checks | Init still produces a minimal seed; Profile 7 validation still checks structure/references, not this full semantic review |
| Installation and publication implications were not visible | All module boundaries below link to the shared contract and its realization status | Distribution must migrate/project the new invocation only when executable support exists; Auto-Docs publishes source-declared dataflow |

This revision changes architecture-authoring obligations and specifications. It does not migrate the
three executable Operation parsers, project configuration on disk, Package Manifest 2, Workspace
Protocol 13, or the installed launcher ABI. Runtime adoption must reconcile those code paths,
schemas, tests, canonical Operation Skills, and installation verification together. No current
command should be rewritten to the target JSON syntax before that cutover.

## Relationship Types

| Predicate | Direction and meaning |
|---|---|
| `composes` | From a controlling Operation or module to direct Skills, public Operations, or the module that owns them, whose identities and results it sequences without taking ownership or flattening internals. |
| `evolves` | From the Concorde-repository cutover process to the normative Concorde Protocol whose semantics it replaces as one validated Git transition. |
| `governs` | From the normative Concorde Protocol to each capability module whose selected-feature behavior it constrains. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.concorde.feature-work` | Maintainer invokes a mutating lifecycle Skill or Operation for one selected feature. | Establish the committed-base linked worktree and exclude primary dirty state; `module.concorde.understanding` resolves Protocol 13 once; `module.concorde.capabilities` binds that receipt, compiles task policy, attests the selected native client, finalizes the launch, and validates semantic completion before state advances; `module.concorde.lifecycle` runs phases/evidence/validation and removes exactly the delivered attempt. | Intent, implementation, tests, and temporal state remain reconciled; only completed capabilities advance, while unrelated primary state and integration bootstrap stay outside task authority. | `contract.concorde.workflow`, `contract.capabilities.permission-bounded-execution` |
| `interaction.concorde.evolve-protocol` | Maintainer explicitly classifies and authorizes a normative Concorde Protocol change from one exact committed base with no active attempt in that commit. | Create one isolated branch/worktree through `entity.concorde.git` without importing primary dirty state; directly reconcile `entity.concorde.specification`, `entity.concorde.control-state`, `entity.concorde.source-code`, `entity.concorde.tests`, templates, fixtures, and projections without lifecycle capabilities; validate the complete target; review and merge one cutover commit or abandon/revert it on failure. | The valid committed base and unrelated primary-worktree state remain available until one complete, target-valid Protocol state replaces it without a self-invalidating attempt or compatibility reader. | `interface.concorde.protocol-evolution` |
| `interaction.concorde.install` | Maintainer previews or explicitly applies a checkout through the native installer. | `module.concorde.distribution` reads `entity.concorde.package-manifest`; calculates owned file and isolated-runtime actions; projects 18 public capabilities through `module.concorde.capabilities`; installs the pinned official Understand Anything Viewer inside the managed runtime; writes framework, runtime, and receipt into `entity.concorde.control-state`. | Idempotent Concorde 2.1.0 installation whose Operations and Viewer start offline, or exact conflict diagnostics. | `contract.concorde.installation` |
| `interaction.concorde.publish` | Maintainer or CI requests the project read model. | `module.concorde.understanding` validates `entity.concorde.specification`; `module.concorde.auto-docs` renders declared diagrams and builds a candidate; the candidate is promoted atomically into `entity.concorde.generated`. | Searchable Architecture/Features site with source provenance and a root architecture entry. | `interface.concorde.publish-docsite` |
| `interaction.concorde.reflect` | A phase records a problem or the maintainer selects a triage action. | `module.concorde.lifecycle` writes one document into `module.concorde.reflections`; `module.concorde.reflections` composes `module.concorde.lifecycle` on the chosen route under policies from `module.concorde.capabilities`; maintainer disposition closes the document. | Every retained problem is tracked once and is resolved or dismissed with Git history as its record. | `interface.concorde.reflections` |

## Modules

| Module | Responsibility | Boundary interaction |
|---|---|---|
| `module.concorde.understanding` | Know what a project is. | Validates the specification and supplies bounded context, Protocol 13, and planning context to every other module. |
| `module.concorde.lifecycle` | Change one feature safely from specify to deliver. | Calls understanding, writes specification/code/tests/attempts, and records reflections. |
| `module.concorde.reflections` | Record and resolve process problems. | Receives documents from lifecycle phases and composes lifecycle capabilities during triage. |
| `module.concorde.capabilities` | Run any Concorde capability on a coding agent under an enforced policy. | Provides the Tool, Skill, and Operation mechanism to the three capability modules and configures the coding agent. |
| `module.concorde.distribution` | Ship and install the package. | Reads the manifest, calls capabilities for projection and verification, and writes installed control state. |
| `module.concorde.auto-docs` | Publish the validated read model. | Reads the specification and writes generated projections. |

## Features

| Feature | Outcome |
|---|---|
| `feature.concorde.workflow` | Carry one direct feature from intent through reconciled implementation and cleanup-only delivery using installed capabilities as the sole conversational surface. |
| `feature.concorde.define-project-ontology` | Define and validate the recursive, capability-partitioned module architecture plus the Script/Tool/Skill/Operation structure that every Concorde project, including this one, follows. |
| `feature.concorde.evolve-protocol` | Evolve normative Concorde Protocol semantics directly in one isolated, attempt-free, fully validated Git cutover unique to this self-applying repository. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Child modules are partitioned by capability, use case, and axis of change (constitution A.VI), not
  by artifact type: each owns every Skill, Tool, Operation, template, schema, and rule its capability
  needs. The flat `skills/`, `operations/`, `templates/`, `scripts/`, and `agent-assets/` directories
  are the distribution format fixed by Package Manifest 2; ownership is expressed by stable entity
  identity in the owning module, never by directory.
- The root owns only project-wide features: the end-to-end workflow, the shared ontology, and the
  Concorde-repository-only Protocol-evolution boundary. Every capability-local use case descends to
  the module that provides it.
- Every Concorde project consumes `entity.concorde.protocol`; only this repository defines,
  implements, and self-applies it. Normative Protocol evolution therefore uses
  `entity.concorde.protocol-cutover`, never an attempt, fast loop, standard loop, or delivery.
- Scripts expose deterministic Tools; public/internal leaf Skills invoke Tools and own effects;
  paired LangGraph Operations compose ordered direct capabilities with explicit controls and
  per-leaf enforced launches. Every Operation Python has one associated Markdown skill, and both leaf
  and Operation skills are installed into one global `concorde-*` agent namespace.
- Package Manifest 2, one installation receipt, one isolated installed Operation environment, and
  version 2.1.0 replace independently composed or mixed-layout capability sources; the source root
  `.venv` and installed `.concorde/.venv` remain distinct and no compatibility shim remains.
- Stable architecture identity remains separate from mutable file/symbol locators.
- Read-only agent work may remain in the primary checkout; every agent-authored mutation defaults to
  one unique linked worktree from its exact committed `HEAD`. Primary staged, unstaged, untracked,
  and ignored bytes are never implicit input, and a generic change request never authorizes the
  primary-worktree override.
- Code and tests remain implementation/evidence; plans and task state remain temporal; generated
  and installed projections never become specification or implementation authority.

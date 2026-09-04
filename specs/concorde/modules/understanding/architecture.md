---
id: module.concorde.understanding
kind: module
parent: module.concorde
modules: []
features:
  - feature.understanding.initialize-architecture
  - feature.understanding.retrieve-bounded-context
  - feature.understanding.answer-workflow-questions
  - feature.understanding.resolve-feature-workspace
  - feature.understanding.validate-architecture
  - feature.understanding.explore-alignment
  - feature.understanding.bound-planning-context
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-understanding-system-overview.html
---

# Architecture: Understanding

## Responsibility

Know what a project is: model it as a validated Profile 7 hierarchy, load it deterministically,
bound one feature's context and permission paths, explore alignment with code evidence, and answer
grounded questions.

## Boundary

Understanding owns the Profile 7 source model and repository loader; the layout, hierarchy, entity,
feature, diagram, and freshness validation rules; the initialization proposal; bounded
module/feature context projection; Feature Workspace Protocol 13 resolution and permission-role path
validation; the planning-context resolver; the alignment explorer and its Understand Anything adapter;
the file-role ontology that distinguishes specification, control state, code, tests, and generated
projections; and the `concorde-init`, `concorde-context`, `concorde-ask`, `concorde-validate`,
`concorde-constitution`, and `concorde-plan-context` Skills plus the feature and constitution format
references. It does not own lifecycle phase prompts, the capability runtime/policy compiler/process
launcher, reflection semantics, installation, or publication.

## Operation Contract Boundary

Understanding provides initialization and host-resolved context to `entity.concorde.operation`.
`entity.understanding.config` currently stores source-profile/root selection only. The target
Operation configuration is separately typed under `operation_configuration` in that file and must
be established by a future reviewed init/config proposal; it is not yet written by Proposal 3.

This module owns `concorde-planning-context@1` field semantics in its bounded-planning-context
feature. It derives feature identity, admitted file references/reasons, attempt path, and source
digest; a caller's `feature_path` selects input but cannot dictate those derived facts. The internal
Skill named `concorde-plan-context` is distinct from the caller data type of that spelling owned by
Lifecycle. Current resolution returns a Python record; its target serialization remains pending.

The generic initializer emits a minimal root scaffold. Structural validation proves Profile 7
shape/reference conformance, not that all product concepts, cardinalities, or data handoffs have
been adequately defined. The ontology's authoring/review contract supplies that semantic review.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.understanding.planning-context-data` | type | Target concorde-planning-context@1: host-resolved feature/module identity, bounded artifact references/reasons, attempt path, exclusions, and source digest. | `concept:concorde-planning-context@1` |
| `entity.understanding.model` | package | Immutable Tool result, module, entity, relation, interface, context, and finding records. | `src/concorde/model.py` |
| `entity.understanding.repository-loader` | program | Discovers Profile 7 module architectures, direct features, diagrams, and control authorities. | `src/concorde/understanding/repository.py#ProjectRepository.load` |
| `entity.understanding.context-builder` | program | Projects one bounded module or feature altitude. | `src/concorde/understanding/context.py#bounded_context` |
| `entity.understanding.workspace-resolver` | program | Resolves native selection, ancestry, related summaries, attempt/reflection state, executable roots, and safe concrete Protocol-13/task path roles without following symlinks. | `src/concorde/understanding/feature_workspace.py#resolve_phase_paths` |
| `entity.understanding.workspace-adapter` | program | Before emitting Protocol 13 paths, rejects mutating phases/selection persistence in the primary worktree unless the explicit override is present; read-only validation remains available. | `scripts/workspace.py` |
| `entity.understanding.planning-context` | program | Resolves selected/providing-module paths and exact project-owned required-interface feature specifications, skips explicitly external required providers, and denies provider internals, symlinks, escapes, and other attempts. | `src/concorde/understanding/planning_context.py#resolve_planning_context` |
| `entity.understanding.validator` | program | Runs layout/parallel-authority, hierarchy, entity, feature, diagram, and freshness rules. | `src/concorde/understanding/validate.py#validate_project` |
| `entity.understanding.model-rules` | package | Layout, hierarchy, entity, feature, diagram, and freshness rule sets that give the validator its deterministic checks. | `src/concorde/understanding/validation` |
| `entity.understanding.initializer` | program | Proposes and atomically applies Initialization Proposal 3 with a root Archify system overview. | `src/concorde/understanding/initialize.py` |
| `entity.understanding.alignment-explorer` | program | Validates optional pinned UA graph/sidecar inputs and projects bounded evidence-qualified alignment without mutation. | `src/concorde/understanding/alignment.py#explore_alignment` |
| `entity.understanding.protocol13` | schema | Structured phase context for one direct feature and stable-ID attempt whose returned paths can be validated into concrete non-symlink permission roles. | `concept:Feature Workspace Protocol 13` |
| `entity.understanding.config` | configuration | Selects Profile 7, specification root, and root module identity. | `.concorde/config.json` |
| `entity.understanding.selection` | configuration | Native pointer containing exactly one canonical direct `feature_path`. | `.concorde/feature.json` |
| `entity.understanding.constitution` | document | Optional project governance authority consulted by lifecycle and capability Skills and Operations. | `.concorde/constitution.md` |
| `entity.understanding.module-architecture` | document | One module's structural authority and maintained architecture documentation: responsibility, boundary, entities, relations, interactions, children, features, and decisions. | `concept:<module>/architecture.md` |
| `entity.understanding.feature-design` | document | One direct feature's behavioral authority and maintained feature documentation: outcome, usage, scenarios, interfaces, requirements, and architecture zoom. | `concept:<module>/features/<NNN-name>.md` |
| `entity.understanding.module-diagrams` | directory | Required Archify system overview plus optional maintained explanatory sources owned by one module architecture. | `concept:<module>/diagrams` |
| `entity.understanding.feature-template` | document | Complete direct-feature format with outcome, usage, scenarios, interfaces, architecture zoom, requirements, and criteria. | `templates/feature-template.md` |
| `entity.understanding.constitution-template` | document | Governance-document format reference. | `templates/constitution-template.md` |
| `entity.understanding.init-skill` | document | Leaf prompt that proposes and applies the reviewed root architecture scaffold. | `skills/concorde-init/SKILL.md` |
| `entity.understanding.context-skill` | document | Leaf prompt that retrieves exactly one bounded module or feature context. | `skills/concorde-context/SKILL.md` |
| `entity.understanding.ask-skill` | document | Leaf prompt that answers a grounded, read-only question about Concorde. | `skills/concorde-ask/SKILL.md` |
| `entity.understanding.validate-skill` | document | Leaf prompt that deterministically validates module-centered Concorde sources. | `skills/concorde-validate/SKILL.md` |
| `entity.understanding.constitution-skill` | document | Leaf prompt that creates or updates the project constitution from provided principles. | `skills/concorde-constitution/SKILL.md` |
| `entity.understanding.plan-context-skill` | document | Internal leaf prompt that resolves and reports the permission-bounded context for one selected planning attempt. | `skills/concorde-plan-context/SKILL.md` |
| `entity.understanding.understand-anything` | external-system | Optional executable graph provider for evidence-qualified alignment exploration. | `external:Egonex-AI/Understand-Anything@ba450c4` |
| `entity.understanding.tests` | test | Unit, contract, integration, and acceptance evidence for Understanding Tool semantics. | `tests/concorde/understanding` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.understanding.planning-context` | `generates` | `entity.understanding.planning-context-data` | Target: serializes the resolved context for Lifecycle; the consumer must bind it to its host receipt. |
| `entity.understanding.repository-loader` | `reads_from` | `entity.concorde.specification` | Loads canonical module architectures, direct features, and declared diagrams. |
| `entity.understanding.repository-loader` | `reads_from` | `entity.concorde.control-state` | Loads configuration, selection, attempt, and reflection state alongside specification sources. |
| `entity.understanding.validator` | `reads_from` | `entity.understanding.repository-loader` | Validates the same loaded package model used by every Tool. |
| `entity.understanding.validator` | `calls` | `entity.understanding.model-rules` | Runs layout, hierarchy, entity, feature, diagram, and freshness rule sets. |
| `entity.understanding.context-builder` | `reads_from` | `entity.understanding.repository-loader` | Projects one bounded module or feature altitude from the loaded model. |
| `entity.understanding.workspace-resolver` | `reads_from` | `entity.understanding.repository-loader` | Builds Protocol 13 context from normalized IDs and paths. |
| `entity.understanding.alignment-explorer` | `reads_from` | `entity.understanding.repository-loader` | Projects the same validated Profile 7 identities used by every Tool. |
| `entity.understanding.planning-context` | `reads_from` | `entity.understanding.repository-loader` | Resolves selected and providing-module paths from the same loaded model. |
| `entity.understanding.planning-context` | `depends_on` | `entity.understanding.workspace-resolver` | Starts from the same Protocol 13 feature/module/ancestry result before narrowing to owned and required-interface paths. |
| `entity.understanding.workspace-adapter` | `calls` | `entity.understanding.workspace-resolver` | Emits Protocol 13 paths for one native-selected direct feature. |
| `entity.understanding.initializer` | `writes_to` | `entity.concorde.specification` | Atomically promotes exactly the reviewed root architecture and its diagram. |
| `entity.understanding.initializer` | `writes_to` | `entity.concorde.control-state` | Creates Profile 7 configuration and the reflection allocation index. |
| `entity.understanding.selection` | `routes_to` | `entity.understanding.feature-design` | Chooses one workflow root without defining behavior. |
| `entity.understanding.config` | `configures` | `entity.understanding.module-architecture` | Identifies the root architecture and Profile 7 source model. |
| `entity.understanding.module-architecture` | `registers_feature` | `entity.understanding.feature-design` | Owns each direct level-local feature once. |
| `entity.understanding.module-architecture` | `contains_module` | `entity.understanding.module-diagrams` | Declares the required system overview and any explanatory sources owned by the module. |
| `entity.understanding.module-diagrams` | `generates` | `entity.concorde.generated` | Maintained views produce disposable provenance-bearing deliveries. |
| `entity.understanding.protocol13` | `documents` | `entity.understanding.feature-design` | Exposes canonical feature/module/ancestry/related context. |
| `entity.concorde.source-code` | `realizes` | `entity.understanding.feature-design` | Code is actual implementation, not a prose realization file. |
| `entity.concorde.source-code` | `tested_by` | `entity.concorde.tests` | Tests provide bounded executable evidence. |
| `entity.understanding.constitution-skill` | `writes_to` | `entity.understanding.constitution` | Maintains governance principles from provided maintainer input. |
| `entity.understanding.init-skill` | `calls` | `entity.understanding.initializer` | Invokes the initialize Tool to propose and apply the root scaffold. |
| `entity.understanding.context-skill` | `calls` | `entity.understanding.context-builder` | Invokes the context Tool for one bounded altitude. |
| `entity.understanding.validate-skill` | `calls` | `entity.understanding.validator` | Invokes the validate Tool for deterministic findings. |
| `entity.understanding.plan-context-skill` | `calls` | `entity.understanding.planning-context` | Invokes the planning-context resolver and reports its receipt. |
| `entity.understanding.ask-skill` | `reads_from` | `entity.concorde.specification` | Answers from the smallest bounded maintained source without mutation. |
| `entity.concorde.coding-agent` | `implements` | `entity.understanding.init-skill` | Follows the installed prompt and its declared write boundary. |
| `entity.concorde.coding-agent` | `implements` | `entity.understanding.context-skill` | Follows the installed prompt within its read-only boundary. |
| `entity.concorde.coding-agent` | `implements` | `entity.understanding.ask-skill` | Follows the installed prompt within its strictly read-only boundary. |
| `entity.concorde.coding-agent` | `implements` | `entity.understanding.validate-skill` | Follows the installed prompt within its read-only boundary. |
| `entity.concorde.coding-agent` | `implements` | `entity.understanding.constitution-skill` | Follows the installed prompt scoped to the constitution document. |
| `entity.concorde.coding-agent` | `implements` | `entity.understanding.plan-context-skill` | Follows the installed prompt to report context without further mutation. |
| `entity.understanding.understand-anything` | `provides` | `entity.understanding.alignment-explorer` | Supplies optional pinned graph evidence without replacing Concorde identity. |
| `entity.understanding.alignment-explorer` | `tested_by` | `entity.understanding.tests` | Unit through acceptance cases establish its bounded claims. |
| `entity.understanding.validator` | `tested_by` | `entity.understanding.tests` | Executable cases establish bounded validation evidence. |
| `module.concorde.capabilities` | `calls` | `module.concorde.understanding` | Dispatches Understanding's deterministic Tools (initialize, context, validate, explore, workspace) through the shared CLI and Tool envelope. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.understanding.initialize` | A maintainer requests initialization for an unconfigured or partially configured project. | Locate the project root; propose Profile 7 configuration, one root architecture, its system overview, and the reflection allocation index; let the maintainer review the digest-bound proposal; on explicit apply atomically promote exactly those four files. | A minimal reviewed root scaffold exists, or an already configured project returns unchanged. | `interface.concorde.initialize` |
| `interaction.understanding.retrieve-context` | A maintainer or agent requests one stable module or feature ID. | Validate Profile 7; load only the canonical sources for that ID; project responsibility/boundary/entities/relations/interactions or feature design/interfaces/zoom; stop at immediate children and related-feature summaries. | Exactly one bounded altitude returns without descendant or unrelated bodies. | `interface.concorde.context` |
| `interaction.understanding.resolve-workspace` | A path-sensitive Skill, Operation stage, or delivery Tool starts a phase for a selected feature. | For a mutating phase or selection persistence, first require the committed-base linked-worktree boundary; resolve explicit path, environment selection, or `.concorde/feature.json`; load the direct feature/module; derive stable-ID attempt/reflection/executable context; validate concrete task/role paths and reject symlinks/escapes; return Protocol 13. | Exactly one canonical direct feature plus bounded safe role inputs is routed, or primary/non-Git mutation fails before write-target resolution. | `interface.concorde.workspace` |
| `interaction.understanding.bound-planning-context` | A planning Operation or its plan-author leaf resolves context for one selected feature. | Resolve the selected feature, its providing module's owned architecture/implementation/test locators, and its attempt paths; walk `interfaces.required` to the exact feature file that owns each interface with a reason trace; deny dependency module internals, descendant modules, unrelated features, and other attempts; return one context receipt. | A plan author reads exactly the selected feature's context plus the published dependency promises it needs, never a dependency module's private internals. | `contract.understanding.planning-context` |
| `interaction.understanding.validate` | A maintainer, CI job, or lifecycle gate requests deterministic validation. | Load the normalized source package; run layout, hierarchy, entity, feature, diagram, and freshness rules plus any composed capability-scoped rules; format one structured result with rule/severity/subject/path/remediation per finding. | A repeatable, complete, actionable account of Profile 7 and control-state integrity, with no mutation. | `interface.concorde.validate` |
| `interaction.understanding.explore` | A maintainer or agent requests one stable module, entity, feature, or interface alongside optional implementation evidence. | Validate Profile 7; project the target altitude; validate optional UA graph and schema-1 sidecar; compare revisions; qualify records; apply text/status bounds; serialize one Tool result. | Current explicit evidence may qualify alignment; absent, stale, incompatible, or candidate-only claims remain unknown. | `contract.concorde.alignment-explorer`, `contract.understand-anything.knowledge-graph` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.understanding.initialize-architecture` | Propose and apply a minimal reviewed root architecture without inventing product structure. |
| `feature.understanding.retrieve-bounded-context` | Retrieve exactly one module or feature altitude with its visible entities, relationships, interfaces, and navigation references. |
| `feature.understanding.answer-workflow-questions` | Answer read-only, cited Concorde questions from the smallest bounded maintained sources. |
| `feature.understanding.resolve-feature-workspace` | Resolve native feature selection into Feature Workspace Protocol 13 paths and role/lifecycle records for every phase. |
| `feature.understanding.validate-architecture` | Diagnose layout, hierarchy, entity, feature, interface, evidence, diagram, and freshness state deterministically. |
| `feature.understanding.explore-alignment` | Browse evidence-qualified specification-to-code relationships through a read-only Tool. |
| `feature.understanding.bound-planning-context` | Resolve one permission-bounded planning context receipt from Protocol 13 and published dependency interfaces. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Python standard-library behavior is canonical for every Understanding Tool; loading, validation,
  context projection, workspace resolution, and exploration require no external dependency.
- Native selection lives at `.concorde/feature.json`; no compatibility reader exists for host state.
- Feature Workspace Protocol 13 and Initialization Proposal 3 use `tool` discriminators; Operation
  metadata is reserved for paired LangGraph execution owned elsewhere.
- Exploration never normalizes or rewrites input graphs and never treats adapter vocabulary or text
  similarity as identity/evidence.
- Exact stable feature IDs key attempts across file/module moves; a planned feature exposes no guessed
  attempt path until specification persists its ID and workspace resolution reruns.
- Generated and installed projections never become specification or implementation authority.
- Module architectures and direct feature designs are the only maintained prose documentation
  authorities; root `docs/` is invalid parallel authority.
- `validate_project` composes this module's layout/hierarchy/entity/feature/diagram/freshness
  rules with capability-scoped and reflection-scoped rules owned by other modules without importing
  their implementation into Understanding.
- Understanding owns the meaning of every file role; capability modules own what they write into those
  roles.

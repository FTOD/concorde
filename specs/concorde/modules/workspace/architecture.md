---
id: module.concorde.workspace
kind: module
parent: module.concorde
modules: []
features:
  - feature.workspace.manage-feature-workspace
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-workspace-system-overview.html
---

# Architecture: Workspace

## Responsibility

Define Profile 7 source authority, native project control, feature selection, bounded context and
concrete permission roles, attempt lifecycle, evidence placement, reflection ownership, installation
ownership, and generated projection boundaries.

## Boundary

Workspace owns the meaning and permitted placement/lifetime of durable, temporal, executable,
installed, and generated files. It does not own the agents or programs that author those files,
implementation behavior, test truthfulness, version-control history, or generated presentation.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.workspace.config` | configuration | Selects Profile 7, specification root, and root module identity. | `.concorde/config.json` |
| `entity.workspace.selection` | configuration | Native pointer containing exactly one canonical direct `feature_path`. | `.concorde/feature.json` |
| `entity.workspace.constitution` | document | Optional project governance authority used by lifecycle Skills and Operations. | `.concorde/constitution.md` |
| `entity.workspace.module-architecture` | document | One module's responsibility, boundary, entities, relations, interactions, children, features, and decisions. | `concept:<module>/architecture.md` |
| `entity.workspace.feature-design` | document | One direct feature's outcome, usage, scenarios, interfaces, requirements, and architecture zoom. | `concept:<module>/features/<NNN-name>.md` |
| `entity.workspace.module-directory` | directory | Immediate recursive child-module container. | `concept:<module>/modules/<child>` |
| `entity.workspace.module-diagrams` | directory | Required Archify system overview plus optional maintained explanatory sources owned by one module architecture. | `concept:<module>/diagrams` |
| `entity.workspace.control-state` | directory | Project-wide configuration, selection, governance, attempts, reflections, framework installation, and receipts. | `.concorde` |
| `entity.workspace.framework` | directory | Installed projection of one standalone package, including Tools, all 17 leaf Skills (two internal), and three paired Operations. | `concept:.concorde/framework` |
| `entity.workspace.install-receipt` | configuration | Digest/role ownership ledger for framework and agent outputs. | `concept:native-install-receipt` |
| `entity.workspace.attempt` | directory | Temporary plan/tasks/research/checklists/validation memory keyed by exact stable feature ID. | `concept:.concorde/attempts/<stable-feature-id>` |
| `entity.workspace.reflections` | directory | Per-file process memory with one `R-NNN.md` prose authority per problem and a metadata-only allocation index. | `.concorde/reflections` |
| `entity.workspace.source-code` | directory | Checked-out implementation authority. | `src` |
| `entity.workspace.tests` | test | Checked-out executable evidence and fixtures. | `tests` |
| `entity.workspace.generated` | directory | Disposable documentation, diagram, and release projections with provenance. | `generated` |
| `entity.workspace.protocol13` | schema | Structured phase context for one direct feature and stable-ID attempt whose returned paths can be validated into concrete non-symlink permission roles. | `concept:Feature Workspace Protocol 13` |
| `entity.workspace.delivery9` | schema | Digest-bound proposal/result for removing one complete attempt. | `concept:Delivery Proposal 9` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.workspace.config` | `configures` | `entity.workspace.module-architecture` | Identifies the root architecture/profile. |
| `entity.workspace.selection` | `routes_to` | `entity.workspace.feature-design` | Chooses one workflow root without defining behavior. |
| `entity.workspace.module-architecture` | `contains_module` | `entity.workspace.module-directory` | Registers immediate recursive module packages. |
| `entity.workspace.module-architecture` | `registers_feature` | `entity.workspace.feature-design` | Owns each direct level-local feature once. |
| `entity.workspace.control-state` | `contains` | `entity.workspace.attempt` | Centralizes temporary work outside specification hierarchy. |
| `entity.workspace.control-state` | `contains` | `entity.workspace.reflections` | Co-locates persisted process memory and scratch configuration. |
| `entity.workspace.control-state` | `contains` | `entity.workspace.framework` | Holds an installed package projection separate from project-authored specifications. |
| `entity.workspace.install-receipt` | `documents` | `entity.workspace.framework` | Records exact owned package and agent output digests. |
| `entity.workspace.attempt` | `depends_on` | `entity.workspace.feature-design` | Stable feature identity relates temporal state to a mutable file locator. |
| `entity.workspace.protocol13` | `documents` | `entity.workspace.feature-design` | Exposes canonical feature/module/ancestry/related context. |
| `entity.workspace.protocol13` | `documents` | `entity.workspace.attempt` | Exposes stable-ID-derived phase paths without guessing identity. |
| `entity.workspace.source-code` | `realizes` | `entity.workspace.feature-design` | Code is actual implementation, not a prose realization file. |
| `entity.workspace.source-code` | `tested_by` | `entity.workspace.tests` | Tests provide bounded executable evidence. |
| `entity.workspace.module-diagrams` | `generates` | `entity.workspace.generated` | Maintained views produce disposable provenance-bearing deliveries. |
| `entity.workspace.delivery9` | `validates` | `entity.workspace.attempt` | Requires completeness/freshness before exact removal. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.workspace.resolve` | A phase starts with explicit or native-selected feature path. | Validate direct placement/stable ID; find module/ancestry; summarize related features; derive stable-ID attempt/reflection/executable paths; trusted consumers validate entity/task locators into concrete roles and reject symlinks/escapes. | Protocol 13 returns exactly one bounded workspace suitable for fail-closed policy compilation. | `contract.workspace.feature-workspace` |
| `interaction.workspace.attempt` | Planning starts with no matching attempt. | Create the returned `.concorde/attempts/<stable-feature-id>/`; seed referenced temporal formats; later phases update declared artifacts and product authorities; evidence precedes completion. | One active attempt contains all unfinished delivery memory. | `contract.workspace.records` |
| `interaction.workspace.specify-new` | Specification selects a direct path not yet authored. | Return unavailable identity/attempt fields; author valid feature front matter; rerun Protocol 13; create only resolved attempt/checklist paths. | No stable identity is guessed from filename or module. | `contract.workspace.feature-workspace` |
| `interaction.workspace.install` | Native installer applies an accepted plan. | Validate target parents/ownership; install 17 leaves and three exact Operation pairs; project 15 public leaves plus three Operations; preserve project-authored control/spec/code; write one role/digest receipt. | Framework internals and 18 public agent capabilities are reproducible and distinguishable from project authority. | `contract.distribution.native-installation` |
| `interaction.workspace.cleanup` | Delivery Tool applies an eligible Proposal 9. | Verify safe attempt, digest, completion, evidence, findings, and rollback staging; remove exactly the attempt. | Feature returns to no-active-attempt state. | `contract.workspace.feature-workspace`, `contract.runtime.tools` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.workspace.manage-feature-workspace` | Every phase receives authoritative design, architecture, relation, attempt, reflection, source, and test paths for one native-selected feature. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Module containment is the only durable specification hierarchy; direct features never contain features.
- `.concorde/feature.json` replaces host-owned selection and has no compatibility fallback.
- `.concorde/framework` is installed package projection; `.concorde/config.json`, constitution, attempts, and reflections are project authority/control.
- Installed `skills/<name>/SKILL.md` (including internal leaves) and
  `operations/<name>/{operation.py,SKILL.md}` remain framework projection; only public leaves and
  Operations receive agent-facing generated Skill files.
- Protocol 13 remains a bounded data contract; Operations-owned trusted code, not an untrusted agent,
  resolves its roles, architecture locators, task tokens, and interface owners into enforcement paths.
- Exact stable feature IDs key attempts across file/module moves; planned files expose no guessed attempt path.
- Generated and installed projections never become specification or implementation authority.

---
id: module.concorde.workspace-files
kind: module
parent: module.concorde
modules: []
features:
  - feature.workspace-files.manage-feature-workspace
diagrams: []
---

# Architecture: Workspace Files

## Responsibility

Define the canonical Profile 7 filesystem model, source authority, selection, bounded context,
attempt lifecycle, evidence placement, reflection ownership, and generated projection boundary.

## Boundary

Workspace Files owns path/role/lifetime rules and the meaning of durable, temporal, executable, and
generated artifacts. It does not own the agents/scripts that author them, code behavior, tests'
truthfulness, version-control history, or generated presentation.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.workspace.config` | configuration | Selects Profile 7, specification root, and root module identity. | `.concorde/config.json` |
| `entity.workspace.module-architecture` | document | One module's durable responsibility, boundary, typed entities, relationships, interactions, modules, features, and decisions. | `concept:<module>/architecture.md` |
| `entity.workspace.feature-design` | document | One feature's direct durable outcome/interface/usage/requirements/architecture-zoom authority. | `concept:<module>/features/<NNN-name>.md` |
| `entity.workspace.module-directory` | directory | Immediate recursive child-module container. | `concept:<module>/modules/<child>` |
| `entity.workspace.module-diagrams` | directory | Optional maintained explanatory sources owned by one module architecture. | `concept:<module>/diagrams` |
| `entity.workspace.control-state` | directory | Project-wide workflow state outside the recursive specification hierarchy. | `.concorde` |
| `entity.workspace.attempt` | directory | Temporary plan/tasks/research/checklists/validation memory keyed by one globally unique path-safe feature ID. | `concept:.concorde/attempts/<stable-feature-id>` |
| `entity.workspace.selection` | configuration | Spec Kit-owned pointer to the current direct feature file. | `.specify/feature.json` |
| `entity.workspace.reflections` | document | Tracked project log and sole persisted authority for difficult choices/problems and their stable identities. | `.concorde/reflections/log.md` |
| `entity.workspace.source-code` | directory | Checked-out executable implementation authority. | `extensions` |
| `entity.workspace.tests` | test | Checked-out executable evidence surfaces. | `tests` |
| `entity.workspace.generated` | directory | Disposable documentation/diagram/release projections with provenance. | `generated` |
| `entity.workspace.protocol12` | schema | Structured phase-path/context record for one direct feature file and its stable-ID project-control attempt. | `concept:Feature Workspace Protocol 12` |
| `entity.workspace.delivery8` | schema | Digest-bound proposal/result for removing exactly one complete attempt. | `concept:Delivery Proposal 8` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.workspace.config` | `configures` | `entity.workspace.module-architecture` | Identifies the root architecture and profile version. |
| `entity.workspace.module-architecture` | `contains_module` | `entity.workspace.module-directory` | Registers only immediate recursive module packages. |
| `entity.workspace.module-architecture` | `registers_feature` | `entity.workspace.feature-design` | Owns each direct level-local feature once. |
| `entity.workspace.control-state` | `contains` | `entity.workspace.attempt` | Centralizes temporary feature work without making it module specification content. |
| `entity.workspace.control-state` | `contains` | `entity.workspace.reflections` | Co-locates the tracked process log with reflection-triage configuration and scratch state. |
| `entity.workspace.attempt` | `depends_on` | `entity.workspace.feature-design` | The validated stable feature ID relates separate temporal control state to the durable file locator. |
| `entity.workspace.selection` | `routes_to` | `entity.workspace.feature-design` | Chooses one lifecycle root without changing behavior. |
| `entity.workspace.protocol12` | `documents` | `entity.workspace.feature-design` | Exposes the canonical direct `feature_path` and providing architecture context. |
| `entity.workspace.protocol12` | `documents` | `entity.workspace.attempt` | Exposes stable-ID-derived current phase paths/state without inventing identity from filenames. |
| `entity.workspace.source-code` | `realizes` | `entity.workspace.feature-design` | Actual implementation is code, not a durable prose artifact. |
| `entity.workspace.source-code` | `tested_by` | `entity.workspace.tests` | Test paths provide executable evidence; validator reports scope separately. |
| `entity.workspace.module-diagrams` | `generates` | `entity.workspace.generated` | Maintained diagram sources produce disposable deliveries with provenance. |
| `entity.workspace.delivery8` | `validates` | `entity.workspace.attempt` | Requires completeness/freshness before removal. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.workspace.resolve` | A phase starts with an explicit or selected feature file. | Validate canonical direct-file placement and stable ID; find providing module architecture/ancestry; summarize related feature paths; derive control attempt/code/test/reflection paths. | Protocol 12 returns exactly one bounded workspace. | `contract.workspace-files.feature-workspace` |
| `interaction.workspace.attempt` | Planning begins for a feature with no matching control attempt. | Create `.concorde/attempts/<stable-feature-id>/` and templates; later phases update only declared artifacts and product sources; evidence precedes task completion. | One active attempt holds all unfinished delivery memory outside the durable specification namespace. | `contract.workspace-files.records` |
| `interaction.workspace.specify-new` | Specification selects a planned direct path whose file does not yet exist. | Return unavailable identity/attempt fields; write valid feature front matter; rerun Protocol 12; create only the newly resolved checklist/attempt paths. | No attempt identity is guessed from filename or module placement. | `contract.workspace-files.feature-workspace` |
| `interaction.workspace.cleanup` | Delivery applies an eligible current proposal. | Verify safe real attempt path, digest, tasks/checklists, findings, and rollback staging; remove exactly the attempt. | Feature returns to no-active-attempt state without another durable document. | `contract.workspace-files.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.workspace-files.manage-feature-workspace` | Every phase receives authoritative design, architecture, relation, attempt, reflection, code, and test paths for one canonical feature. |

## Decisions

- Filename plus package position determines role; each durable feature is one direct Markdown file.
- Source/test reality and temporal evidence remain separate so structural validation cannot claim behavior.
- Delivery deletes temporal reasoning; reflections retain only deliberate difficult choices/problems, not task logs.
- Exact stable feature IDs map deterministically to control attempts; file/module moves preserve work,
  stable-ID changes with active state become orphan findings, and first-pass planned features expose no guessed attempt.

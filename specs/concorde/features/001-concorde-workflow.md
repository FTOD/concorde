---
id: feature.concorde.workflow
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow.initialize-architecture
  - feature.concorde.workflow.retrieve-bounded-context
  - feature.concorde.workflow.answer-workflow-questions
  - feature.concorde.workflow.manage-feature-workspaces
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.workflow.execute-and-reconcile
  - feature.concorde.workflow.validate-architecture
  - feature.concorde.workflow.accept-milestone
  - feature.concorde.workflow.fast-loop
interfaces:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
evidence_status: partial
---

# Feature Design: Concorde Workflow

## Outcome and Scope

A maintainer can direct one feature from its complete direct file through bounded planning, dependency-
ordered implementation/evidence, deterministic validation, and cleanup-only delivery using installed
skills as the sole conversational surface.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.skills` | Presents the normal and Concorde-specific workflow operations. |
| `module.concorde.scripts` | Resolves workspaces and performs deterministic init/context/validate/deliver operations. |
| `module.concorde.workspace-files` | Defines durable specification paths plus stable-ID attempts and reflections in project control state. |
| `entity.concorde.coding-agent` | Authors design/plan/tasks/code/tests and follows evidence/authority rules. |

## Interfaces

### `contract.concorde.workflow` — Skill-guided feature lifecycle

- **Consumer**: Maintainer and supported coding-agent integration.
- **Direction**: Maintainer intent to phase result, with structured deterministic operation crossings.
- **Entry points**: Installed specify/clarify/checklist/plan/tasks/implement/analyze/converge/fast-loop and Concorde init/context/validate/deliver/ask skills.
- **Inputs**: Selected `feature_path`, providing module architecture, related feature paths, code/tests, constitution, `.concorde/reflections/log.md`, and optional corresponding stable-ID control attempt.
- **Outputs**: Revised durable intent/architecture when authorized, temporal planning/evidence, reconciled code/tests/projections, findings, and delivery cleanup result.
- **Obligations**: Keep each fact in one authority, resolve Protocol 12 paths first, trace every task, validate deterministically, and disclose evidence limits.
- **Failures**: Invalid placement/authority, incomplete checklist/task, failed check, stale/unsafe delivery, or ambiguous impact stops the affected phase without implied authorization.
- **Compatibility**: Profile 7 features are direct Markdown files; Protocol 12 rejects specification-local control state/redundant feature fields, while Delivery 8 retains cleanup-only semantics.
- **Implementing entities**: `module.concorde.skills`, `module.concorde.scripts`, `module.concorde.workspace-files`, `entity.concorde.coding-agent`.
- **Example**: A maintainer specifies `features/001-change.md` with ID `feature.example.change`, runs plan/tasks/implement in `.concorde/attempts/feature.example.change/`, verifies all evidence, then invokes delivery once to remove that attempt.

### `contract.concorde.spec-kit-platform` — Required Spec Kit host lifecycle

- **Provider**: `external:specify-cli==0.16.4`.
- **Consumer**: Concorde preset/extension packages and their installed phase surfaces.
- **Direction**: Host project/component/phase state to composition, selection, and lifecycle services.
- **Entry points**: Spec Kit project initialization, catalogs/bundles/components, preset composition, extension registration, and `.specify/feature.json` selection.
- **Inputs**: Valid manifests, compatibility ranges, project root, integration, phase/selection, and lifecycle intent.
- **Outputs**: Composed templates/commands, installed ownership/registries, selected feature control, and structured component results.
- **Obligations**: Preserve typed component identity/provenance, deterministic composition order, project containment, and explicit mutation preview/apply.
- **Failures**: Incompatible/missing/colliding components or invalid project/selection state must fail without partial hidden ownership.
- **Compatibility**: Concorde currently targets `specify-cli>=0.16.4,<0.16.5`.
- **Implementing entities**: `entity.concorde.spec-kit`.
- **Example**: Spec Kit composes the base spec template with Concorde's design-only addendum and installs the extension's workspace adapter.

## Usage Scenarios

1. Establish or revise one direct module feature file and its interface/architecture references.
2. Create its corresponding stable-ID control attempt whose plan/tasks trace every affected architecture, feature, code, test, and projection.
3. Execute with evidence, validate the reconciled project, then deliver by removing only the attempt.
4. Use the fast loop only when deterministic preflight proves the change is already specified, bounded, and non-structural.

## Requirements

- **FR-001**: Every phase MUST resolve one Protocol 12 feature workspace and respect its declared read/write boundary.
- **FR-002**: Specification/architecture/code/test/projection facts MUST remain in their single authority and be reconciled together when affected.
- **FR-003**: Every executable task MUST have a requirement trace, exact path, dependency state, passed check, artifact, and stated evidence limitation before completion.
- **FR-004**: Validation/read-only failures MUST be non-mutating; reviewed initialization, eligible fast loop, and cleanup delivery MUST be atomic within their explicit authority.
- **FR-005**: Delivery MUST remove one complete current `.concorde/attempts/<stable-feature-id>/`, retain the direct feature and reflection log byte-identically, and MUST NOT author durable implementation prose or architectural intent.

## Edge Cases

- Related features span several immediate modules but the feature remains specified at the level where those modules are visible.
- A passing structural check has no behavioral evidence and therefore cannot authorize a completion claim.
- A stale proposal or unexpected protected-source change stops mutation while preserving the attempt.
